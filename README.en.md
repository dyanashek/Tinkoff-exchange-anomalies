# Tinkoff exchange anomalies
## Изменить язык: [Русский](README.md)
***
Sends notifications to a specific channel in case of an abnormal change in the price or volume of a trading instrument traded on MOEX with the Tinkoff broker.
## [DEMO](README.demo.md)
## Commands:
**Add via [BotFather](https://t.me/BotFather) for easy display.**
- **stop** - stops sending notifications
- **restart** - resumes sending notifications
- **status** - displays the status of the bot (notifications enabled or not)
> These commands are only accepted from authorized users and must be sent in a separate chat with the bot. To grant access see "setting .env"
## .env setup:
- in the file, specify the bot's telegram token and the access token to TinkoffInvest Api:\
**TELEBOT_TOKEN**=TOKEN\
**TINKOFF_TOKEN**=TOKEN
- **SIGMA_COEFF** is responsible for the sensitivity of notifications to changes in volume (the calculated sigma is multiplied by this coefficient, respectively, if the coefficient is less than 1, notifications are more sensitive, if the coefficient is greater than 1, they are less sensitive).\
Initially **SIGMA_COEFF = 1**
- the variable **DELTA_SIGMA_COEFF** is responsible for the sensitivity of notifications to price changes within one candle, the principle of operation is the same as **SIGMA_COEFF** (it is recommended to make notifications less sensitive, because the value often tends to 0.1% of the asset price) \
Initially **DELTA_SIGMA_COEFF = 3**
- the **CHANNEL_ID** variable contains the ID of the channel where notifications should come, you need to insert the required ID. **Bot must be added as a channel administrator** (change in the upper right corner of the profile channel -> administrators -> add administrator, allow sending messages)
> To determine the channel ID, forward any channel post to the next [bot](https://t.me/getmyid_bot). The value contained in **Forwarded from chat** - channel ID
- **MANAGERS_ID** lists user IDs that have access to execute commands. IDs should be listed separated by commas with a space - (for example: MANAGERS_ID=1234 - one user, MANAGERS_ID=1234, 5678 - two users, etc.)
> To determine the user ID, you need to send any message from the corresponding account to the next [bot](https://t.me/getmyid_bot). Value contained in **Your user ID** - User ID
- flag **LOGGING_FILE** is responsible for logging to a file (if set to 1) or console (if set to 0)\
Initially **LOGGING_FILE=0**
## Installation and use:
**Python not higher than 3.9.13**
- create and activate virtual environment (if necessary):
```sh
python3 -m venv venv
source venv/bin/activate # for mac
source venv/Scripts/activate # for windows
```
- Install dependencies:
```sh
pip install -r requirements.txt
```
- run the project:
```sh
python3 main.py
```
## Features of use:
- the bot starts working with an already formed database containing all information about the instrument: the availability of obtaining historical candles, sigma and delta calculated for the previous seven-day period (weekend data are not taken into account), lot size, trading currency
- data is updated every 3 hours
- if a new tool appears available for tracking, it is automatically entered into the database, however, tracking on it will only start when the bot is restarted (successively the command **/stop**, then **/restart**)
- the maximum number of tickers available for tracking is 300, currently 231 tickers are being tracked. If this number exceeds 300, the last ones added will be cut off.