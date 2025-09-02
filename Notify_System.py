import logging
from data_base import get_subscribers, get_all_subscribed_streamers, was_streamer_live_before, update_streamer_status
from Streamers import Streamer
import threading
import time


def start_background_check(bot, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    def run():
        while True:
            try:
                check_streamers(bot,TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN)
            except Exception as e:
                print(f"Ошибка в фоновой проверке: {e}")
            time.sleep(60)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()






def check_streamers(bot, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    # Все стримеры, на которых кто-то подписан
    streamers = get_all_subscribed_streamers()

    for streamer in streamers:
        is_live = is_streamer_live(streamer, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN)
        was_live = was_streamer_live_before(streamer)

        if is_live and not was_live:
            notify_stream_start(bot, streamer)

        # Обновляем статус в БД
        update_streamer_status(streamer, is_live)




def notify_stream_start(bot, streamer_login):
    subscribes = get_subscribers(streamer_login)
    for user_id in subscribes:
        try:
            bot.send_message(chat_id=user_id, text=f"🔴 {streamer_login} начал стрим!\n\n"
                     f"🎮 Зайди и посмотри: <a href='https://twitch.tv/{streamer_login}'>Смотреть</a>", parse_mode='HTML')
        except Exception as e:
            logging.error(f"Не удалось отправить {user_id}: {e}")


def is_streamer_live(streamer, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    try:
        STREAMER = Streamer(streamer_name=streamer)
        STREAMER.get_streamer_info(streamer_name=streamer, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
        stream_data = STREAMER.get_stream_info(streamer_id=STREAMER.streamer_id, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
        is_live = bool(stream_data.get('data'))
        return is_live
    except Exception as e:
        logging.error(f"Ошибка при получении онлайна стримера: {e}")
        return False
