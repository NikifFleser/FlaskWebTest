CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    score INTEGER
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    matchday INTEGER NOT NULL,
    date DATE NOT NULL,
    location TEXT NOT NULL,
    result TEXT
);

CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    team1_goals INTEGER,
    team2_goals INTEGER,
    bet_score INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (match_id) REFERENCES match (id)
);
