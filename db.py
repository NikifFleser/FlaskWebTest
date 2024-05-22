from flask import g
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
