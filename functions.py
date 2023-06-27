import sqlite3
import time
import datetime
import logging
import itertools
import threading
import numpy
import inspect
import telebot

from tinkoff.invest import Client, CandleInterval, CandleInstrument, SubscriptionInterval,\
                            MarketDataRequest, SubscribeCandlesRequest, SubscriptionAction,\
                            InstrumentClosePriceRequest, Candle, Quotation
from tinkoff.invest.constants import INVEST_GRPC_API

from classes import Share
import config
import utils

if config.LOGGING_FILE:
    logging.basicConfig(level=logging.ERROR, 
                        filename="py_log.log", 
                        filemode="w", 
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        )
else:
    logging.getLogger().setLevel(logging.ERROR)

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

lock = threading.Lock()

def get_all_available_share():
    """Gets all shares that available on tinkoff"""

    try:
        with Client(config.TINKOFF_TOKEN, target=INVEST_GRPC_API) as client:
            shares = client.instruments.shares(instrument_status=2).instruments

        logging.info(f'{inspect.currentframe().f_code.co_name}: Получена информация по акциям, доступным в Tinkoff.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось получить акции, доступные в Tinkoff. {ex}')
        shares = False

    return shares


def sort_shares(shares):
    """Gets shares that are available in main trade session on MOEX."""

    for share in shares:
        if (share.otc_flag is False) and ('moex' in share.exchange.lower()) and ('TCS' not in share.figi):
            share = Share(name=share.name, 
                    ticker=share.ticker, 
                    figi=share.figi,
                    lot=share.lot,
                    currency=share.currency.upper()
                    )
            share = historical_candles_availability(share)
            renew_database(share)
            time.sleep(3)
    
    logging.info(f'{inspect.currentframe().f_code.co_name}: Собраны данные по акциям tinkoff.')


def historical_candles_availability(share: Share):
    """Tries to get historical candles for share, 
    changes the Share class object if there is the possibility and
    calculates sigma, delta, etc.
    """

    candles_volume = []
    deltas_volume = []

    try:
        with Client(config.TINKOFF_TOKEN, target=INVEST_GRPC_API) as client:
            candles = client.get_all_candles(
                    from_=datetime.datetime.utcnow() - datetime.timedelta(days=7), 
                    to=datetime.datetime.utcnow(),
                    figi=f'{share.figi}', 
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                )
            
            logging.info(f'{inspect.currentframe().f_code.co_name}: Получена информация по figi: {share.figi}.')

            for candle in candles:
                if candle:
                    # the candle is complete
                    if candle.is_complete:
                        # received on a business day
                        if candle.time.isoweekday() in range(1, 6):
                            candles_volume.append(candle.volume)

                            # converts open and close price to float
                            close = utils.price_converter(candle.close)
                            open = utils.price_converter(candle.open)

                            deltas_volume.append(abs(open-close))

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось получить информацию о свечах по тикеру {share.ticker}. {ex}')

    if (candles_volume != []) and (deltas_volume != []):
        sigma, average, price_delta = calculate_statistic_data(candles_volume, deltas_volume)
        if sigma:
            share.candles = True
            share.sigma = sigma
            share.average = average
            share.price_delta = price_delta

    return share 


def renew_database(share: Share):
    """Updates information in database."""

    in_available = is_in_available(share.figi)
    in_not_available = is_in_not_available(share.figi)

    if share.candles:
        ...
        if (not in_available) and (not in_not_available):
            add_available(share)
        elif in_available:
            update_available(share)
        elif in_not_available:
            delete_from_not_available(share.figi)
            add_available(share)

    else:
        if (not in_available) and (not in_not_available):
            add_not_available(share) 
        elif in_not_available:
            update_not_available(share)
        elif in_available:
            delete_from_available(share.figi)
            add_not_available(share)


def is_in_available(figi):
    """Checks if share in 'available' table. Returns True if it is."""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    available = cursor.execute(f"SELECT id from available WHERE figi='{figi}'").fetchall()

    if available == []:
        return False

    return True


def is_in_not_available(figi):
    """Checks if share in 'not available' table. Returns True if it is."""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    not_available = cursor.execute(f"SELECT id from not_available WHERE figi='{figi}'").fetchall()

    if not_available == []:
        return False

    return True


def add_available(share: Share):
    """Adds share to available"""
    
    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    try:
        cursor.execute(f'''
                INSERT INTO available (name, ticker, figi, lot, currency, sigma, average, delta)
                VALUES ("{share.name}", "{share.ticker}", "{share.figi}",
                {share.lot}, "{share.currency}", {share.sigma}, 
                {share.average}, {share.price_delta})
                ''')
        logging.info(f'{inspect.currentframe().f_code.co_name}: В таблицу available добавлен {share.ticker}.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось добавить в таблицу available {share.ticker}. {ex}')
    
    database.commit()
    cursor.close()
    database.close()


def update_available(share: Share):
    """Updates share in available."""
    
    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    try:
        cursor.execute(f'''
                UPDATE available
                SET name="{share.name}", ticker="{share.ticker}", figi="{share.figi}",
                lot={share.lot}, currency="{share.currency}", sigma={share.sigma}, 
                average={share.average}, delta={share.price_delta}
                WHERE figi="{share.figi}"
                ''')
        logging.info(f'{inspect.currentframe().f_code.co_name}: В таблице available обновлен {share.ticker}.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось обновить в таблице available {share.ticker}. {ex}')
    
    database.commit()
    cursor.close()
    database.close()


def delete_from_available(figi):
    """Deletes share from available"""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    cursor.execute(f"DELETE FROM available WHERE figi='{figi}'")

    logging.info(f'{inspect.currentframe().f_code.co_name}: Из таблицы available удален {figi}.')

    database.commit()
    cursor.close()
    database.close()


def add_not_available(share: Share):
    """Adds share to not_available"""
    
    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    try:
        cursor.execute(f'''
                INSERT INTO not_available (name, ticker, figi, lot, currency)
                VALUES ("{share.name}", "{share.ticker}", "{share.figi}",
                {share.lot}, "{share.currency}")
                ''')
        logging.info(f'{inspect.currentframe().f_code.co_name}: В таблицу not_available добавлен {share.ticker}.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось добавить в таблицу not_available {share.ticker}. {ex}')
    
    database.commit()
    cursor.close()
    database.close()


def update_not_available(share: Share):
    """Updates share in not_available."""
    
    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    try:
        cursor.execute(f'''
                UPDATE not_available
                SET name="{share.name}", ticker="{share.ticker}", figi="{share.figi}",
                lot={share.lot}, currency="{share.currency}"
                WHERE figi="{share.figi}"
                ''')
        logging.info(f'{inspect.currentframe().f_code.co_name}: В таблице not_available обновлен {share.ticker}.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось обновить в таблице not_available {share.ticker}. {ex}')
    
    database.commit()
    cursor.close()
    database.close()


def delete_from_not_available(figi):
    """Deletes share from not available"""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    cursor.execute(f"DELETE FROM not_available WHERE figi='{figi}'")

    logging.info(f'{inspect.currentframe().f_code.co_name}: Из таблицы not_available удален {figi}.')

    database.commit()
    cursor.close()
    database.close()


def calculate_statistic_data(candles_volume, deltas_volume):
    """Calculates price, volume sigmas (standard deviation) and average volume."""

    # calculates average values
    candles_avg = int(round(sum(candles_volume) / len(candles_volume), 0))
    deltas_avg = int(round(sum(deltas_volume) / len(deltas_volume), 0))

    # form pair to get deltas between previous and next value
    candles_deltas_previous = zip(candles_volume, candles_volume[1:])
    deltas_deltas_previous = zip(deltas_volume, deltas_volume[1:])

    candles_deltas = []
    deltas_deltas = []

    # calculates deltas
    for pair in candles_deltas_previous:
        candles_deltas.append(abs(pair[0] - pair[1]))

    for pair in deltas_deltas_previous:
        deltas_deltas.append(abs(pair[0] - pair[1]))

    try:
        # calculates sigma
        candles_sigma = numpy.std(candles_deltas)
        deltas_sigma = numpy.std(deltas_deltas)

        # calculates a value that indicates a maximum normal difference between candle's close and open
        price_delta = deltas_sigma * config.delta_sigma_coeff + deltas_avg
    except:
        candles_sigma = False
        candles_avg = False
        price_delta = False

    return candles_sigma, candles_avg, price_delta


def get_all_from_available():
    """Gets all shares figi from available table."""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    figis = cursor.execute("SELECT DISTINCT figi FROM available").fetchall()

    cursor.close()
    database.close()

    if figis != []:
        figis = itertools.chain.from_iterable(figis)

    return figis


def instruments_to_subscribe(figis):
    """Generates a list of CandleInstruments objects to make a stream with."""

    instruments = []

    for figi in figis:
        instruments.append(CandleInstrument(
                                    figi=figi,
                                    interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE,
                                    )
                        )
    
    return instruments


def request_iterator(instruments):
        """Iterates a request for data streaming."""
        
        yield MarketDataRequest(
            subscribe_candles_request=SubscribeCandlesRequest(
                waiting_close=True,
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=instruments,
            )
        )

        while True:

            # breaking the loop if WORKING_FLAG is False
            if not config.WORK_FLAG:
                return
            
            time.sleep(1)


def start_tracking(instruments):
    """Makes a subscription for instruments (starts tracking shares candles)."""
    
    if len(instruments) > 300:
        instruments = instruments[:300]

    # making a loop to reconnect if there are problems with API
    while True:
        try:
            # subscribe for streaming
            with Client(config.TINKOFF_TOKEN) as client:
                sub = client.market_data_stream.market_data_stream(
                    request_iterator(instruments)
                )
                logging.info(f'{inspect.currentframe().f_code.co_name}: Осуществлена подписка на свечи.')
                for candle in sub:
                    
                    # breaking the loop if WORKING_FLAG is False
                    if not config.WORK_FLAG:
                        return
                    
                    # if we received a candle object
                    if candle.candle is not None:
                        threading.Thread(daemon=True, target=handle_candle, args=(candle.candle,)).start()

        # if connection wasn't successful - logging and sleeps a while to try again
        # the error could be caused by the requests amount                
        except Exception as ex:
            logging.error(f'{inspect.currentframe().f_code.co_name}: Сбой в работе Tinkoff api. {ex}')
            time.sleep(2)


# specify the data type to correctly display attributes in IDE
def handle_candle(candle: Candle):
    """Handles candles from subscribe. 
    Analyzes data and decides if there is one or more of triggers: price or volume.
    """

    # getting data (from database) that we need to identify triggers
    figi_info = get_figi_data(candle.figi)

    # if we successfully got values
    if figi_info != [] and len(figi_info) == 9:

        sigma = figi_info[6]
        average = figi_info[7]
        delta = figi_info[8]

        # setting trigger flags
        price_flag = False
        volume_flag = False

        # converts prices to float
        close = utils.price_converter(candle.close)
        open = utils.price_converter(candle.open)

        # checking if volume trigger is positive - changing flag
        if candle.volume > sigma * config.sigma_coeff + average:
            volume_flag = True

        # checking if price trigger is positive - changing flag
        if abs(close - open) > delta:
            price_flag = True

        # if one or more flags are True - getting extra data that we need for notifications
        if price_flag or volume_flag:
            name = figi_info[1]
            ticker = figi_info[2]
            lot = figi_info[4]
            currency = figi_info[5]

            # getting previous trade day close price
            close_price = get_close_price(candle.figi)
            # constructing notification text, based 
            reply_text = construct_reply(name=name,
                                         ticker=ticker,
                                         lot=lot,
                                         currency=currency,
                                         close_price=close_price,
                                         close=close,
                                         open=open,
                                         volume=candle.volume,
                                         time=candle.time,
                                         price_flag=price_flag,
                                         volume_flag=volume_flag,
                                         )
            if reply_text not in config.MY_QUEUE.queue:
                lock.acquire()
                try:
                    if ticker not in config.SENDED_TICKERS:
                        config.SENDED_TICKERS.append(ticker)
                        notify = True
                    else:
                        notify = False
                except:
                    notify = False
                finally:
                    lock.release()
                
                if notify:
                    config.MY_QUEUE.put(reply_text)


def get_figi_data(figi):
    """Gets all data of current figi."""

    # creating database cursor
    database = sqlite3.connect("tinkoff.db")
    cursor = database.cursor()

    figi_info = cursor.execute(f"SELECT * FROM available WHERE figi='{figi}'").fetchall()

    cursor.close()
    database.close()

    if figi_info != []:
        figi_info = figi_info[0]
    
    return figi_info


def get_close_price(figi):
    """Gets the previous trade day close price."""

    try:
        with Client(config.TINKOFF_TOKEN, target=INVEST_GRPC_API) as client:
            price = client.market_data.get_close_prices(
                instruments=[InstrumentClosePriceRequest(instrument_id=figi)],
                )
            close_price = utils.price_converter(price.close_prices[-1].price)
            logging.info(f'{inspect.currentframe().f_code.co_name}: Получена цена закрытия для {figi}.')

    except Exception as ex:
        logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось определить цену закрытия для {figi}. {ex}')
        close_price = 0
    
    return close_price


def construct_reply(name, ticker, lot, currency, close_price, close, 
                    open, volume, time, price_flag, volume_flag):
    
    """Constructs notification message based on received data."""

    trigger = ''
    if price_flag:
        trigger += 'цена, '
    if volume_flag:
        trigger += 'объем, '
    
    trigger = trigger.rstrip(', ')

    delta = round(abs(close - open), 2)
    delta = utils.number_format(delta)

    percent = round(((close - open) / open) * 100, 2)


    lot_price = round(lot * close, 2)
    volume_price = close * lot * volume
    lot = utils.number_format(lot)
    lot_price = utils.number_format(lot_price)
    volume_price = utils.full_price_format(volume_price)


    if close_price != 0:
        prevprice_percent =  round((close - close_price) / close_price * 100, 2)
        prevprice_percent = utils.number_format(prevprice_percent)
    else:
        close_price = 'не определено'
        prevprice_percent = 'не определено'
    
    close = utils.number_format(round(close, 5))
    volume = utils.number_format(volume)

    time = (time + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

    reply_text = f'''
                    \n*[{name}](https://www.tinkoff.ru/invest/stocks/{ticker}?utm_source=security_share)*\
                    \nТикер: \#*{ticker}*\
                    \nДельта: *{delta} {currency}*\
                    \nИзменение цены: *{percent}%*\
                    \nЦена объема: *{volume_price} {currency}*\
                    \nВремя: *{time}*\
                    \nЦена закрытия: *{close} {currency}*\
                    \nИзменение цены за день: *{prevprice_percent}%*\
                    \nТриггер: *{trigger}*\
    '''.replace('.', '\.').replace('-', '\-').replace('+', '\+')

    return reply_text


def track_available_shares():
    """Tracks shares that available on MOEX."""

    shares = get_all_from_available()
    instruments = instruments_to_subscribe(shares)
    start_tracking(instruments)


def send_notifications():
    """Send notifications when rise anomalies."""

    while True:
        try:
            bot.send_message(chat_id=config.CHANNEL_ID,
                            text=config.MY_QUEUE.get(),
                            parse_mode='MarkdownV2',
                            disable_web_page_preview=True,
                            )
            time.sleep(1)
        except Exception as ex:
            logging.error(f'{inspect.currentframe().f_code.co_name}: Не удалось отправить сообщение. {ex}')
            pass


def update_all_data():
    """Updates tables."""

    while True:
        shares = get_all_available_share()
        sort_shares(shares)
        time.sleep(10000)


def clear_sended():
    while True:
        config.SENDED_TICKERS.clear()
        time.sleep(25)