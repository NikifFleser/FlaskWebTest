from flask import Flask, request, session, g
from flask import render_template, redirect, url_for
from db import init_db, get_db
from auth import auth_bp, requires_admin, requires_login
from requests import get as get_from
from api import initial_fill_db


app = Flask(__name__)
app.secret_key = 'dev'

app.register_blueprint(auth_bp)

DATABASE = 'data.db'
app.config['DATABASE'] = DATABASE
init_db(app, DATABASE)

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/about')
def about():
    username = session.get('username')
    return render_template('about.html', username=username)

@requires_admin
@app.route('/admin')
def admin():
    #initial_fill_db(DATABASE)
    return redirect(url_for("index"))

@requires_login
@app.route("/bet")
def bet():
    username = session.get('username')
    matchday = 1
    db = get_db(DATABASE)
    matches = db.execute('SELECT * FROM matches WHERE matchday = ?',
                            (matchday,)).fetchall()

    return render_template("bet.html", matches=matches, username=username)


# Close the database connection at ?request? end
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)#, host="0.0.0.0")
