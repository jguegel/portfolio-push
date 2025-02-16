import csv
import os
import time
import pytz
import yfinance as yf
import threading
from datetime import datetime, timedelta
from colorama import init
from termcolor import colored

# Initialize colorama for cross-platform support
init(autoreset=True)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def color(value):
    value = float(value)
    if value < 0:
        return colored(f"{round(value, 2)} ↓", "red")
    elif value > 0:
        return colored(f"{round(value, 2)} ↑", "green")
    else:
        return f"{value} ±"

filename = "depot.csv"
header, rows = [], []

try:
    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)
        rows = [row for row in csvreader]
except FileNotFoundError:
    print(f"Error: {filename} not found!")
    exit(1)

print(f"{len(rows)} rows imported from {filename}")

berlin_tz = pytz.timezone("Europe/Berlin")

last_known_values = {}
stop_script = False

def wait_for_exit():
    global stop_script
    input("\nPress ENTER to stop the script...\n")
    stop_script = True

threading.Thread(target=wait_for_exit, daemon=True).start()

def update_display(formatted_now, last_trade_formatted, change_total, entry_total, total):
    clear_screen()
    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\nPress ENTER to stop the script...\n")
    print(f"Latest request timestamp:   {formatted_now}")
    print(f"Latest trade timestamp:     {last_trade_formatted}")
    print(f"Change to previous day:     {color(change_total)}")
    print(f"Total depot change:         {color(entry_total)}")
    print(f"Total depot value:          {round(total, 2)}")

total = 0  # Keep track of total value persistently
while not stop_script:
    last_trade_timestamps = []
    error_occurred = False

    i = 0
    while i < len(rows):
        if stop_script:
            break
        
        try:
            ticker_symbol = rows[i][0]
            shares_owned = float(rows[i][1])
            purchase_price = float(rows[i][2])

            stock = yf.Ticker(ticker_symbol)
            stock_info = stock.history(period="1d")

            if stock_info.empty:
                raise ValueError(f"No data found for {ticker_symbol}")

            current_price = stock_info["Close"].iloc[-1]
            price_change = stock_info["Close"].iloc[-1] - stock_info["Open"].iloc[-1]

            if ticker_symbol not in last_known_values:
                last_known_values[ticker_symbol] = {
                    "current_price": current_price,
                    "price_change": price_change,
                }

            last_known_values[ticker_symbol]["current_price"] = current_price
            last_known_values[ticker_symbol]["price_change"] = price_change

            last_trade_timestamps.append(datetime.now(berlin_tz))


        except Exception as e:
            print(f"Error fetching data for {rows[i][0]}: {e}")
            error_occurred = True
        i += 1  # Ensure i increments even if an error occurs

        if stop_script:
            break  # Check after each loop iteration

    total = sum(
        last_known_values[ticker]["current_price"] * float(rows[i][1])
        for i, ticker in enumerate(last_known_values)
    )
    entry_total = sum(float(rows[i][1]) * float(rows[i][2]) for i in range(len(rows)))
    change_total = sum(
        last_known_values[ticker]["price_change"] * float(rows[i][1])
        for i, ticker in enumerate(last_known_values)
    )

    latest_trade_timestamp = max(last_trade_timestamps, default="N/A")
    if isinstance(latest_trade_timestamp, datetime):
        latest_trade_timestamp = latest_trade_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    oldest_trade_timestamp = min(last_trade_timestamps, default="N/A")

    if isinstance(latest_trade_timestamp, datetime) and isinstance(oldest_trade_timestamp, datetime):
        if oldest_trade_timestamp < latest_trade_timestamp - timedelta(days=1):
            latest_trade_timestamp = "Check CSV, timestamp gap too big"

    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_display(formatted_now, latest_trade_timestamp, change_total, entry_total, total)

    time.sleep(5)

print("\nScript stopped successfully.")
