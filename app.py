from flask import Flask, request, session, g
from flask import render_template, redirect, url_for, jsonify
from flask_wtf.csrf import CSRFProtect
from db import init_db, get_db
from auth import auth_bp, requires_admin, requires_login
from requests import get as get_from
from api import initial_fill_db, get_current_matchday


app = Flask(__name__)
app.secret_key = 'dev'
csrf = CSRFProtect(app) # i have no idea what this does but we need it
csrf.exempt(auth_bp)

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

@app.route("/bet_route")
@requires_login
def bet_route():
    matchday = get_current_matchday()
    return redirect(url_for('bet', matchday=matchday))

@app.route("/bet/<int:matchday>")
@requires_login
def bet(matchday):
    username = session.get("username")
    if username == "admin":
        return redirect(url_for("auth.logout"))
    db = get_db(DATABASE)
    match_tuples = db.execute("SELECT * FROM matches WHERE matchday = ?",(matchday,)).fetchall()
    matches = []
    for match in match_tuples:
        m_id = match[0]
        bet = db.execute("SELECT team1_goals, team2_goals FROM bets WHERE user_id = ? and match_id = ?", (session["user_id"], m_id)).fetchone()
        matches.append((m_id, match[1], match[2], bet[0], bet[1]))

    return render_template("bet.html", matches=matches, username=username, matchday=matchday)

@app.route('/update_bet', methods=['POST'])
def update_bet():
    data = request.get_json()
    match_id = data.get('match_id')
    team = data.get('team')
    goals = data.get('goals')
    user_id = session["user_id"]
    update_bet_in_db(match_id, team, goals, user_id)
    return jsonify({'status': 'success', 'match_id': match_id, 'team': team, 'goals': goals})

def update_bet_in_db(match_id, team, goals, user_id):
    db = get_db(DATABASE)
    db.execute(f"UPDATE bets SET {team}_goals = ? WHERE match_id = ? and user_id = ?", (goals, match_id, user_id))
    db.commit()

# Close the database connection at ?request? end
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)#, host="0.0.0.0")
