from flask import g
import sqlite3
from requests import get as get_from

def init_db(app, db_file):
    with app.app_context():
        db = get_db(db_file)
        with app.open_resource('schema.sql', mode='r') as f:
            script = f.read()
            cursor = db.cursor()
            cursor.executescript(script)
        db.commit()

def get_db(db_file):
    db = getattr(g, 'database', None)
    if db is None:
        db  = sqlite3.connect(db_file)
        g.database = db
    return db

def update_db(db_file):
    db = get_db(db_file)
    season = 2023
    matchday = 1
    url = f"https://api.openligadb.de/getmatchdata/bl1/{season}/{matchday}"
    response = get_from(url)
    data = response.json()

    for game in data:
        date = game["matchDateTime"]
        team1 = game['team1']['teamName']
        team2 = game['team2']['teamName']

        result = game["matchResults"][1]
        team1_goals = result["pointsTeam1"]
        team2_goals = result["pointsTeam2"]
        endresult = f"{team1_goals}:{team2_goals}"
        print(endresult)

        db.execute('INSERT INTO match (team1, team2, matchday, result, date) VALUES (?, ?, ?, ?, ?)', (team1, team2, matchday, endresult, date))
        db.commit()



        