from flask import Flask, request, session, g
from flask import render_template
from db import init_db, get_db
from auth import auth_bp

app = Flask(__name__)
app.secret_key = 'dev'

app.register_blueprint(auth_bp)

DATABASE = 'users.db'
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


# Close the database connection at request end
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
