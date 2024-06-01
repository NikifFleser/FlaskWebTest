from flask import Blueprint, session, request, current_app
from flask import redirect, url_for, render_template, flash
from db import get_db

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
            user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
            if user:
                session['username'] = username
                next_url = request.args.get("next")
                print(next_url)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for('index'))
            else:
                error = "Username or password incorrect."
    return render_template("login.html", error=error)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        error = None
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db(current_app.config["DATABASE"])
        if not username:
            error = "Please enter a username."
        elif not password:
            error = "Please enter a password."
        elif db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone() is None:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            session["username"] = username
        else:
            error = "Username unavailable."

        if error:
            return render_template("signup.html", error=error)
        else:
            return redirect(url_for('index'))
    return render_template("signup.html", error=None)

def requires_login(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to be logged in to access this page.')
            login_url = url_for('auth.login', next=request.url)
            return redirect(login_url)
        return f(*args, **kwargs)
    return decorated_function

def requires_admin(f):
    def decorated_function(*args, **kwargs):
        if session["username"] != 'admin':
            flash('You do not have permission to access this page.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
