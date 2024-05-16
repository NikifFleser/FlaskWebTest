from flask import Blueprint, session, request, current_app
from flask import redirect, url_for, render_template
from db import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        error = None
        username = request.form['username']
        password = request.form['password']
        db = get_db(current_app.config['DATABASE'])
        if not username:
            error = "please enter a username"
        elif not password:
            error = "please enter a password"
        elif db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone() == None:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            session["username"] = username
        else:
            error = "username unavailable"

        if error:
            return render_template("signup.html", error=error)
        else:
            return redirect(url_for('index'))
        
    return render_template("signup.html", error=None)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db(current_app.config["DATABASE"])
        if not username:
            error = "please enter a username"
        elif not password:
            error = "please enter a password"
        else:
            user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
            if user:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                error = "username or password incorrect"
    return render_template("login.html", error=error)