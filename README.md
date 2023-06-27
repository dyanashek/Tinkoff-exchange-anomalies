# Tinkoff exchange anomalies
## Change language: [English](README.en.md)
***
Присылает уведомления в определенный канал в случае аномального изменения цены или объема по торговому инструменту, торгующемуся на MOEX у брокера Tinkoff.
## [DEMO](README.demo.md)
## Команды:
**Добавить через [BotFather](https://t.me/BotFather) для удобного отображения.**
- **stop** - останавливает отправку уведомлений
- **restart** - возобновляет отправку уведомлений
- **status** - отображает статус работы бота (включены уведомления или нет)
> Данные команды принимаются только от имеющих доступ пользователей и должны быть отправлены в отдельном чате с ботом. Для предоставления доступа смотри "настройка .env"
## Настройка .env:
- в файле указать токен телеграмм бота и токен доступа к TinkoffInvest Api:\
**TELEBOT_TOKEN**=ТОКЕН\
**TINKOFF_TOKEN**=ТОКЕН
- **SIGMA_COEFF** отвечает за чувствительность уведомлений к изменению объема (рассчитанная сигма умножается на данный коэффициент, соответственно при коэффициенте меньше 1 - уведомления более чувствительны, при коэффициенте больше 1 - менее чувствительны).\
Изначально **SIGMA_COEFF = 1**
- переменная **DELTA_SIGMA_COEFF** отвечает за чувствительность уведомлений к изменению цены в рамках одной свечи, принцип работы одинаков с **SIGMA_COEFF** (рекомендуется сделать уведомления менее чувствительными, т.к. значение часто стремится к 0.1% процента от цены актива)\
Изначально **DELTA_SIGMA_COEFF = 3**
- в переменной **CHANNEL_ID** содержится ID канала, куда должны приходить уведомления, необходимо вставить нужный ID. **Бот должен быть добавлен в качестве администратора канала** (изм. в правом верхнем углу профиля канал -> администраторы -> добавить администратора, разрешить отправку сообщений)
> Для определения ID канала нужно переслать любую публикацию канала в следующий [бот](https://t.me/getmyid_bot). Значение, содержащееся в **Forwarded from chat** - ID канала
- в **MANAGERS_ID** перечислены ID пользователей, имеющих доступ к выполнению команд. ID следует перечислять через запятую с пробелом - (например: MANAGERS_ID=1234 - один пользователь, MANAGERS_ID=1234, 5678 - два пользователя и т.д.) 
> Для определения ID пользователя нужно отправить следующему [боту](https://t.me/getmyid_bot) любое сообщение с соответствующего аккаунта. Значение, содержащееся в **Your user ID** - ID пользователя
- флаг **LOGGING_FILE** отвечает за логирование в файл (при значении 1) или консоль (при значении 0)\
Изначально **LOGGING_FILE=0**
## Установка и использование:
**Python не выше 3.9.13**
- создать и активировать виртуальное окружение (если необходимо):
```sh
python3 -m venv venv
source venv/bin/activate # for mac
source venv/Scripts/activate # for windows
```
- Установить зависимости:
```sh
pip install -r requirements.txt
```
- запустить проект:
```sh
python3 main.py
```
## Особенности использования:
- бот начинает работу с уже сформированной базой данных, содержащей всю информацию об инструменте: доступность получения исторических свечей, сигмы и дельты, рассчитанные за предшествующий семидневный период (данные выходных дней в расчет не принимаются), лотность, валюта торгов
- данные обновляются раз в 3 часа
- в случае если появляется новый инструмент, доступный для отслеживания - он автоматически вносится в базу данных, однако отслеживание по нему начнется только при перезапуске бота (последовательно команда **/stop**, затем **/restart**)
- максимальное количество тикеров, доступное для отслеживания - 300, на данный момент отслеживается 231 тикер. В случае если это количество превысит 300 - последние добавленные будут отсечены.