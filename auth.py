from flask import Blueprint, session, request, current_app
from flask import redirect, url_for, render_template, flash
from db import get_db
from functools import wraps
import random

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db(current_app.config["DATABASE"])
        if not username:
            error = "Please enter a username."
        elif not password:
            error = "Please enter a password."
        else:
            user_id = db.execute('SELECT id FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
            if user_id:
                session['username'] = username
                session["user_id"] = user_id[0]
                next_url = request.args.get("next_url")
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for('index'))
            else:
                error = "Username or password incorrect."
    return render_template("login.html", error=error)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # return redirect(url_for("index"))
    if request.method == 'GET':
        return render_template("signup.html", error=None)
    
    default_score = 0 # random.randint(0, 10)

    # request.method is 'POST'
    error = None
    username = request.form.get('username')
    password = request.form.get('password')
    db = get_db(current_app.config["DATABASE"])
    # failchecks
    if not username:
        error = "Please enter a username."
    elif not password:
        error = "Please enter a password."
    elif db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone() is not None:
        error = "Username unavailable."
    else: 
        # create a new user
        db.execute('INSERT INTO users (username, password, score) VALUES (?, ?, ?)', (username, password, default_score))
        db.commit()
        # update session
        user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        session["username"] = username
        session["user_id"] = user[0]
        # create the empty bets for the new user
        games = db.execute("SELECT id FROM matches").fetchall()
        for game in games:
            db.execute("INSERT INTO bets (user_id, match_id, bet_score) VALUES (?, ?, ?)", (user[0], game[0], 0))
        db.commit()
    if error:
        return render_template("signup.html", error=error)
    else:
        return redirect(url_for('index'))
    

def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        in_session = "username" in session
        if not in_session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        in_session = "username" in session
        if not in_session:
            return redirect(url_for("index"))
        elif session["username"] != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
