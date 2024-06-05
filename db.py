from flask import g
from datetime import datetime, timedelta
import sqlite3

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
    current_date = datetime.now()# + timedelta(days=10)
    db = get_db(db_file)
    match_date = db.execute("SELECT date FROM matches WHERE id = ?", (match_id,)).fetchone()
    if datetime.strptime(match_date[0], '%Y-%m-%dT%H:%M:%S') > current_date:
        db.execute(f"UPDATE bets SET {team}_goals = ? WHERE match_id = ? and user_id = ?", (goals, match_id, user_id))
        db.commit()
        return True
    return False