import telebot
import threading

import config
import functions

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

threading.Thread(daemon=True, target=functions.update_all_data).start()
threading.Thread(daemon=True, target=functions.track_available_shares).start()
threading.Thread(daemon=True, target=functions.send_notifications).start()
threading.Thread(daemon=True, target=functions.clear_sended).start()

@bot.message_handler(commands=['stop'])
def stop_command(message):
    """Handles the 'stop' command."""

    if str(message.from_user.id) in config.MANAGERS_ID:
        config.WORK_FLAG = False

        bot.send_message(chat_id=message.chat.id,
                            text='Уведомления отключены.',
                            )
    else:
        bot.send_message(chat_id=message.chat.id,
                        text=f'Недостаточно прав доступа.',
                        )


@bot.message_handler(commands=['restart'])
def restart_command(message):
    """Handles the 'stop' command."""

    if str(message.from_user.id) in config.MANAGERS_ID:
        if not config.WORK_FLAG:
            config.WORK_FLAG = True
            threading.Thread(daemon=True, target=functions.track_available_shares).start()

            bot.send_message(chat_id=message.chat.id,
                            text='Уведомления включены.',
                        )
    else:
        bot.send_message(chat_id=message.chat.id,
                        text=f'Недостаточно прав доступа.',
                        )
    

@bot.message_handler(commands=['status'])
def status_command(message):
    """Handles the 'stop' command."""

    if str(message.from_user.id) in config.MANAGERS_ID:
        status = 'уведомления отключены'
        if config.WORK_FLAG:
            status = 'уведомления включены'
        
        bot.send_message(chat_id=message.chat.id,
                        text=f'*Статус:* {status}.',
                        parse_mode='Markdown'
                        )
    else:
        bot.send_message(chat_id=message.chat.id,
                        text=f'Недостаточно прав доступа.',
                        )


if __name__ == '__main__':
    # bot.polling(timeout=80)
    while True:
        try:
            bot.polling()
        except:
            pass