from requests import get as get_from
from datetime import datetime, timedelta

def get_games(matchday="1", season="2024", tournament="em"):
    """returns a list of match-dicts with the following keys:
    date, team1, team2, location, matchday, result"""

    url = f"https://api.openligadb.de/getmatchdata/{tournament}/{season}/{matchday}"
    response = get_from(url)
    data = response.json()

    games = []

    for raw_game in data:
        game = dict()

        game["live"] = format_datetime(raw_game)
        game["date"] = raw_game["matchDateTime"]
        game["team1"] = raw_game['team1']['teamName']
        game["team2"] = raw_game['team2']['teamName']
        game["location"] = "none"#raw_game["location"]["locationCity"]
        game["matchday"] = matchday
        game["finished"] = raw_game["matchIsFinished"]

        result = raw_game["matchResults"]
        try:
            g1 = result[1]['pointsTeam1']
            g2 = result[1]['pointsTeam2']
            game["result"] = f"{g1}:{g2}"
        except(IndexError):
            game["result"] = None
        games.append(game)

    return games

def format_datetime(game):
    datetime_str = game["matchDateTime"]
    dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    now = datetime.now()
    en_to_de = {"Mon": "Mo",
                "Tue": "Di",
                "Wed": "Mi",
                "Thu": "Do",
                "Fri": "Fr",
                "Sat": "Sa",
                "Sun": "So"}

    if dt < now:
        if game["matchIsFinished"]:
            return "beendet"
        return "- live -"
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
            match_date = datetime.strptime(match['date'], '%Y-%m-%dT%H:%M:%S')
            if match_date >= current_date:
                return matchday
    # If all matches have passed, return the last matchday
    return 7

def update_db(db_file):
    pass