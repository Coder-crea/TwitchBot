from Streamers import Streamer
from Auxiliary_functions import get_twitch_token
import os
from dotenv import load_dotenv
import pytest

load_dotenv()
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")


try:
    TWITCH_ACCESS_TOKEN = get_twitch_token(TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET=TWITCH_CLIENT_SECRET)
    print("Twitch access token получен")
except Exception as e:
    print(e)
    exit()

@pytest.fixture()
def streamer():
    return Streamer("buster")


def test_streamer_info(streamer):
    info = streamer.get_streamer_info(streamer_name=streamer.streamer_name, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    print(info)
    assert info["data"][0]['display_name'] == "buster"


def test_streamer_profile_image(streamer):
    info = streamer.get_streamer_info(streamer_name=streamer.streamer_name, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    assert info["data"][0]['profile_image_url'] == streamer.photo_online


def test_streamer_offline_image(streamer):
    info = streamer.get_streamer_info(streamer_name=streamer.streamer_name, TWITCH_CLIENT_ID=TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN=TWITCH_ACCESS_TOKEN)
    assert info["data"][0]['offline_image_url'] == streamer.photo_offline