import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
from Auxiliary_functions import get_twitch_token, format_twitch_date
from dotenv import load_dotenv
from Streamer import Streamer
from data_base import save_user_to_db

load_dotenv()


# TODO: Убрать после теста
# FIXME: Временное решение
# HACK: Костыль, переделать


TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not all([TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TELEGRAM_BOT_TOKEN]):
    raise Exception("Не хватает переменных окружения в .env файле!")


# Получаем Twitch токен

try:
    TWITCH_ACCESS_TOKEN = get_twitch_token(TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET=TWITCH_CLIENT_SECRET)
    print("Twitch access token получен")
except Exception as e:
    print(e)
    exit()


#Создаём бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
popular_streamers = ["Buster", "Evelone2004", "Anar Abdullaev", "Enzzai", "Whylollycry", "StRoGo"]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    save_user_to_db(user)
    markup = ReplyKeyboardMarkup(row_width=6)
    for streamer in popular_streamers:
        button = KeyboardButton(streamer)
        markup.add(button)
    bot.reply_to(message, """
👋 <b>Привет! Я — Twitch Analytics Bot!</b>
Я помогу тебе анализировать стримеров на Twitch:
📌 Просто отправь имя стримера, например:
   <code>Evelone2004</code>
    """, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "support":
            message = "Поддерживая проект, вы попадаете в эксклюзивный список спонсоров, у которых есть премиальные возможности"
            photo_donate = "https://lfb.su/assets/components/phpthumbof/cache/EP_9164.5829e9bb4bbfce8e8b20161f14bb89752225.png"
            ways_for_pay = {
                "Boosty": {"url": "https://twitch-analitics-bot-web.vercel.app/"},
                "Telegram-stars": {"url": "https://twitch-analitics-bot-web.vercel.app/"},
                "СБП": {"url": "https://twitch-analitics-bot-web.vercel.app/"},
            }
            markup = InlineKeyboardMarkup()
            for way in ways_for_pay:
                btn = InlineKeyboardButton(way, url=ways_for_pay[way]['url'])
                markup.add(btn)
            bot.send_photo(call.message.chat.id, photo=photo_donate, caption=message, reply_markup=markup)


        elif call.data == "Boosty":
            bot.send_message(call.message.chat.id, "Вы выбрали Boosty")

        elif call.data == "Telegram-stars":
            bot.send_message(call.message.chat.id, "Вы выбрали Telegram-stars")

    bot.answer_callback_query(callback_query_id=call.id, text="Действие выполнено")




@bot.message_handler(func=lambda message: True)
def handle_streamer_name(message):
    streamer_name = message.text.strip().replace(" ", "")

    # Валидация
    if not streamer_name.isalnum() or len(streamer_name) > 25:
        bot.reply_to(message, "⚠️ Введите корректное имя стримера (буквы и цифры, до 25 символов).")
        return

    STREAMER = Streamer(streamer_name)

    # Получаем данные о стримере
    streamer_data = STREAMER.get_streamer_info(streamer_name=streamer_name, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)

    if not streamer_data.get('data'):
        bot.reply_to(message, f"❌ Стример с именем '{streamer_name}' не найден на Twitch.")
        return


    # Проверяем, онлайн ли
    stream_data = STREAMER.get_stream_info(streamer_id= STREAMER.streamer_id, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    is_live = bool(stream_data.get('data'))


    # Формируем ответ
    if is_live:

        reply = f"""
📊 <b>{STREAMER.streamer_display_name}</b> — 🔴 В эфире

🎮 Игра: <i>{STREAMER.stream["game"]}</i>
👀 Зрителей: <b>{STREAMER.stream["viewers"]}</b>
📌 Название: <code>{STREAMER.stream["title"]}</code>
🕒 Начало: {STREAMER.stream["started_at"]}
🎮 Стрим: <a href='{STREAMER.stream["url"]}'>Смотреть на Twitch</a>
   Канал был создан:{STREAMER.streamer_was_created}
        """
    else:
        reply = f"""
📊 <b>{STREAMER.streamer_display_name}</b> — 🟢 Оффлайн

📌 <code>{STREAMER.streamer_description}</code>

    Канал был создан: {STREAMER.streamer_was_created}
        """



    # Отправляем фото + текст
    if is_live and STREAMER.photo_online != "Error image":
        try:
            bot.send_photo(message.chat.id, STREAMER.photo_online, caption=reply, parse_mode='HTML')
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка отправки фото: {e}")

    elif not is_live and STREAMER.photo_offline != "Error image":
        try:
            bot.send_photo(message.chat.id, STREAMER.photo_offline, caption=reply, parse_mode='HTML')
        except  Exception as e:
            bot.send_message(message.chat.id, f"Ошибка отправки фото: {e}")

    else:
        try:
            bot.send_message(message.chat.id, reply, parse_mode="HTML")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка отправки фото: {e}")



    # Получаем последний VOD
    vod = STREAMER.get_last_vod( streamer_id=STREAMER.streamer_id, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)



    # Если есть VOD — предлагаем скачать
    if vod:
        bot.send_message(
            message.chat.id,
            f"🟣 <b>Найден последний стрим <i>{STREAMER.streamer_display_name}</i></b>\n"
            f"────────────────\n"
            f"🎮 <b>{STREAMER.last_vod['title']}</b>\n"
            f"📅 <i>Опубликован:</i> {STREAMER.last_vod['published']}\n"
            f"⏱ <i>Длительность:</i> {STREAMER.last_vod['duration']}\n"
            f"👁 <i>Просмотры:</i> {STREAMER.last_vod['view_counts']}\n\n"
            f"🔗 <a href='{STREAMER.last_vod["url"]}'>🎬 Смотреть на Twitch</a>\n\n",
            # f"Хочешь скачать его? Напиши: <code>/download {vod_id}</code>"
            parse_mode='HTML',
        )
    else:
        bot.send_message(message.chat.id, "📌 У стримера пока нет записей стримов.")


bot.polling(none_stop=True)
# if __name__ == "__main__":
#     bot.remove_webhook()
#     if os.getenv("ENV") == "production":
#         url =os.getenv("NETWORK")
#         bot.set_webhook(url= url)
#     else:
#         bot.polling(none_stop=True)

