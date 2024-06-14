from flask import g, has_request_context
from datetime import datetime, timedelta
import sqlite3
from api import get_games, get_current_matchday, DAYS
from numpy import sign

matchday_list = ["Gruppenphase Spieltag 1",
                 "Gruppenphase Spieltag 2",
                 "Gruppenphase Spieltag 3",
                 "Achtelfinale",
                 "Viertelfinale",
                 "Halbfinale",
                 "Finale"]

country_dict = {
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

def column_exists(db_file, table_name, column_name):
    db = get_db(db_file)
    infos = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    columns = [info[1] for info in infos]
    return column_name in columns

def check_table_empty(db_file, table_name):
    db = get_db(db_file)
    row_count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return row_count <= 0

def init_db(app, db_file):
    with app.app_context():
        db = get_db(db_file)
        with app.open_resource('schema.sql', mode='r') as f:
            script = f.read()
            cursor = db.cursor()
            cursor.executescript(script)
        db.commit()
    update_matches(db_file)
    update_current(db_file)

def update_current(db_file):
    db = get_db(db_file)
    if check_table_empty(db_file, "current"):
        db.execute('INSERT INTO current (id) VALUES (?)', (1,))
    db.commit()

def update_matches(db_file):
    db = get_db(db_file)
    if check_table_empty(db_file, "matches"):
        for matchday in range(1, 8):
            games = get_games(matchday)
            for game in games:
                db.execute(
                    'INSERT INTO matches (team1, team2, matchday, date, location, ref, result) VALUES (?,?,?,?,?,?,?)',
                    (game["team1"], game["team2"], matchday, game["date"], game["location"], game["id"], game["result"]))
    else:
        matchday = get_current_matchday()
        games = get_games(matchday)
        for game in games:
            db.execute("UPDATE matches SET result = ? WHERE matchday = ? AND team1 = ?",
                        (game["result"], matchday, game["team1"]))
    db.commit()
        
def get_db(db_file):
    if has_request_context():
        db = getattr(g, 'database', None)
        if db is None:
            db = sqlite3.connect(db_file)
            g.database = db
        return db
    else:
        return sqlite3.connect(db_file)

def update_bet_in_db(db_file, match_id, team, goals, user_id):
    current_date = datetime.now() + timedelta(days=DAYS)
    db = get_db(db_file)
    match_date = db.execute("SELECT date FROM matches WHERE id = ?", (match_id,)).fetchone()
    if datetime.strptime(match_date[0], '%Y-%m-%dT%H:%M:%S') > current_date:
        db.execute(f"UPDATE bets SET {team}_goals = ? WHERE match_id = ? and user_id = ?", (goals, match_id, user_id))
        db.commit()
        return True
    return False

# We update all bets for one specific match which is given by a match_id.
def update_bet_scores(db_file, match_id):
    db = get_db(db_file)
    bet_table = db.execute("SELECT id, team1_goals, team2_goals FROM bets WHERE match_id = ?", (match_id,)).fetchall()
    for bet in bet_table:
        bet_id = bet[0]
        match_result = db.execute("SELECT result FROM matches WHERE id = ?", (match_id,)).fetchone()[0]
        bet_score = evaluate_bet_score(bet[1], bet[2], match_result)
        db.execute("UPDATE bets SET bet_score = ? WHERE id = ?", (bet_score, bet_id))
    # Either commit after ever execution or once after multiple executions.
    db.commit()

# def update_results(db_file):
#     db = get_db(db_file)
#     current_game_id = db.execute("SELECT id FROM current").fetchone()[0]
#     while current_game_id < 51:
#         matchday = db.execute(f"SELECT matchday FROM matches WHERE id={current_game_id}").fetchone()[0]


def update_user_scores(db_file):
    db = get_db(db_file)
    user_scores = db.execute("SELECT user_id, SUM(bet_score) FROM bets GROUP BY user_id").fetchall()
    for user in user_scores:
        user_id = user[0]
        score = user[1]
        db.execute("UPDATE users SET score = ? WHERE id = ?", (score, user_id))
    db.commit()
    
# This could be somewhere else but not sure if it makes sense to create a py file just for one function.
def evaluate_bet_score(team1_goal, team2_goal, match_result):
    ON_POINT = 4
    GOAL_DIFF = 3
    CORRECT_TEAM = 2
    WRONG = 0

    # We check if the user has even set a bet. If not, return 0 points.
    if (team1_goal == None) or (team2_goal == None):
        return WRONG

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
    elif sign(t1_goal - t2_goal) == sign(r1_goal - r2_goal):
        return CORRECT_TEAM
    # Users did not bet on the correct team.
    else:
        return WRONG
    