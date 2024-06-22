from flask import Flask, request, session, g
from flask import render_template, redirect, url_for, jsonify
from flask_wtf.csrf import CSRFProtect
from db import country_dict, matchday_list, update_match_result
from db import init_db, get_db, update_bet_in_db, update_user_scores
from auth import auth_bp, requires_admin, requires_login
from api import game_get_online_id, get_current_matchday, get_game, get_games, game_get_result, game_get_db_id, game_get_date, get_datetime, format_datetime
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
    username = session.get("username")
    matchday_alias = matchday_list[matchday-1]
    db = get_db(DATABASE)
    matches_api = get_games(matchday)
    matches = []
    for m in matches_api:
        m_t1, m_t2 = m["team1"]["teamName"], m["team2"]["teamName"]
        m_id, m_date, m_result = game_get_db_id(m), game_get_date(m), game_get_result(m)
        if m_result == None: m_result = "-:-"
        #bet = db.execute("SELECT team1_goals, team2_goals, bet_score FROM bets WHERE user_id = ? and match_id = ?", (session["user_id"], m_id)).fetchone()
        bet = db.execute("""SELECT b.team1_goals, b.team2_goals, b.bet_score, m.result
                          FROM bets b JOIN matches m ON b.match_id = m.id 
                          WHERE b.user_id = ? AND b.match_id = ?""",
                          (session["user_id"], m_id)).fetchone()
        b_g1, b_g2, b_score, old_result = bet[0], bet[1], bet[2], bet[3]
        #assign flag tags
        flag_t1, flag_t2 = "xx", "xx"
        if m_t1 in country_dict:
            flag_t1 = country_dict[m_t1]
        if m_t2 in country_dict:
            flag_t2 = country_dict[m_t2]
        #disable if game started
        disable = False 
        if m_date < current_date:
            disable = True

        live = format_datetime(m)
        if old_result != m_result and m_result != "-:-":
            update_match_result(DATABASE, m_id, m_result) #update the match and related bets
        

        matches.append((m_id, flag_t1, flag_t2, #0,1,2
                         b_g1, b_g2, disable, m_t1, m_t2, #3,4,5,6,7
                         live, m_result, b_score)) #8,9,10
        
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

@app.route("/leaderboard_route")
def leaderboard_route():
    matchday = get_current_matchday()
    return redirect(url_for('leaderboard', matchday=matchday))

@app.route("/leaderboard/<int:matchday>")
def leaderboard(matchday):
    username = session.get("username")
    matchday_alias = matchday_list[matchday-1]
    update_user_scores(DATABASE)
    db = get_db(DATABASE)
    users = db.execute("SELECT id, username, score FROM users ORDER BY score DESC").fetchall()
    matches = db.execute("SELECT id, team1, team2, result FROM matches WHERE matchday = ? ORDER BY id ASC", (matchday,)).fetchall()

    # This is going to be a bit messy...
    bet_data = []
    rank = 1
    for user in users:
        user_id = user[0]
        user_name = user[1]
        user_score = user[2]
        
        # If there is a more elegant way, I would love to hear about it!
        bets = db.execute("""SELECT b.team1_goals, b.team2_goals, b.bet_score, b.match_id, b.user_id FROM bets b 
                          JOIN matches as m ON b.match_id = m.id AND m.matchday = ? 
                          WHERE b.user_id = ? ORDER BY b.match_id ASC""", (matchday, user_id)).fetchall()
        user_bets = []  # Data is stored as (bet, score)
        for bet in bets:
            t1_goals = bet[0]
            t2_goals = bet[1]
            bet_score = bet[2]
            match_id = bet[3]
            b_user_id = bet[4]
            match_started = game_get_result(get_game(game_get_online_id(match_id))) == None

            if t1_goals == None or t2_goals == None:
                user_bet = "-:-"
            elif not match_started:
                if b_user_id == user_id:
                    user_bet = f"{t1_goals}:{t2_goals}"
                else:
                    user_bet = "-:-"
            else:
                user_bet = f"{t1_goals}:{t2_goals}"
            data = (user_bet, bet_score)
            user_bets.append(data)
        bet_data.append((rank, user_name, user_score, user_bets))
        rank += 1
    
    # Lets finish up the matchdata as well
    match_data = []
    for match in matches:
        m_t1, m_t2, result = match[1], match[2], match[3]
        #assign flag tags
        flag_t1, flag_t2 = "xx", "xx"
        if m_t1 in country_dict:
            flag_t1 = country_dict[m_t1]
        if m_t2 in country_dict:
            flag_t2 = country_dict[m_t2]
        match_data.append((flag_t1, flag_t2, result))
    return render_template("leaderboard.html", bet_data=bet_data, match_data=match_data, username=username, matchday=matchday, matchday_alias=matchday_alias)

# Close the database connection at ?request? end
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
