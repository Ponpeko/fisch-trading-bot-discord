# Fisch Trading Bot Discord

A Discord bot for the Fisch game that helps players check item values, calculate trades, and find high-demand items using data from a Google Sheet.

## Features

- **Item Value Lookup** (`f!value <item>`) - Search for item values, demand, and status with fuzzy matching
- **Trade Calculator** (`f!trade [item1] + [item2] for [target]`) - Calculate if a trade is fair, lowball, or overpay
- **High Demand List** (`f!highdemand [threshold] [limit]`) - View items with demand above a specified threshold
- **Help Command** (`f!info`) - Display available commands

## Requirements

- Python 3.8+
- Discord.py
- python-dotenv
- pandas
- requests
- rapidfuzz

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/fisch-trading-bot-discord.git
cd fisch-trading-bot-discord
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your credentials:
```
DISCORD_TOKEN=your_discord_bot_token_here
SHEET_URL=your_google_sheets_csv_url_here
```

## Configuration

### Discord Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to Bot section and click "Add Bot"
4. Copy the token and add it to `.env`

### Google Sheet URL
1. Create a Google Sheet with columns: `Name`, `Value`, `Demand`, `Status`
2. Publish it to the web as CSV
3. The URL format should be: `https://docs.google.com/spreadsheets/d/{ID}/gviz/tq?tqx=out:csv`
4. Add the URL to `.env`

## Usage

Run the bot:
```bash
python bot.py
```

### Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `f!value` | `f!value <item>` | Look up an item's value, demand, and status |
| `f!trade` | `f!trade [item1] + [item2] for [target]` | Calculate if a trade is fair |
| `f!highdemand` | `f!highdemand [threshold] [limit]` | List items with high demand |
| `f!info` | `f!info` | Show all available commands |

### Examples

```
f!value salmon
f!trade common fish + rope for rare fish
f!highdemand 8 10
```

## Trade Calculation Logic

- **LOWBALL**: Offer < 85% of target value (❌ red)
- **FAIR**: Offer 85-115% of target value (✅ green)
- **OVERPAY**: Offer > 115% of target value (⚠️ orange)

## Data Caching

The bot loads data from the Google Sheet once at startup and caches it in memory. This reduces API calls and improves response time.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.
