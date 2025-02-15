import asyncio, csv, os, pytz
from datetime import datetime, timedelta
from tqdm import tqdm
from wallstreet import Stock 
from datetime import datetime
from termcolor import colored

clear = lambda:os.system('cls')

rows, output, lastTradeTimestamp = [], [], []
berlin_tz = pytz.timezone('Europe/Berlin')
filename = "depot.csv"

async def process_row(item):
   stock = Stock(item[0])
   total = (stock.price * float(item[1]))
   entryTotal = (float(item[1]) * float(item[2]))
   changeTotal = (stock.change * float(item[1]))
   date_format = "%d %b %Y %H:%M:%S"
   dt_utc = datetime.strptime(stock.last_trade, date_format)
   dt_de = dt_utc.replace(tzinfo=pytz.utc).astimezone(berlin_tz)
   lastTradeTimestamp = dt_de.replace(tzinfo=None)
   return total, entryTotal, changeTotal, lastTradeTimestamp

async def main(rows):
   tasks, lastTradeTimestamp = [], []
   output = [0, 0, 0, datetime]
   for item in rows:
      tasks.append(asyncio.create_task(process_row(item)))
   results = await asyncio.gather(*tasks)
   for item in results:
      output[0] += item[0]
      output[1] += item[1]
      output[2] += item[2]
      lastTradeTimestamp.append(item[3])
      latestTradeTimestamp = max(lastTradeTimestamp)
      oldestTradeTimestamp = min(lastTradeTimestamp)
      one_day = timedelta(days=1)
      clear()
      if oldestTradeTimestamp < latestTradeTimestamp - one_day:
         latestTradeTimestamp = "check csv, timestamp gap too big"
      output[3] = latestTradeTimestamp
      totalChange = output[0] - output[1]
      formatted_datenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      print("Latest request timestamp:   ", formatted_datenow)
      print("Latest trade timestamp:     ", output[3])
      print("Change to previous day:     ", color(output[2]))
      print("Total depot change:         ", color(totalChange))
      print("Total depot value:          ", "{:.2f}".format(round(output[0], 2)))
   lastTradeTimestamp.clear()
   return output

# coloring incoming value
def color(value):
   value = float(value)
   if value < 0:
      valueColored = colored("{:.2f}".format(round(value, 2)), 'red')
      valueColored = valueColored + u' \u2193'
   if value > 0:
      valueColored = colored("{:.2f}".format(round(value, 2)), 'green')
      valueColored = valueColored + u' \u2191'
   if value == 0:
      valueColored = value
      valueColored = valueColored + u' \u00B1'
   return valueColored

# reading csv file
with open(filename, 'r') as csvfile:
   # creating a csv reader object
   csvreader = csv.reader(csvfile)
   # extracting field names through first row
   header = next(csvreader)
   # extracting each data row one by one
   for row in csvreader:
      rows.append(row)

while True:
   output = asyncio.run(main(rows))