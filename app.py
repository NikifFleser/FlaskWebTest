from flask import Flask, request, session, g
from flask import render_template, redirect, url_for, jsonify
from flask_wtf.csrf import CSRFProtect
from db import country_dict, matchday_list, update_match_result
from db import init_db, get_db, update_bet_in_db
from auth import auth_bp, requires_admin, requires_login
from api import get_current_matchday, get_game, get_datetime, format_datetime
from datetime import datetime

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
    current_date = get_datetime()
    dct = country_dict
    username = session.get("username")
    matchday_alias = matchday_list[matchday-1]
    db = get_db(DATABASE)
    matches_db = db.execute("SELECT id, team1, team2, date, result, ref FROM matches WHERE matchday = ?",(matchday,)).fetchall()
    matches = []
    
    for m in matches_db:
        
        m_id, m_t1, m_t2, m_date, m_result, m_ref = m[0], m[1], m[2], m[3], m[4], m[5]
        m_date = datetime.strptime(m_date, "%Y-%m-%dT%H:%M:%S")
        bet = db.execute("SELECT team1_goals, team2_goals, bet_score FROM bets WHERE user_id = ? and match_id = ?", (session["user_id"], m_id)).fetchone()
        b_g1, b_g2, b_score = bet[0], bet[1], bet[2]
        #assign flag tags
        flag_t1, flag_t2 = "xx", "xx"
        if m_t1 in dct:
            flag_t1 = dct[m_t1]
        if m_t2 in dct:
            flag_t2 = dct[m_t2]
        #disable if game started
        disable = False 
        if m_date < current_date:
            disable = True

        api = get_game(m_ref)
        finished = api["matchIsFinished"]
        if api["matchResults"] is None or api["matchResults"] == []:
            result = "-:-"
        else:
            l1 = api["matchResults"][1]
            l2 = api["matchResults"][1]
            r1 = l1["pointsTeam1"]
            r2 = l2["pointsTeam2"]
            result = f"{r1}:{r2}"
        if result != m_result and result != "-:-":
            update_match_result(DATABASE, m_id, result) #update the match and related bets
        live = format_datetime(api)

        matches.append((m_id, flag_t1, flag_t2, #0,1,2
                         b_g1, b_g2, disable, m_t1, m_t2, #3,4,5,6,7
                         live, result, b_score)) #8,9,10
        
    return render_template("bet.html", matches=matches, username=username, matchday=matchday, matchday_alias=matchday_alias)

@app.route('/update_bet', methods=['POST'])
def update_bet():
    """updates puts the form inputs into the database
    called on change from js"""
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
    username = session.get("username")
    db = get_db(DATABASE)
    users = db.execute("SELECT username, score FROM users ORDER BY score DESC").fetchall()
    return render_template("leaderboard.html", users=users, username=username)

# Close the database connection at ?request? end
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
