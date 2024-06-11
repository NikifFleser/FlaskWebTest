from requests import get as get_from
from db import get_db
from datetime import datetime, timedelta

def get_games(matchday="1", season="2023", tournament="bl1"):
    url = f"https://api.openligadb.de/getmatchdata/{tournament}/{season}/{matchday}"
    response = get_from(url)
    data = response.json()

    games = []

    for raw_game in data:
        game = dict()

        game["date"] = raw_game["matchDateTime"]
        game["team1"] = raw_game['team1']['teamName']
        game["team2"] = raw_game['team2']['teamName']
        game["location"] = "none"#raw_game["location"]["locationCity"]
        game["matchday"] = matchday

        result = raw_game["matchResults"]
        try:
            g1 = result[1]['pointsTeam1']
            g2 = result[1]['pointsTeam2']
            game["result"] = f"{g1}:{g2}"
        except(IndexError):
            game["result"] = None
        games.append(game)

    return games

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

def initial_fill_db(db_file):
    db = get_db(db_file)
    for matchday in range(1, 8):
        games = get_games(matchday)
        for game in games:
            db.execute(
                'INSERT INTO matches (team1, team2, matchday, date, location, result) VALUES (?,?,?,?,?,?)',
                (game["team1"], game["team2"], matchday, game["date"], game["location"], game["result"]))
    db.commit()

def update_db(db_file):
    pass