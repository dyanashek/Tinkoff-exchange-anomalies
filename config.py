import os
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TINKOFF_TOKEN = os.getenv('TINKOFF_TOKEN')

# sigma coeff (can be changed depends on the situation when you want to get notifications)
sigma_coeff = float(os.getenv('SIGMA_COEFF'))
# sigma price coeff (can be changed depends on the situation when you want to get notifications)
delta_sigma_coeff = float(os.getenv('DELTA_SIGMA_COEFF'))

# channel id to send messages
CHANNEL_ID = os.getenv('CHANNEL_ID')

# users who allowed to complete commands
MANAGERS_ID = os.getenv('MANAGERS_ID')

# flag that decides where to fill logs
if int(os.getenv('LOGGING_FILE')) == 0:
    LOGGING_FILE = False
else:
    LOGGING_FILE = True

MY_QUEUE = Queue()

WORK_FLAG = True

SENDED_TICKERS = []