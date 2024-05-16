from flask import Flask, g
import sqlite3

def init_db(app, db_file):
    with app.app_context():
        db = get_db(db_file)
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db(db_file):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(db_file)
    return db
