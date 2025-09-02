import requests
from datetime import datetime
import logging


def get_twitch_token(*,TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET):
    url= "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=data)
    res_data = response.json()
    if "access_token" in res_data:
        return res_data["access_token"]
    else:
        raise Exception(f"Ошибка получения токена: {data}")


def format_twitch_date(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
        # Можно добавить tzinfo и конвертировать, если нужно
        return dt.strftime("%d.%m.%Y в %H:%M")
    except ValueError:
        return "неверный формат даты"


def get_streamer_name_by_caption(*, caption:str)->str:
    return caption.split(" ")[1]


def get_text_for_message_of_subscribes(all_followed_streamers_by_user):
    if not all_followed_streamers_by_user:
        return "📭 Вы не подписаны ни на одного стримера.\nОтправьте ник стримера, чтобы подписаться"

    # Делаем каждый ник жирным через HTML
    formatted_streamers = [f"{i+1}.<b>{streamer}</b>" for i, streamer in enumerate(all_followed_streamers_by_user)]
    return "Вы подписаны на:\n" + "\n".join(formatted_streamers) + "\nЧтобы отписаться введите команду /unsubscribe имя_стримера" #join может итерировать объект??????