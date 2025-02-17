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

    # Check if additional columns exist, add them if not
    additional_columns = ["single_value", "last_request_timestamp", "last_trade_timestamp"]
    for col in additional_columns:
        if col not in header:
            header.append(col)
            for row in rows:
                row.append("N/A")

    # Write back the updated CSV structure (only if new columns were added)
    with open(filename, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(header)
        csvwriter.writerows(rows)
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

def update_display():
    clear_screen()
    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = 0
    entry_total = 0
    change_total = 0
    last_trade_timestamp = "N/A"

    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        data = list(csvreader)
        header = data[0]
        rows = data[1:]
    
    for row in rows:
        try:
            total += float(row[-3]) * float(row[1])
            entry_total += float(row[1]) * float(row[2])
            change_total += (float(row[-3]) - float(row[2])) * float(row[1])
            last_trade_timestamp = row[-1]
        except ValueError:
            continue
    
    print("\nPress ENTER to stop the script...\n")
    print(f"Latest request timestamp:   {formatted_now}")
    print(f"Latest trade timestamp:     {last_trade_timestamp}")
    print(f"Change to previous day:     {color(change_total)}")
    print(f"Total depot change:         {color(entry_total)}")
    print(f"Total depot value:          {round(total, 2)}")

while not stop_script:
    last_trade_timestamps = []
    error_occurred = False

    for row in rows:
        if stop_script:
            break
        try:
            ticker_symbol = row[0]
            shares_owned = float(row[1])
            purchase_price = float(row[2])

            stock = yf.Ticker(ticker_symbol)
            stock_info = stock.history(period="1d")

            if stock_info.empty:
                raise ValueError(f"No data found for {ticker_symbol}")

            current_price = stock_info["Close"].iloc[-1]
            price_change = stock_info["Close"].iloc[-1] - stock_info["Open"].iloc[-1]

            last_known_values[ticker_symbol] = {
                "current_price": current_price,
                "price_change": price_change,
            }

            last_trade_timestamps.append(datetime.now(berlin_tz))
        except Exception as e:
            print(f"Error fetching data for {row[0]}: {e}")
            error_occurred = True
        
        formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update CSV with new values
        if ticker_symbol in last_known_values:
            row[-3] = round(last_known_values[ticker_symbol]["current_price"], 2)
            row[-2] = formatted_now
            row[-1] = last_trade_timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")

        with open(filename, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(header)
            csvwriter.writerows(rows)
        
        # Update display after each row
        update_display()
        
        if stop_script:
            break  # Check after each loop iteration

    #time.sleep(1)

print("\nScript stopped successfully.")
