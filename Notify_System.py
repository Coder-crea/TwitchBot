import logging
from data_base import get_subscribers, get_all_subscribed_streamers
from Streamers import Streamer


def check_streamers(bot, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    # Все стримеры, на которых кто-то подписан
    streamers = get_all_subscribed_streamers()

    for streamer in streamers:
        is_live = is_streamer_live(streamer, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN)
        # was_live = was_streamer_live_before(streamer)  # из БД

        if is_live: #  not was_live
            notify_stream_start(bot, streamer)

        # Обновляем статус в БД
        # update_streamer_status(streamer, is_live)




def notify_stream_start(bot, streamer_login):
    subscribes = get_subscribers(streamer_login)
    for user_id in subscribes:
        try:
            bot.send_message(chat_id=user_id, text=f"🔴 {streamer_login} начал стрим!\n\n"
                     f"🎮 Зайди и посмотри: https://twitch.tv/{streamer_login}", parse_mode='HTML')
        except Exception as e:
            logging.error(f"Не удалось отправить {user_id}: {e}")


def is_streamer_live(streamer, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    try:
        STREAMER= Streamer(streamer_name=streamer)
        stream_data = STREAMER.get_stream_info(streamer_id=streamer, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
        is_live = bool(stream_data.get('data'))
        return is_live
    except Exception as e:
        logging.error(f"Ошибка при получении онлайна стримера: {e}")
        return False