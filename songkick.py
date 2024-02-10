import requests
from bs4 import BeautifulSoup
from time import sleep
from os import path
from datetime import datetime
from re import search


BASE_URL = "https://www.songkick.com"
ENV = {}
CONCERT_CACHE = set()

############################################## UTILS
##### HTTP
def get_random_UA() -> str:
    from random import choice
    
    return choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) obsidian/1.4.16 Chrome/114.0.5735.289 Electron/25.8.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Cypress/13.6.3 Chrome/114.0.5735.289 Electron/25.8.4 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) obsidian/1.5.3 Chrome/114.0.5735.289 Electron/25.8.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) obsidian/1.4.14 Chrome/114.0.5735.289 Electron/25.8.1 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.6; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    ])

def get_domain(url: str) -> str:
    from re import search
    m = search('https?://([A-Za-z_0-9.-]+).*', url)
    if m:
        return m.group(1)
    return ""

def get_page(url: str):
    _domain = get_domain(url)    
    resp = requests.get(url, headers = {'User-Agent': get_random_UA()})
    if resp.status_code == 200:
        return resp.text

    else:
        return None

##### CACHE
def add_to_cache(concert: str):
    CONCERT_CACHE.add(concert)

def del_from_cache(concert: str):
    CONCERT_CACHE.discard(concert)

def update_cache():
    CACHE = CONCERT_CACHE  # Python raises UnboundLocalError if I use CONCERT_CACHE directly at line 77...
    if not CACHE:
        with open('./.concerts.cache', 'r') as cache:
            CACHE = {line.strip() for line in cache.readlines()}

    with open('./.concerts.cache', 'w') as cache:
        today = datetime.today()
        day = today.strftime("%d")
        month = today.strftime("%m")
        pattern = r"([0-9]{4})[a-zA-Z]"

        for concert in CACHE:
            concert_match = search(pattern, concert)

            if concert_match:
                concert_date = concert_match[1]

                if int(month) < int(concert_date[-2:]):
                    cache.write(f"{concert}\n")
                    continue

                if int(month) == int(concert_date[-2:]) and int(day) < int(concert_date[:2]):
                    cache.write(f"{concert}\n")

def cache_hit(concert: str) -> bool:
    if CONCERT_CACHE:
        return concert in CONCERT_CACHE

    else:
        if path.isfile('.concerts.cache'):
            with open('.concerts.cache', 'r') as cache:
                concert_is_cached = False
                for line in cache.readlines():
                    line = line.strip()
                    CONCERT_CACHE.add(line)
                    if concert in line:
                        concert_is_cached = True

                return concert_is_cached
        return False

##### YAML ENV
def parse_env():
    import yaml

    if path.isfile('./env.yaml'):
        with open('./env.yaml', 'r') as fenv:
            try:
                fdata = yaml.safe_load(fenv)

                keys = ['telegram', 'artists', 'countries']
                if all(key in fdata for key in keys):
                    ENV = fdata
                    return fdata
                else:
                    raise ValueError(f'Missing one of the following keys : {keys}')
                    
            except (yaml.YAMLError, ValueError) as exc:
                print(exc)
    
    exit(1)

def get_env_artists() -> list[str]:
    if ENV:
        return ENV.get('artists')

    return parse_env().get('artists')

def get_env_telegram() -> dict:
    if ENV:
        return ENV.get('telegram')

    return parse_env().get('telegram')

def get_env_countries() -> dict:
    if ENV:
        return ENV.get('countries')

    return parse_env().get('countries')

##### TELEGRAM
def telegram_command(method, data):
    url = f"https://api.telegram.org/bot{get_env_telegram().get('token')}/{method}"
    return requests.post(url=url, json=data)

def telegram_sendMessage(text: str):
    return telegram_command('sendMessage', {
        'text': text,
        'chat_id': get_env_telegram().get('chatID'),
        'parse_mode': 'markdown',
        'disable_web_page_preview': True
    })

##### SONGKICK
def retrieve_artist_url(artist) -> str:
    soup = BeautifulSoup(get_page(f"https://www.songkick.com/search?query={requests.utils.quote(artist)}&type=artists"), features = 'html.parser')

    try:
        return BASE_URL + soup.find('li', attrs = {'class': 'artist'}).find('a')['href']  # The first li, as the most popular artist in search page is first
    except:
        print(f'No result for {artist}')
        return None

def reverse_month_to_date(month) -> int:
    match month:
        case "Jan":
            return f"{1:02d}"
        case "Feb":
            return f"{2:02d}"
        case "Mar":
            return f"{3:02d}"
        case "Apr":
            return f"{4:02d}"
        case "May":
            return f"{5:02d}"
        case "Jun":
            return f"{6:02d}"
        case "Jul":
            return f"{7:02d}"
        case "Aug":
            return f"{8:02d}"
        case "Sep":
            return f"{9:02d}"
        case "Oct":
            return 10
        case "Nov":
            return 11
        case "Dec":
            return 12
    return -1
############################################## UTILS END


def run():
    for artist in get_env_artists():
        artist = artist.lower()
        artist_url = retrieve_artist_url(artist)
        if artist_url:
            print(f'[{artist}] Retrieving concerts ({artist_url})')

            try:
                artist_calendar_url = f"{artist_url}/calendar"
                soup = BeautifulSoup(get_page(artist_calendar_url), features = 'html.parser')

                if soup:  # TODO: Optimize
                    soup = soup.find('div', attrs={'id': 'calendar-summary'})

                    if soup:
                        total_cnt = 0
                        new_concert_cnt = 0
                        if soup.find('li', attrs = {'class': 'event-listing'}):
                            for concert in soup.find_all('li', attrs = {'class': 'event-listing'}):
                                is_outdoor = False

                                link = concert.find('a').get('href', None)
                                day = f"{int(concert.select_one('.date').getText().strip()):02d}"
                                month = reverse_month_to_date(concert.select_one('.month').getText().strip())
                                location = concert.select_one('.primary-detail').getText().strip()
                                event = concert.select_one('.secondary-detail').getText().strip()
                                details = f"{artist.replace(' ', '')}{day}{month}{location.split(',')[0].replace(' ', '')}".lower()
                                    
                                if any(country in location.lower() for country in get_env_countries()):  # Verify concert is in one of the specified location
                                    total_cnt += 1
                                    if 'festival' in event.lower():  # Festival is likely outdoor
                                        is_outdoor = True

                                    if concert.select_one('.outdoor'):
                                        is_outdoor = True
                                    concert_in_cache = cache_hit(details)

                                    if concert_in_cache:  # Verify if concert cached (previously active)
                                        if concert.select_one('.canceled'):  # Verify if canceled, if so notify and delete
                                            telegram_sendMessage(f"❌ *{artist.upper()}* ❌\n**CANCELED** {day}/{month}: {'🏕️' if is_outdoor else '🏟️'} [{event}]({BASE_URL}{link}) ({location})")  # notify cancel
                                            del_from_cache(details)

                                        continue #Already cached || duplicate || canceled and notified

                                    new_concert_cnt += 1 
                                    telegram_sendMessage(f"*{artist.upper()}*\n{day}/{month}: {'🏕️' if is_outdoor else '🏟️'} [{event}]({BASE_URL}{link}) ({location})")
                                    add_to_cache(details)

                        if total_cnt:
                            print(f"[{artist}] {total_cnt} concert{'s' if total_cnt > 1 else ''} found.", end=' ')
                            if new_concert_cnt:
                                print(f"{new_concert_cnt} new concert{'s' if new_concert_cnt > 1 else ''}.")
                            else:
                                print("No new concert.")
                        else:
                            print(f"[{artist}] No concert in selected countries.")

                    else:
                        print(f"[{artist}] No concert found.")

            except Exception as e:
                print(f'Error exception for {artist}: {e}')
                telegram_sendMessage(f'[ERROR] Artist `{artist}`: {e}.')

            sleep(1)  # Let's not spam songkick for this

    update_cache()


if __name__ == "__main__":
    run()