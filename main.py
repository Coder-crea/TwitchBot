import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
from Auxiliary_functions import get_twitch_token, get_streamer_name_by_caption
from dotenv import load_dotenv
from Streamers import Streamer
from data_base import save_user_to_db, subscribe_user_to_streamer, get_subscribers
import logging
from Notify_System import check_streamers



logging.basicConfig(level=logging.INFO)


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
        if call.data == "subscribe":
            try:
                streamer_name = get_streamer_name_by_caption(caption=call.message.caption)
            except  Exception as e:
                logging.warning("Ошибка получения информации об имени стримера")
                bot.send_message(call.message.chat.id, f"Ошибка получения информации, а точнее имени стримера. Подробнее: {e}")

            if streamer_name:
                success = subscribe_user_to_streamer(user_id=call.from_user.id, streamer_login=streamer_name)
                if success:
                    check_streamers(bot, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN)
                    bot.send_message(call.message.chat.id, f"✅ Вы успешно подписались на {streamer_name}")

                else:
                    bot.send_message(call.message.chat.id, "❌ Ошибка при подписке")
            else:
                logging.error("❌ Пустое имя стримера")


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


    subscribe = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Подписаться', callback_data="subscribe")
    subscribe.add(button)


    # Отправляем фото + текст
    if is_live and STREAMER.photo_online != "Error image":
        try:
            bot.send_photo(message.chat.id, STREAMER.photo_online, caption=reply, parse_mode='HTML', reply_markup= subscribe )
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка отправки фото: {e}")

    elif not is_live and STREAMER.photo_offline != "Error image":
        try:
            bot.send_photo(message.chat.id, STREAMER.photo_offline, caption=reply, parse_mode='HTML', reply_markup= subscribe)
        except  Exception as e:
            bot.send_message(message.chat.id, f"Ошибка отправки фото: {e}")

    else:
        try:
            bot.send_message(message.chat.id, reply, parse_mode="HTML", reply_markup= subscribe)
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


