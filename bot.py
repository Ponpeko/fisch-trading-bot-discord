import os
import discord
import pandas as pd
import requests
from rapidfuzz import fuzz
from datetime import datetime, timedelta

from io import StringIO
from discord.ext import commands
from dotenv import load_dotenv

# Load token dari .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Cache variables
cached_data = None

def get_sheet_data():
    """Load sheet data once (no periodic updates). Returns None on failure."""
    global cached_data
    if cached_data is not None:
        return cached_data

    sheet_url = os.getenv("SHEET_URL")
    try:
        print("🔄 Mengambil data dari Google Sheet (startup)...")
        response = requests.get(sheet_url)
        response.raise_for_status()
        cached_data = pd.read_csv(StringIO(response.text))
        print("✅ Data berhasil dimuat dari sheet (sekali).")
        return cached_data
    except Exception as e:
        print(f"❌ Gagal ambil data dari sheet: {e}")
        return None

def get_item_value(item_name: str, data: pd.DataFrame):
    """Cari value item dengan fuzzy matching"""
    best_match = None
    best_score = 0
    
    for idx, row in data.iterrows():
        sheet_item = str(row["Name"]).lower()
        similarity = fuzz.ratio(item_name.lower(), sheet_item)
        
        if similarity > best_score:
            best_score = similarity
            best_match = row
    
    if best_score < 70:
        return None, best_score
    
    return best_match, best_score

# Inisialisasi bot
intents = discord.Intents.default()
intents.message_content = True  # penting!
bot = commands.Bot(command_prefix="f!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} sudah online!")
    # Load data sekali saat bot startup
    get_sheet_data()

@bot.command()
async def value(ctx, *, item_name: str):
    """Cari value item dari spreadsheet"""
    data = get_sheet_data()

    if data is None:
        await ctx.send("❌ Gagal mengambil data dari spreadsheet.")
        return

    match, score = get_item_value(item_name, data)
    
    if match is None:
        await ctx.send(f"🔍 Item **{item_name}** tidak ditemukan. (similarity: {score}%)")
        return

    value = match["Value"]
    demand = match["Demand"]
    status = match["Status"]
    correct_name = match["Name"]
    
    embed = discord.Embed(
        title=f"{correct_name}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Value", value=f"**{value}**", inline=False)
    embed.add_field(name="Demand", value=f"**{demand}**", inline=False)
    embed.add_field(name="Status", value=f"**{status}**", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def trade(ctx, *, trade_info: str):
    """Kalkulasi trade: !trade [item1] + [item2] for [item_target]"""
    data = get_sheet_data()
    
    if data is None:
        await ctx.send("❌ Gagal mengambil data dari spreadsheet.")
        return
    
    try:
        parts = trade_info.split(" for ")
        if len(parts) != 2:
            await ctx.send("❌ Format salah! Gunakan: `!trade [item1] + [item2] for [item_target]`")
            return
        
        items_offered = parts[0].strip().split("+")
        item_target = parts[1].strip()
        
        # Hitung total value item yang ditawarkan
        total_offered = 0
        offered_items = []
        
        for item in items_offered:
            item = item.strip()
            match, score = get_item_value(item, data)
            
            if match is None:
                await ctx.send(f"❌ Item **{item}** tidak ditemukan!")
                return
            
            value = int(match["Value"])
            total_offered += value
            offered_items.append((match["Name"], value))
        
        # Cari value item target
        target_match, score = get_item_value(item_target, data)
        
        if target_match is None:
            await ctx.send(f"❌ Item **{item_target}** tidak ditemukan!")
            return
        
        target_value = int(target_match["Value"])
        target_name = target_match["Name"]
        
        # Hitung persentase
        percentage = (total_offered / target_value) * 100
        
        # Tentukan status (sesuaikan threshold sesuai kebutuhan)
        if percentage < 85:
            status = "❌ **LOWBALL**"
            color = discord.Color.red()
        elif percentage <= 115:
            status = "✅ **FAIR**"
            color = discord.Color.green()
        else:
            status = "⚠️ **OVERPAY**"
            color = discord.Color.orange()
        
        # Buat embed
        embed = discord.Embed(
            title="Trade Calculator",
            color=color
        )
        
        # Item yang ditawarkan
        offered_text = "\n".join([f"• {name}: **{value}**" for name, value in offered_items])
        embed.add_field(name="📤 Offer", value=offered_text, inline=False)
        
        # Item target
        embed.add_field(name="📥 For", value=f"• {target_name}: **{target_value}**", inline=False)
        
        # Summary
        embed.add_field(name="📊 Result", value=f"**{total_offered}** / **{target_value}** = **{percentage:.1f}%**", inline=False)
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name= "Note", value="Note: Calculations only based on value", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

def parse_demand(s):
    """Parse demand format '7/10' -> returns float or None."""
    if s is None:
        return None
    raw = str(s).strip().lower()
    if raw in ["", "-", "—", "na", "n/a"]:
        return None
    try:
        # format "7/10"
        if "/" in raw:
            parts = raw.split("/")
            if len(parts) == 2:
                num = float(parts[0])
                denom = float(parts[1])
                if denom == 0:
                    return None
                return num  # 7/10 -> 7.0
        # fallback plain number
        return float(raw)
    except:
        return None

@bot.command()
async def highdemand(ctx, threshold: float = 7.0, limit: int = 20):
    """Tampilkan item dengan demand >= threshold (default 7). Usage: !highdemand [threshold] [limit]"""
    data = get_sheet_data()
    if data is None:
        await ctx.send("❌ Gagal mengambil data dari spreadsheet.")
        return

    rows = []
    for idx, row in data.iterrows():
        name = row.get("Name")
        demand_raw = row.get("Demand")
        demand_num = parse_demand(demand_raw)
        if demand_num is None:
            continue
        if demand_num >= threshold:
            value_raw = row.get("Value")
            rows.append((demand_num, name, value_raw, demand_raw))

    if not rows:
        await ctx.send(f"ℹ️ Tidak ada item dengan demand ≥ {threshold}.")
        return

    # sort by demand desc
    rows.sort(key=lambda x: x[0], reverse=True)
    rows = rows[:limit]

    lines = []
    for d, name, v_raw, d_raw in rows:
        demand_display = d_raw if d_raw not in [None, "nan"] else f"{d:.1f}"
        value_display = str(v_raw) if v_raw is not None else "N/A"
        lines.append(f"• {name} — Demand: **{demand_display}** — Value: **{value_display}**")

    # send embed (or plain if too long)
    text = "\n".join(lines)
    if len(text) > 1900:
        # fallback to chunked plain message
        await ctx.send("🔥 High Demand (results too long, showing first items):")
        for line in lines[:limit]:
            await ctx.send(line)
    else:
        embed = discord.Embed(title=f"🔥 High Demand (≥ {threshold})", color=discord.Color.orange())
        embed.description = text
        embed.set_footer(text=f"Showing up to {len(rows)} items")
        await ctx.send(embed=embed)

@bot.command(name="info")
async def info_cmd(ctx):
    """Tampilkan bantuan singkat untuk command bot"""
    embed = discord.Embed(title="Info — Commands", color=discord.Color.blurple())
    embed.add_field(name="f!value <item>", value="Cari value, demand, status dari <item>.", inline=False)
    embed.add_field(name="f!trade [item1] + [item2] + ... for [target]", value="Hitung trade; hasil: LOWBALL / FAIR / OVERPAY.", inline=False)
    embed.add_field(name="f!highdemand [demand] [limit]", value="List item dengan demand ≥ <demand>.", inline=False)
    embed.add_field(name="f!info", value="Tampilkan pesan ini.", inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
