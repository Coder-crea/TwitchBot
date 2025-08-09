import logging
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise Exception("Не хватает переменных (DB) окружения в .env файле!")

# Инициализация клиента
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
