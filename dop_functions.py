import requests
from datetime import datetime
import yt_dlp
import os
from supabase import create_client

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


def get_streamer_info(*, username, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    params = {"login": username.lower()}
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def get_stream_info(*, streamer_user_id, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    url="https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    params = {"user_id": streamer_user_id}
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def format_twitch_date(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
        # Можно добавить tzinfo и конвертировать, если нужно
        return dt.strftime("%d.%m.%Y в %H:%M")
    except ValueError:
        return "неверный формат даты"


def get_last_vod(*, user_id, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
    url = "https://api.twitch.tv/helix/videos"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    params = {
        "user_id": user_id,
        "first": 1,
        "type": "archive"  # 'archive' = VOD, 'highlight' = clip, 'upload' = manually uploaded
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if data.get('data'):
        return data['data'][0]  # Возвращаем последний VOD
    else:
        return None


# def download_vod(vod_id, output_path="vod.mp4"):
#     """
#     Скачивает VOD с Twitch по ID
#     :param vod_id: ID стрима (число)
#     :param output_path: Куда сохранить файл
#     :return: путь к файлу или None при ошибке
#     """
#     url = f"https://www.twitch.tv/videos/{vod_id}"
#
#     ydl_opts = {
#         'outtmpl': output_path,  # имя файла
#         'format': 'bestvideo+bestaudio/best',  # лучшее качество
#         'noplaylist': True,
#         'quiet': False,  # показывать логи (для отладки)
#         'no_warnings': False,
#         'retries': 3,
#         'fragment_retries': 5,
#         'socket_timeout': 15,
#         'merge_output_format': 'mp4',  # объединить в mp4
#     }
#
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
#
#         # Убедимся, что файл существует
#         if os.path.exists(output_path):
#             return output_path
#         else:
#             # Возможно, yt-dlp сохранил с другим расширением
#             base, ext = os.path.splitext(output_path)
#             for ext in ['.mp4', '.mkv', '.webm']:
#                 if os.path.exists(base + ext):
#                     return base + ext
#             return None
#
#     except Exception as e:
#         print(f"❌ Ошибка при скачивании VOD: {e}")
#         return None
