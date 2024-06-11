from flask import g
from datetime import datetime, timedelta
import sqlite3

country_dict = {
    "Noch Offen": "xx",
    "noch offen": "xx",
    "TBD": "xx",
    "Albanien": "al",
    "Belgien": "be",
    "Deutschland": "de",
    "Dänemark": "dk",
    "England": "gb-eng",
    "Frankreich": "fr",
    "Georgien": "ge",
    "Italien": "it",
    "Kroatien": "hr",
    "Niederlande": "nl",
    "Polen": "pl",
    "Portugal": "pt",
    "Rumänien": "ro",
    "Schottland": "gb-sct",
    "Schweiz": "ch",
    "Serbien": "rs",
    "Slowakei": "sk",
    "Slowenien": "si",
    "Spanien": "es",
    "Tschechien": "cz",
    "Türkei": "tr",
    "Ukraine": "ua",
    "Ungarn": "hu",
    "Österreich": "at"
}

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

def update_bet_in_db(db_file, match_id, team, goals, user_id):
    current_date = datetime.now() + timedelta(days=-360)
    db = get_db(db_file)
    match_date = db.execute("SELECT date FROM matches WHERE id = ?", (match_id,)).fetchone()
    if datetime.strptime(match_date[0], '%Y-%m-%dT%H:%M:%S') > current_date:
        db.execute(f"UPDATE bets SET {team}_goals = ? WHERE match_id = ? and user_id = ?", (goals, match_id, user_id))
        db.commit()
        return True
    return False


def update_bet_score(db_file, bet_id):
    db = get_db(db_file)
    bet = db.execute("SELECT match_id, team1_goals, team2_goals FROM bets WHERE id = ?", (bet_id,)).fetchone()
    match_id = bet[0]
    match_result = db.execute("SELECT result FROM matches WHERE id = ?", (match_id,)).fetchone()[0]
    bet_score = evaluate_bet_score(bet[1], bet[2], match_result)
    db.execute("UPDATE bets SET bet_score = ? WHERE id = ?", (bet_score, bet_id))
    db.commit()

def update_user_score(db_file, user_id):
    return None

# This could be somewhere else but not sure if it makes sense to create a py file just for one function.
def evaluate_bet_score(team1_goal, team2_goal, match_result):
    ON_POINT = 3
    GOAL_DIFF = 2
    CORRECT_TEAM = 1
    WRONG = 0

    # We split a result like 3:1 into a list ["3", "1"].
    m_result = match_result.split(":")

    t1_goal = int(team1_goal)
    t2_goal = int(team2_goal)
    r1_goal = int(m_result[0])
    r2_goal = int(m_result[1])
    
    # User betted on the correct team and the exact goal number.
    if (t1_goal == r1_goal) and (t2_goal == r2_goal):
        return ON_POINT
    # User betted on the correct team and the correct goal difference.
    elif (t1_goal - t2_goal) == (r1_goal - r2_goal):
        return GOAL_DIFF
    # User betted on the correct team.
    elif (t1_goal - t2_goal < 0) and (r1_goal - r2_goal < 0):
        return CORRECT_TEAM
    elif (t1_goal - t2_goal == 0) and (r1_goal - r2_goal == 0):
        return CORRECT_TEAM
    elif (t1_goal - t2_goal > 0) and (r1_goal - r2_goal > 0):
        return CORRECT_TEAM
    # Users did not bet on the correct team.
    else:
        return WRONG
    