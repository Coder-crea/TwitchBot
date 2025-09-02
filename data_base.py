import logging
import os


from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
    raise Exception("Не хватает переменных (DB) окружения в .env файле!")

# Инициализация клиента
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)

def save_user_to_db(user, is_sponsor=False):
    try:
        response = supabase.table("users").upsert({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_sponsor": is_sponsor
        }).execute()

        logging.info(f"Пользователь {user.id} сохранён/обновлён")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя {user.id}: {e}")
        return False



def subscribe_user_to_streamer(user_id: int, streamer_login: str) -> bool:
    # Подписывает пользователя на стримера с использованием upsert / или обновляется***
    try:
        result = supabase.table("subscriptions").upsert(
            {
                "user_id": user_id,
                "streamer_login": streamer_login.lower(),
            },
            on_conflict="user_id,streamer_login"  # указываем колонки, по которым может быть конфликт
        ).execute()

        logging.info(f"Пользователь {user_id} подписан на {streamer_login}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при подписке {user_id} на {streamer_login}: {e}")
        return False


def unsubscribe_user(user_id: int, streamer_login: str):
    try:
        supabase.table("subscriptions") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("streamer_login", streamer_login.lower()) \
            .execute()
        logging.info(f"Пользователь {user_id} отписан от {streamer_login}")
    except Exception as e:
        logging.error(f"Ошибка при отписке: {e}")



def get_subscribers(streamer_login: str):
    try:
        response = supabase.table("subscriptions") \
            .select("user_id") \
            .eq("streamer_login", streamer_login.lower()) \
            .execute()
        return [row["user_id"] for row in response.data]
    except Exception as e:
        logging.error(f"Ошибка при получении подписчиков: {e}")
        return []


def get_all_subscribed_streamers():
    try:
        response = supabase.table("subscriptions") \
        .select("streamer_login") \
        .execute()
        all_streamers = [row["streamer_login"] for row in response.data]
        unique_name_streamers = set(all_streamers)
        return unique_name_streamers
    except Exception as e:
        logging.error(f"Ошибка при получении всех стримеров из бд: {e}")
        return []


def was_streamer_live_before(streamer_login):
    try:
        response = supabase.table("streamer_status") \
        .select("is_live") \
        .eq("streamer_login", streamer_login.lower()) \
        .execute()
        if response.data:
            return response.data[0]["is_live"]
        return False
    except Exception as e:
        print(f"Ошибка при проверке предыдущего статуса {streamer_login}: {e}")
        return False

def update_streamer_status(streamer_login, is_live):
    try:
        supabase.table("streamer_status").upsert({
            "streamer_login": streamer_login.lower(),
            "is_live": is_live
        }).execute()
    except Exception as e:
        print(f"Ошибка при обновлении статуса {streamer_login}: {e}")


def get_all_followed_streamers_by_user(user_id):
    try:
        response = supabase.table("subscriptions") \
        .select("streamer_login") \
        .eq("user_id", user_id) \
        .execute()
        return [row["streamer_login"] for row in response.data]
    except Exception as e:
        print(f"Ошибка получения подписок пользователя: {e}")