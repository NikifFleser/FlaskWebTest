from flask import Flask, request, session, g
from flask import render_template, redirect, url_for, jsonify
from flask_wtf.csrf import CSRFProtect
from db import init_db, get_db, update_bet_in_db, country_dict, column_exists, update_bet_scores, update_user_scores
from auth import auth_bp, requires_admin, requires_login
from requests import get as get_from
from api import get_current_matchday, get_games, DAYS
from datetime import datetime, timedelta

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
    dct = country_dict
    username = session.get("username")
    db = get_db(DATABASE)
    match_db = db.execute("SELECT id, team1, team2, date FROM matches WHERE matchday = ?",(matchday,)).fetchall()
    match_api = get_games(matchday)
    matches = []
    current_date = datetime.now() + timedelta(days=DAYS)
    match_nr = 0
    for match in match_db:
        flag_t1, flag_t2 = "xx", "xx"
        m_id = match[0]
        m_date = datetime.strptime(match[3], "%Y-%m-%dT%H:%M:%S")
        bet = db.execute("SELECT team1_goals, team2_goals, bet_score FROM bets WHERE user_id = ? and match_id = ?", (session["user_id"], m_id)).fetchone()
        if match[1] in dct:
            flag_t1 = dct[match[1]]
        if match[2] in dct:
            flag_t2 = dct[match[2]]
            
        if m_date < current_date:
            disable = True
        else:
            disable = False

        live = match_api[match_nr]["live"]
        scoreline = match_api[match_nr]["result"]
        if scoreline == None:
            scoreline = "-:-"
        if live != "Endstand" and live != "- Live -":
            userpoints = "-"
        else:
            userpoints = bet[2] #get_bet_points(result="2:1", bet="1:0")->3 for example 

        matches.append((m_id, flag_t1, flag_t2, #0,1,2
                         bet[0], bet[1], disable, match[1], match[2], #3,4,5,6,7
                         live, scoreline, userpoints)) #8,9,10
        match_nr += 1
        
    return render_template("bet.html", matches=matches, username=username, matchday=matchday)

@app.route('/update_bet', methods=['POST'])
def update_bet():
    data = request.get_json()
    match_id = data.get('match_id')
    team = data.get('team')
    goals = data.get('goals')
    user_id = session["user_id"]
    if update_bet_in_db(DATABASE, match_id, team, goals, user_id):
        return jsonify({'status': 'success', 'match_id': match_id, 'team': team, 'goals': goals})
    return jsonify({'status': 'failure'})

@app.route("/leaderboard")
def leaderboard():
    # We update the leaderboard whenever someone checks the leaderboard.
    update_user_scores(DATABASE)
    username = session.get("username")
    db = get_db(DATABASE)
    users = db.execute("SELECT username, score FROM users ORDER BY score DESC").fetchall()
    return render_template("leaderboard.html", users=users, username=username)

@app.route("/update_bets/<int:match_id>")
def update_bets(match_id):
    # To test it, I am goona input dummy data
    dummy_result = "1:0"
    db = get_db(DATABASE)
    db.execute("UPDATE matches SET result = ? WHERE id = ?", (dummy_result, match_id))
    db.commit()
    update_bet_scores(DATABASE, match_id)
    return f"Updated bets for match {match_id}."


# Close the database connection at ?request? end
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
