import csv
import os
import time
import pytz
import yfinance as yf
from datetime import datetime, timedelta
from colorama import init, Style
from termcolor import colored
from tqdm import tqdm

# Initialize colorama for cross-platform support
init(autoreset=True)

# Function to clear the terminal screen (cross-platform)
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# Coloring value changes
def color(value):
    value = float(value)
    if value < 0:
        return colored(f"{round(value, 2)} ↓", "red")
    elif value > 0:
        return colored(f"{round(value, 2)} ↑", "green")
    else:
        return f"{value} ±"

# Read CSV file
filename = "depot.csv"
header, rows = [], []

try:
    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)  # Extract column headers
        rows = [row for row in csvreader]  # Read all data rows
except FileNotFoundError:
    print(f"Error: {filename} not found!")
    exit(1)

print(f"{len(rows)} rows imported from {filename}")

# Berlin timezone for accurate timestamps
berlin_tz = pytz.timezone("Europe/Berlin")

while True:
    clear_screen()
    last_trade_timestamps = []
    total, entry_total, change_total = 0, 0, 0
    error_occurred = False

    for item in tqdm(rows, desc="Fetching Stock Data"):
        try:
            ticker_symbol = item[0]
            shares_owned = float(item[1])
            purchase_price = float(item[2])

            stock = yf.Ticker(ticker_symbol)
            stock_info = stock.history(period="1d")

            if stock_info.empty:
                raise ValueError(f"No data found for {ticker_symbol}")

            current_price = stock_info["Close"].iloc[-1]  # Get last closing price
            price_change = stock_info["Close"].iloc[-1] - stock_info["Open"].iloc[-1]

            total += current_price * shares_owned
            entry_total += shares_owned * purchase_price
            change_total += price_change * shares_owned

            # Get last trade timestamp
            last_trade_timestamps.append(datetime.now(berlin_tz))

        except Exception as e:
            print(f"Error fetching data for {item[0]}: {e}")
            error_occurred = True
            break  # Exit loop on error

    if not error_occurred:
        entry_total = total - entry_total
        latest_trade_timestamp = max(last_trade_timestamps) if last_trade_timestamps else "N/A"
        oldest_trade_timestamp = min(last_trade_timestamps) if last_trade_timestamps else "N/A"
        
        # Check if timestamps have a big gap
        if isinstance(latest_trade_timestamp, datetime) and isinstance(oldest_trade_timestamp, datetime):
            one_day = timedelta(days=1)
            if oldest_trade_timestamp < latest_trade_timestamp - one_day:
                latest_trade_timestamp = "Check CSV, timestamp gap too big"

        formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"Latest request timestamp:   {formatted_now}")
        print(f"Latest trade timestamp:     {latest_trade_timestamp}")
        print(f"Change to previous day:     {color(change_total)}")
        print(f"Total depot change:         {color(entry_total)}")
        print(f"Total depot value:          {round(total, 2)}")

    else:
        print("An error occurred while fetching data. Retrying in 60 seconds.")

    time.sleep(10)  # Wait before refreshing
