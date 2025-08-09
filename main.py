import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
from dotenv import load_dotenv
from dop_functions import get_twitch_token, get_streamer_info, get_stream_info, format_twitch_date, get_last_vod #,download_vod
from data_base import save_user_to_db
load_dotenv()

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

# Команда для скачивания VOD
# @bot.message_handler(commands=['download'])
# def download_vod_command(message):
#     try:
#         vod_id = message.text.split()[1]
#     except IndexError:
#         bot.reply_to(message, "UsageId: /download 123456789")
#         return
#
#     bot.send_message(message.chat.id, "⏳ Начинаю загрузку VOD... Это может занять время.")
#
#     video_path = f"vod_{vod_id}.mp4"
#     downloaded_file = download_vod(vod_id, video_path)
#
#     if downloaded_file and os.path.exists(downloaded_file):
#         # Проверим размер
#         file_size = os.path.getsize(downloaded_file)
#         try:
#             with open(downloaded_file, 'rb') as f:
#                 if file_size > 50 * 1024 * 1024:
#                     bot.send_document(message.chat.id, f, caption="📹 VOD (файл)")
#                 else:
#                     bot.send_video(message.chat.id, f, caption="📹 VOD")
#         except Exception as e:
#             bot.send_message(message.chat.id, f"❌ Ошибка отправки: {e}")
#         finally:
#             os.remove(downloaded_file)
#     else:
#         bot.send_message(message.chat.id, "❌ Не удалось скачать VOD.")

# ways_for_pay = {
#     "Boosty": {"url": "https://twitch-analitics-bot-web.vercel.app/"},
#     "Telegram-stars":{"url": "https://twitch-analitics-bot-web.vercel.app/"},
#     "СБП":{"url": "https://twitch-analitics-bot-web.vercel.app/"},
# }
# for way in ways_for_pay:
#     print(ways_for_pay[way]["url"])
# print(type(ways_for_pay))

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
    streamer = message.text.strip().replace(" ", "")

    # Валидация
    if not streamer.isalnum() or len(streamer) > 25:
        bot.reply_to(message, "⚠️ Введите корректное имя стримера (буквы и цифры, до 25 символов).")
        return

    # Получаем данные о стримере
    streamer_data = get_streamer_info(username=streamer, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    if not streamer_data.get('data'):
        bot.reply_to(message, f"❌ Стример с именем '{streamer}' не найден на Twitch.")
        return

    user = streamer_data['data'][0]
    user_id = user['id']
    user_login = user['login']
    display_name = user['display_name']
    description = user["description"]
    was_created = format_twitch_date(user["created_at"])
    # view_count = f"{user['view_count']:,}".replace(',', ' ')

    # Проверяем, онлайн ли
    stream_data = get_stream_info(streamer_user_id= user_id, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    is_live = bool(stream_data.get('data'))

    # Получаем последний VOD
    vod = get_last_vod(user_id=user_id, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)

    # Формируем ответ
    if is_live:
        stream = stream_data['data'][0]
        viewers = f"{stream['viewer_count']:,}".replace(",", " ")
        game = stream['game_name']
        title = stream['title']
        started_at = format_twitch_date(stream['started_at'])
        url = f"https://twitch.tv/{user_login}"



        reply = f"""
📊 <b>{display_name}</b> — 🔴 В эфире

🎮 Игра: <i>{game}</i>
👀 Зрителей: <b>{viewers}</b>
📌 Название: <code>{title}</code>
🕒 Начало: {started_at}
🎮 Стрим: <a href='{url}'>Смотреть на Twitch</a>
   Канал был создан:{was_created}
        """
    else:
        reply = f"""
📊 <b>{display_name}</b> — 🟢 Оффлайн

📌 <code>{description}</code>

    Канал был создан: {was_created}
        """

    # Отправляем фото + текст
    if is_live:
        photo_url = user.get('profile_image_url')
    else:
        photo_url = user.get('offline_image_url')


    bot.send_photo(message.chat.id, photo_url, caption=reply, parse_mode='HTML') #, reply_markup=markup

    #support part

    # markup_support = InlineKeyboardMarkup()
    # btn = InlineKeyboardButton("ПОМОГИ ПРОЕКТУ", callback_data="support")
    # markup_support.add(btn)


    # Если есть VOD — предлагаем скачать
    if vod:
        vod_id = vod['id']
        title = vod['title']
        duration = vod['duration']
        published = format_twitch_date(vod['published_at'])
        url = f"https://www.twitch.tv/videos/{vod_id}"
        view_counts = f"{vod['view_count']:,}".replace(",", " ")



        bot.send_message(
            message.chat.id,
            f"🟣 <b>Найден последний стрим 👤 {display_name}</b>\n"
            f"────────────────\n"
            f"🎮 <b>{title}</b>\n"
            f"📅 <i>Опубликован:</i> {published}\n"
            f"⏱ <i>Длительность:</i> {duration}\n"
            f"👁 <i>Просмотры:</i> {view_counts}\n\n"
            f"🔗 <a href='{url}'>🎬 Смотреть на Twitch</a>\n\n",
            # f"Хочешь скачать его? Напиши: <code>/download {vod_id}</code>"
            parse_mode='HTML',
        )
    else:
        bot.send_message(message.chat.id, "📌 У стримера пока нет записей стримов.")

# print(get_streamer_info(username="whylollycry", TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN))
# print(get_last_vod(user_id=490666905, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN))

bot.polling(none_stop=True)

