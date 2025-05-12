

from flask import Flask, request, jsonify, send_from_directory, render_template
from threading import Thread
import sqlite3
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from bbl import BBLBestMatchFunctions as BBL_BMF
from functools import wraps

from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Define Comparison model
class Comparison(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User table
    avg_shots = db.Column(db.Float, nullable=False)
    avg_goals = db.Column(db.Float, nullable=False)
    avg_fouls = db.Column(db.Float, nullable=False)
    avg_cards = db.Column(db.Float, nullable=False)
    shot_accuracy = db.Column(db.Float, nullable=False)
    matched_team = db.Column(db.String(80), nullable=False)

    # Relationship to access the associated user
    user = db.relationship('User', backref='comparisons')

# Create the database tables
with app.app_context():
    print("Creating tables...")
    db.create_all()
    print("Tables created successfully.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'Username already exists!'})

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')




# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('landing_page'))
        else:
            return jsonify({'message': 'Invalid username or password!'})

    return render_template('login.html')


# Route for user logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/')
def landing_page():
    if 'user_id' not in session:  # Check if the user is logged in
        return redirect(url_for('register'))
    print("Landing page served")
    return render_template('index.html', username="Jessie")


@app.route('/forum')
def forum_page():
    return render_template('forum.html')

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    avg_shots = db.Column(db.Float, nullable=False)
    avg_goals = db.Column(db.Float, nullable=False)
    avg_fouls = db.Column(db.Float, nullable=False)
    avg_cards = db.Column(db.Float, nullable=False)
    shot_accuracy = db.Column(db.Float, nullable=False)

import csv

@app.route('/epl')
def epl_page():
    # Query all teams from the database
    team_data = Team.query.all()

    # Serialize the team data into a list of dictionaries
    serialized_team_data = [
        {
            'name': team.name,
            'avg_shots': team.avg_shots,
            'avg_goals': team.avg_goals,
            'avg_fouls': team.avg_fouls,
            'avg_cards': team.avg_cards,
            'shot_accuracy': team.shot_accuracy
        }
        for team in team_data
    ]

    # Pass the serialized data to the template
    return render_template('epl/epl.html', team_data=serialized_team_data)



@app.route('/afl')
def afl_page():
    return render_template('afl.html')

@app.route('/nba')
def nba_page():
    return render_template('nba.html')

@app.route('/bbl', methods=['GET', 'POST'])
def bbl_page():
    matches_bat = []
    matches_bowl = []
    if request.method == 'POST':
        # 1. Extract and validate form data
        bat_fields = ['bat_innings', 'bat_runs', 'bat_high', 'bat_avg', 'bat_sr']
        bowl_fields = ['bowl_overs', 'bowl_wkts', 'bowl_runs', 'bowl_avg', 'bowl_eco']
        bat_data = {f: request.form.get(f, type=float) for f in bat_fields}
        bowl_data = {f: request.form.get(f, type=float) for f in bowl_fields}

        # 2. Connect to DB
        db_path = os.path.join(os.path.dirname(__file__), 'static', 'bbl', 'data', 'data.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # 3. Batting: fetch averages, compute distances, get top 10
        if all(bat_data.values()):
            matches_bat = BBL_BMF.get_top_batters(conn, bat_data)

        # 4. Bowling: fetch averages, compute distances, get top 10
        if all(bowl_data.values()):
            matches_bowl = BBL_BMF.get_top_bowlers(conn, bowl_data)

        conn.close()
    return render_template('bbl.html', matches_bat=matches_bat, matches_bowl=matches_bowl)

# Route to serve static files (e.g., HTML, CSS, JS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# # Start Flask server in a separate thread
# def start_flask():
#     app.run(port=5000, debug=True, use_reloader=False)

@app.route('/get_team_data', methods=['GET'])
def get_team_data():
    team_data = Team.query.all()
    return jsonify([{
        'name': team.name,
        'avg_shots': team.avg_shots,
        'avg_goals': team.avg_goals,
        'avg_fouls': team.avg_fouls,
        'avg_cards': team.avg_cards,
        'shot_accuracy': team.shot_accuracy
    } for team in team_data])

@app.route('/teams')
def teams():
    return render_template('teams.html')


@app.route('/data')
def data():
    return render_template('data.html')



@app.route('/get_comparison', methods=['GET'])
@login_required
def get_comparison():
    username = request.args.get('username')
    selected_user = User.query.filter_by(username=username).first()

    if not selected_user:
        return jsonify({'message': 'User not found'}), 404

    # Fetch comparison data for the current user and the selected user
    current_user_data = Comparison.query.filter_by(user_id=session['user_id']).order_by(Comparison.id.desc()).first()
    selected_user_data = Comparison.query.filter_by(user_id=selected_user.id).first()

    return jsonify({
        'currentUser': {
            'avg_shots': current_user_data.avg_shots,
            'avg_goals': current_user_data.avg_goals,
            'avg_fouls': current_user_data.avg_fouls,
            'avg_cards': current_user_data.avg_cards,
            'shot_accuracy': current_user_data.shot_accuracy,
            'matched_team': current_user_data.matched_team
        },
        'selectedUser': {
            'username': selected_user.username,
            'avg_shots': selected_user_data.avg_shots,
            'avg_goals': selected_user_data.avg_goals,
            'avg_fouls': selected_user_data.avg_fouls,
            'avg_cards': selected_user_data.avg_cards,
            'shot_accuracy': selected_user_data.shot_accuracy,
            'matched_team': selected_user_data.matched_team
        }
    })
class UserResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    avg_shots = db.Column(db.Float, nullable=False)
    avg_goals = db.Column(db.Float, nullable=False)
    avg_fouls = db.Column(db.Float, nullable=False)
    avg_cards = db.Column(db.Float, nullable=False)
    shot_accuracy = db.Column(db.Float, nullable=False)
    matched_team = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



@app.route('/save_comparison', methods=['POST'])
@login_required
def save_comparison():
    try:
        # Get the JSON data sent from the frontend
        data = request.json

        # Create a new UserResult entry
        user_result = UserResult(
            user_id=session['user_id'],
            avg_shots=data['avg_shots'],
            avg_goals=data['avg_goals'],
            avg_fouls=data['avg_fouls'],
            avg_cards=data['avg_cards'],
            shot_accuracy=data['shot_accuracy'],
            matched_team=data['matched_team']
        )

        # Save to the database
        db.session.add(user_result)
        db.session.commit()

        return jsonify({'message': 'Comparison saved successfully!'})
    except Exception as e:
        return jsonify({'message': f'Error saving comparison: {str(e)}'}), 500

@app.route('/get_user_results', methods=['GET'])
@login_required
def get_user_results():
    # Fetch the latest result for the current user
    latest_result = UserResult.query.filter_by(user_id=session['user_id']).order_by(UserResult.timestamp.desc()).first()

    if not latest_result:
        return jsonify({'message': 'No results found for the current user'}), 404

    result = {
        'avg_shots': latest_result.avg_shots,
        'avg_goals': latest_result.avg_goals,
        'avg_fouls': latest_result.avg_fouls,
        'avg_cards': latest_result.avg_cards,
        'shot_accuracy': latest_result.shot_accuracy,
        'matched_team': latest_result.matched_team,
        'timestamp': latest_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify(result)


# Route to handle user search
@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('query', '').lower()  # Get the query parameter from the request
    if not query:
        return jsonify({"users": []})  # Return an empty list if no query is provided
# Query the database for matching usernames
    matching_users = User.query.filter(User.username.ilike(f"%{query}%")).all()
    return jsonify({"users": [user.username for user in matching_users]})


        
# # Route to serve static files (e.g., HTML, CSS, JS)
# @app.route('/static/<path:filename>')
# def serve_static(filename):
#     return send_from_directory('static', filename)

# # Start Flask server in a separate thread
# def start_flask():
#     app.run(port=5000, debug=True, use_reloader=False)



if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)





