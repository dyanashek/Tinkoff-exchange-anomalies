import sqlite3
import logging

database = sqlite3.connect("tinkoff.db")
cursor = database.cursor()

try:
    # creates table with tickers identity, which candles we can get by API
    cursor.execute('''CREATE TABLE available(
        id INTEGER PRIMARY KEY,
        name VARCHAR (30),
        ticker VARCHAR (6),
        figi VARCHAR (40),
        lot INTEGER,
        currency VARCHAR(8),
        sigma REAL,
        average REAL,
        delta REAL
    )''')
except:
    logging.error('Available table already exists.')
    

try:
    # creates table with tickers identity, which candles we can not get by API
    cursor.execute('''CREATE TABLE not_available(
        id INTEGER PRIMARY KEY,
        name VARCHAR (30),
        ticker VARCHAR (6),
        figi VARCHAR (40),
        lot INTEGER,
        currency VARCHAR(8)
    )''')
except:
    logging.error('Not_available table already exists.')

cursor.execute(f"DELETE FROM not_available WHERE id<>10000")
database.commit()