from requests import get as get_from
from datetime import datetime, timedelta
from pytz import timezone


def get_datetime():
    DAYS = 0
    HOURS = 0

    berlin_timezone = timezone('Europe/Berlin')
    berlin_aware = datetime.now(berlin_timezone) + timedelta(days=DAYS, hours=HOURS)
    berlin_naive = berlin_aware.replace(tzinfo=None)

    return berlin_naive


def get_game(game_api_id):
    "returns a match-dict from a game_id (ref)"
    url = f"https://api.openligadb.de/getmatchdata/{game_api_id}"
    response = get_from(url)
    data = response.json()
    return data

def get_games(matchday="1", season="2024", tournament="em"):
    """returns a list of match-dicts with the following keys:
    date, team1, team2, location, matchday, result"""
    #https://api.openligadb.de/getmatchdata/em/2024/1
    url = f"https://api.openligadb.de/getmatchdata/{tournament}/{season}/{matchday}"
    response = get_from(url)
    data = response.json()
    games = []
    for raw_game in data:
        games.append(raw_game)
    return games

def game_get_result(game):
    """returns None or 'x:y'"""
    res = game["matchResults"]
    if res == [] or res is None:
        return None
    g1 = res[1]["pointsTeam1"]
    g2 = res[1]["pointsTeam2"]
    return f"{g1}:{g2}"

def game_get_date(game):
    date = game["matchDateTime"]
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

def game_get_db_id(game):
    id = game["matchID"]
    return id - 69340

def game_get_online_id(game_id):
    return game_id + 69340

def format_datetime(game):
    datetime_str = game["matchDateTime"]
    dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    now = get_datetime()
    en_to_de = {"Mon": "Mo",
                "Tue": "Di",
                "Wed": "Mi",
                "Thu": "Do",
                "Fri": "Fr",
                "Sat": "Sa",
                "Sun": "So"}

    if dt < now:
        if game["matchIsFinished"]:
            return "Endstand"
        return "- Live -"
    elif dt.date() == now.date():
        return dt.strftime('%H:%M Uhr')
    else:
        day = dt.strftime('%a')
        date = dt.strftime('%d.%m')
        return f"{en_to_de[day]}. {date}"

def get_current_matchday():
    current_date = datetime.now()
    for matchday in range(1, 8):
        matches = get_games(matchday)
        for match in matches:
            match_date = datetime.strptime(match['matchDateTime'], '%Y-%m-%dT%H:%M:%S')
            if match_date >= current_date:
                return matchday
    # If all matches have passed, return the last matchday
    return 7
