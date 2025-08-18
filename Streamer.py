import requests
from Auxiliary_functions import format_twitch_date


class Streamer:


    def __init__(self, streamer_name):
        self.streamer_name = streamer_name
        self.streamer_id = None
        self.streamer_login = None
        self.streamer_display_name = None
        self.streamer_description = None
        self.streamer_was_created = None
        self.photo_online = None
        self.photo_offline = None

        self.stream = {}
        self.last_vod = {}


    def get_streamer_info(self, *, streamer_name, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
        }
        params = {"login": streamer_name.lower()}
        response = requests.get(url, headers=headers, params=params)

        if response.json().get('data'):
            info = response.json()["data"][0]
            print(info)
            self.streamer_id = info['id'] if info.get('id') else None
            self.streamer_login = info['login'] if info.get('login') else None
            self.streamer_display_name = info['display_name'] if info.get('display_name') else None
            self.streamer_description = info['description'] if info.get('description') else None
            self.streamer_was_created = format_twitch_date(info["created_at"] if info.get('created_at') else None)
            self.photo_online = (info.get('profile_image_url') or "Error image").strip()
            self.photo_offline = (info.get('offline_image_url') or "Error image").strip()
        return response.json()


    def get_stream_info(self, *, streamer_id, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
        url = "https://api.twitch.tv/helix/streams"
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
        }
        params = {"user_id": streamer_id}
        response = requests.get(url, headers=headers, params=params)
        is_live = bool(response.json().get('data'))
        if is_live:
            info = response.json()['data'][0]
            self.stream = {
                "viewers": f"{info['viewer_count']:,}".replace(",", " "),
                "game" : info['game_name'] if info.get('game_name') else None,
                "title" : info['title'] if info.get('title') else None,
                "started_at" : format_twitch_date(info['started_at']) if info.get('started_at') else None,
                "url" : f"https://twitch.tv/{self.streamer_login}",
            }
        return response.json()



    def get_last_vod(self, *, streamer_id, TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN):
        url = "https://api.twitch.tv/helix/videos"
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
        }
        params = {
            "user_id": streamer_id,
            "first": 1,
            "type": "archive"  # 'archive' = VOD, 'highlight' = clip, 'upload' = manually uploaded
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get('data'):
            info = data['data'][0]
            self.last_vod= {
            "vod_id" : info['id'] if info.get('id') else None,
            "title" : info['title'] if info.get('title') else None,
            "duration" : info['duration'] if info.get('duration') else None,
            "published" : format_twitch_date(info['published_at']) if info.get('published_at') else None,
            "url" : f"https://www.twitch.tv/videos/{info['id'] if info.get('id') else None}",
             "view_counts" : f"{info['view_count']:,}".replace(",", " ") if info.get('view_count') else None
            }
            return data['data'][0]  # Возвращаем последний VOD
        else:
            return None




