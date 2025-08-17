import requests
from datetime import datetime

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