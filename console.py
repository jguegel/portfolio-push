import csv
import os
import time
import pytz
import yfinance as yf
import threading
from datetime import datetime, timedelta
from colorama import init
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

# Store last known values in case of an error
last_known_values = {
    "latest_trade_timestamp": "N/A",
    "change_total": 0,
    "entry_total": 0,
    "total": 0
}

# Variable to track if the script should stop
stop_script = False

# Function to wait for user input in a separate thread
def wait_for_exit():
    global stop_script
    input("\nPress ENTER to stop the script...\n")
    stop_script = True

# Start input listener thread
exit_thread = threading.Thread(target=wait_for_exit, daemon=True)
exit_thread.start()

while not stop_script:
    # Immediately display the last known values before fetching new data
    clear_screen()
    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format trade timestamp to match request timestamp
    latest_trade_formatted = (
        last_known_values["latest_trade_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(last_known_values["latest_trade_timestamp"], datetime)
        else last_known_values["latest_trade_timestamp"]
    )

    print("\nPress ENTER to stop the script...\n")
    print(f"Latest request timestamp:   {formatted_now}")
    print(f"Latest trade timestamp:     {latest_trade_formatted}")
    print(f"Change to previous day:     {color(last_known_values['change_total'])}")
    print(f"Total depot change:         {color(last_known_values['entry_total'])}")
    print(f"Total depot value:          {round(last_known_values['total'], 2)}")

    # Initialize new calculations
    last_trade_timestamps = []
    total, entry_total, change_total = 0, 0, 0
    error_occurred = False

    for item in tqdm(rows, desc="Fetching Stock Data"):
        if stop_script:
            break  # Exit immediately if the user presses ENTER

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
            break  # Continue showing old values

    if not error_occurred:
        entry_total = total - entry_total
        latest_trade_timestamp = max(last_trade_timestamps) if last_trade_timestamps else "N/A"
        oldest_trade_timestamp = min(last_trade_timestamps) if last_trade_timestamps else "N/A"

        # Check if timestamps have a big gap
        if isinstance(latest_trade_timestamp, datetime) and isinstance(oldest_trade_timestamp, datetime):
            one_day = timedelta(days=1)
            if oldest_trade_timestamp < latest_trade_timestamp - one_day:
                latest_trade_timestamp = "Check CSV, timestamp gap too big"

        # Store latest known values in case of future errors
        last_known_values.update({
            "latest_trade_timestamp": latest_trade_timestamp,
            "change_total": change_total,
            "entry_total": entry_total,
            "total": total
        })

    time.sleep(5)  # Refresh rate

print("\nScript stopped successfully.")
