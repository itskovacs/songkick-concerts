import time
from datetime import datetime
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

BASE_URL = "https://www.songkick.com"
CACHE_FILE = Path(__file__).with_name(".concerts.cache")
ENV_FILE = Path(__file__).with_name("env.yaml")
CONCERT_CACHE = set()
ENV = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3"
}


# Utility Functions
def notify(text: str):
    token = get_env("telegram").get("token")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
            "text": "🎵 "+text,
            "chat_id": get_env("telegram").get("chatID"),
            "parse_mode": "markdown",
            "disable_web_page_preview": True,
        }
    requests.post(url, json=data)


def get_page(url: str):
    resp = requests.get(url, headers=HEADERS)
    return resp.text if resp.status_code == 200 else None

def load_env():
    global ENV
    if not ENV_FILE.exists():
        raise FileNotFoundError("Missing env.yaml file")

    with open(ENV_FILE, "r", encoding="utf-8") as f:
        ENV = yaml.safe_load(f) or {}

    required_keys = ["telegram", "artists", "countries", "city"]
    if not all(key in ENV for key in required_keys):
        raise KeyError(f"Missing one of the following keys : {required_keys}")


def get_env(key: str, default=None):
    return ENV.get(key, default)


# Cache Functions
def load_cache():
    global CONCERT_CACHE
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as cache:
            CONCERT_CACHE = {line.strip() for line in cache}


def update_cache():
    with open(CACHE_FILE, "w") as cache:
        if CONCERT_CACHE:
            cache.write("\n".join(CONCERT_CACHE))


def cache_hit(concert: str) -> bool:
    return concert in CONCERT_CACHE


def add_to_cache(concert: str):
    CONCERT_CACHE.add(concert)
    update_cache()


def del_from_cache(concert: str):
    CONCERT_CACHE.discard(concert)
    update_cache()


# Songkick Functions
def get_artist_url(artist: str) -> str | None:
    query = requests.utils.quote(artist)
    soup = BeautifulSoup(
        get_page(f"{BASE_URL}/search?query={query}&type=artists"), "html.parser"
    )
    artist_tag = soup.select_one("li.artist a")
    return f"{BASE_URL}{artist_tag['href']}" if artist_tag else None


def parse_month(month: str) -> str:
    months = {
        "Jan": "01", "Feb": "02", "Mar": "03",
        "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09",
        "Oct": "10", "Nov": "11", "Dec": "12",
    }
    return months.get(month, "00")


def fetch_concerts():
    today = datetime.today()
    my_location = get_env("city")

    for artist in get_env("artists", []):
        artist_url = get_artist_url(artist)
        if not artist_url:
            print(f"No result for {artist}")
            continue

        print(f"[{artist}] Fetching concerts from {artist_url}/calendar")
        soup = BeautifulSoup(get_page(f"{artist_url}/calendar"), "html.parser")
        event_listings = soup.select("li.event-listing")

        if not event_listings:
            print(f"[{artist}] No concerts found.")
            continue

        new_concerts = 0

        for concert in event_listings:
            location = concert.select_one(".primary-detail").get_text(strip=True)
            if not any(
                country.lower() in location.lower()
                for country in get_env("countries", [])
            ):
                continue

            concert_day = f"{int(concert.select_one('.date').get_text(strip=True)):02d}"
            concert_month = parse_month(
                concert.select_one(".month").get_text(strip=True)
            )
            concert_year = int(today.strftime("%Y"))

            if concert.select_one('.year'): # If True, it's not current year, might be previous for past concerts or next year for future concert
                concert_year = int(concert.select_one('.year').get_text(strip=True))
                if int(today.strftime("%Y")) > concert_year:
                    continue # Past concert

            event = concert.select_one(".secondary-detail").get_text(strip=True)
            concert_link = f"{BASE_URL}{concert.find('a')['href']}"

            is_outdoor = bool(
                concert.select_one(".outdoor") or "festival" in event.lower()
            )
            concert_id = f"{artist.replace(' ', '').lower()}{concert_day}{concert_month}{location.split(',')[0].replace(' ', '').lower()}"

            if cache_hit(concert_id):
                if concert.select_one(".canceled"):
                    notify(
                        f"❌ *{artist.upper()}* ❌\n**CANCELED** {concert_day}/{concert_month}/{concert_year}: {'🏕️' if is_outdoor else '🏟️'} [{event}]({concert_link}) ({location})"
                    )
                    del_from_cache(concert_id)
                continue

            if int(today.strftime("%m")) < int(concert_month) or (
                int(today.strftime("%m")) == int(concert_month)
                and int(today.strftime("%d")) < int(concert_day)
            ):
                notify(
                    f"*{artist.upper()}* {'🏠' if my_location in location else ''}\n{concert_day}/{concert_month}/{concert_year}: {'🏕️' if is_outdoor else '🏟️'} [{event}]({concert_link}) ({location})"
                )
                add_to_cache(concert_id)
                new_concerts += 1

        print(f"[{artist}] {len(event_listings)} concerts found, {new_concerts} new.")
        time.sleep(4)


if __name__ == "__main__":
    load_env()
    load_cache()
    fetch_concerts()
