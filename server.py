from extensions import db

# Standard library imports
from config import Config
import os
import csv
import sqlite3
from threading import Thread
from datetime import datetime
from functools import wraps
import base64
import time
# Flask-related imports
from flask import (
    Flask, request, jsonify, send_from_directory, render_template,
    redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Third-party imports
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from werkzeug.security import generate_password_hash, check_password_hash

# Local application imports
from config import Config

from forms import BBLStatsForm, LoginForm, RegisterForm, TemplateDataNBA, EPLTeamForm
from bbl import BBLBestMatchFunctions as BBL_BMF

from models import User, PlayerComparison, Submission, ForumPost
from nba import nba_bp

# Setup the flask extensions

login_manager = LoginManager()
csrf = CSRFProtect()


# Models


# Comparison model
class Comparison(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    avg_shots = db.Column(db.Float, nullable=False)
    avg_goals = db.Column(db.Float, nullable=False)
    avg_fouls = db.Column(db.Float, nullable=False)
    avg_cards = db.Column(db.Float, nullable=False)
    shot_accuracy = db.Column(db.Float, nullable=False)
    matched_team = db.Column(db.String(80), nullable=False)
    user = db.relationship('User', backref='comparisons')


def load_team_data_from_csv():
    csv_file_path = os.path.join(os.path.dirname(__file__), 'static', 'epl_data', 'team_comparison_stats.csv')
    teams = []
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teams.append({
                'name': row['Team'],
                'avg_shots': float(row['Average Shots per Match']),
                'avg_goals': float(row['Average Goals per Match']),
                'avg_fouls': float(row['Average Fouls per Match']),
                'avg_cards': float(row['Average Cards per Match']),
                'shot_accuracy': float(row['Shot Accuracy'])
            })
    return teams


def create_app(test_config=None):
    

    app = Flask(__name__)
    app.config.from_object(Config)

    # Override config if testing
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate = Migrate(app, db) # Bringing this back from last commit
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'login' 


    app.register_blueprint(nba_bp, url_prefix='/nba')
 

    # Create tables
    with app.app_context():
        db.create_all()

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            if User.query.filter_by(username=username).first():
                return jsonify({'message': 'Username already exists!'})
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('landing_page'))
            return jsonify({'message': 'Invalid username or password!'})
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def landing_page():
        return render_template('index.html', username=current_user.username)

    @app.route('/forum')
    @login_required
    def forum_page():
        return render_template('forum.html')

    @app.route('/epl')
    @login_required
    def epl_page():
        form = EPLTeamForm()
        team_data = load_team_data_from_csv()
        return render_template('epl/epl.html', team_data=team_data, form=form)

    @app.route('/afl')
    @login_required
    def afl_page():
        return render_template('afl.html')

    @app.route('/nba')
    @login_required
    def nba_page():
        return render_template('nba/nba.html')

    @app.route('/bbl', methods=['GET', 'POST'])
    @login_required
    def bbl_page():
        form = BBLStatsForm()
        matches_bat, matches_bowl = [], []
        bat_data, bowl_data = {}, {}
        if form.validate_on_submit(): 
            bat_fields = ['bat_innings', 'bat_runs', 'bat_high', 'bat_avg', 'bat_sr']
            bowl_fields = ['bowl_overs', 'bowl_wkts', 'bowl_runs', 'bowl_avg', 'bowl_eco']
            bat_data = {f: request.form.get(f, type=float) for f in bat_fields}
            bowl_data = {f: request.form.get(f, type=float) for f in bowl_fields}
            db_path = os.path.join(os.path.dirname(__file__), 'static', 'bbl', 'data', 'data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            if all(bat_data.values()):
                matches_bat = BBL_BMF.get_top_batters(conn, bat_data)
            if all(bowl_data.values()):
                matches_bowl = BBL_BMF.get_top_bowlers(conn, bowl_data)
            conn.close()
        user_stats = {**bat_data, **bowl_data} if request.method == 'POST' else {}
        return render_template('bbl.html', matches_bat=matches_bat, matches_bowl=matches_bowl, user_stats=user_stats, form=form)

    @app.route('/bbl/json', methods=['POST'])
    @login_required
    @csrf.exempt                       # tell Flask-WTF we are handling CSRF manually
    def bbl_json():                    # NEW: JSON version of the similarity search
        """
        Accepts the form via fetch(), returns JSON:
            {
            "user" : { …user stats… },
            "bat"  : [ …top 10 similar batters… ],
            "bowl" : [ …top 10 similar bowlers… ]
            }
        """
        # ---- 1. parse user input ------------------------------------------------
        f = request.form     # same names as the original form fields
        bat_fields  = ['bat_innings', 'bat_runs', 'bat_high', 'bat_avg', 'bat_sr']
        bowl_fields = ['bowl_overs', 'bowl_wkts', 'bowl_runs', 'bowl_avg', 'bowl_eco']

        bat_data  = {k: float(f.get(k, 0) or 0) for k in bat_fields}
        bowl_data = {k: float(f.get(k, 0) or 0) for k in bowl_fields}

        # ---- 2. query DB for similar players ------------------------------------
        db_path = os.path.join(app.root_path, 'static', 'bbl', 'data', 'data.db')
        conn    = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        matches_bat  = BBL_BMF.get_top_batters(conn, bat_data)  if all(bat_data.values())  else []
        matches_bowl = BBL_BMF.get_top_bowlers(conn, bowl_data) if all(bowl_data.values()) else []
        conn.close()

        user_stats = {**bat_data, **bowl_data}

        # ---- 3. return JSON ------------------------------------------------------
        return jsonify({
            "user": user_stats,
            "bat" : matches_bat,
            "bowl": matches_bowl
        })
    @app.route('/bbl/player_search')
    @login_required
    def bbl_player_search():
        q = request.args.get('q', '').strip()
        return jsonify(BBL_BMF.search_players(q)) if q else jsonify([])

    @app.route('/bbl/team_list')
    @login_required
    def bbl_team_list():
        return jsonify(BBL_BMF.list_teams())

    @app.route('/bbl/team_stats')
    @login_required
    def bbl_team_stats():
        team = request.args.get('team', '')
        return jsonify(BBL_BMF.get_team_stats(team)) if team else jsonify({})

 

    @app.route('/get_comparison')
    @login_required
    def get_comparison():
        username = request.args.get('username')
        if not username:
            return jsonify({'message': 'No username provided'}), 400
        selected_user = User.query.filter_by(username=username).first()
        if not selected_user:
            return jsonify({'message': 'User not found'}), 404
        selected_result = Comparison.query.filter_by(user_id=selected_user.id).order_by(Comparison.id.desc()).first()
        current_result = Comparison.query.filter_by(user_id=current_user.id).order_by(Comparison.id.desc()).first()
        if not selected_result or not current_result:
            return jsonify({'message': 'No results found'}), 404
        return jsonify({
            'currentUser': {
                'avg_shots': current_result.avg_shots,
                'avg_goals': current_result.avg_goals,
                'avg_fouls': current_result.avg_fouls,
                'avg_cards': current_result.avg_cards,
                'shot_accuracy': current_result.shot_accuracy,
            },
            'selectedUser': {
                'username': selected_user.username,
                'avg_shots': selected_result.avg_shots,
                'avg_goals': selected_result.avg_goals,
                'avg_fouls': selected_result.avg_fouls,
                'avg_cards': selected_result.avg_cards,
                'shot_accuracy': selected_result.shot_accuracy,
            }
        })

    @app.route('/save_comparison', methods=['POST'])
    @login_required
    def save_comparison():
        try:
            data = request.json
            comparison = Comparison(
                user_id=current_user.id,
                avg_shots=data['avg_shots'],
                avg_goals=data['avg_goals'],
                avg_fouls=data['avg_fouls'],
                avg_cards=data['avg_cards'],
                shot_accuracy=data['shot_accuracy'],
                matched_team=data['matched_team']
            )
            db.session.add(comparison)
            db.session.commit()
            return jsonify({'message': 'Comparison saved successfully!'})
        except Exception as e:
            return jsonify({'message': f'Error saving comparison: {str(e)}'}), 500

    @app.route('/get_user_results', methods=['GET'])
    @login_required
    def get_user_results():
        latest_result = Comparison.query.filter_by(user_id=current_user.id).order_by(Comparison.id.desc()).first()
        if not latest_result:
            return jsonify({'message': 'No results found for the current user'}), 404
        result = {
            'avg_shots': latest_result.avg_shots,
            'avg_goals': latest_result.avg_goals,
            'avg_fouls': latest_result.avg_fouls,
            'avg_cards': latest_result.avg_cards,
            'shot_accuracy': latest_result.shot_accuracy,
            'matched_team': latest_result.matched_team
        }
        return jsonify(result)

    @app.route('/search_users', methods=['GET'])
    @login_required
    def search_users():
        query = request.args.get('query', '').lower()
        if not query:
            return jsonify({"users": []})
        matching_users = User.query.filter(User.username.ilike(f"%{query}%")).all()
        return jsonify({"users": [user.username for user in matching_users]})

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)
    

    @app.route('/submit_post', methods=['POST'])
    @login_required
    def submit_post():
        data = request.get_json()
        text = data.get('text', '')
        image_data = data.get('image', None)
        recipient_username = data.get('recipient_username', None)
        image_path = None
        recipient_id = None

        if recipient_username:
            recipient = User.query.filter_by(username=recipient_username).first()
            if recipient:
                recipient_id = recipient.id

        if image_data:
            header, encoded = image_data.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            directory = 'static/forum_images'
            os.makedirs(directory, exist_ok=True)
            filename = f"{directory}/{current_user.username}_{int(time.time())}.png"
            with open(filename, "wb") as f:
                f.write(img_bytes)
            image_path = filename

        post = ForumPost(
            user_id=current_user.id,
            username=current_user.username,
            text=text,
            image_path=image_path,
            recipient_id=recipient_id
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({'message': 'Post created!'})

    
    @app.route('/all_posts')
    @login_required
    def all_posts():
        """
        view=public     → everyone’s public posts  
        view=received   → private posts addressed **to** me  
        view=sent       → private posts I **sent** to someone else  

        The old …?private=1 alias still works so existing links don’t break.
        """
        # Back-compat for legacy ?private=1 links
        if request.args.get('private'):
            view = 'received'
        else:
            view = request.args.get('view', 'public').lower()

        q = ForumPost.query.order_by(ForumPost.timestamp.desc())

        if view == 'public':
            q = q.filter(ForumPost.recipient_id.is_(None))

        elif view == 'received':
            q = q.filter(ForumPost.recipient_id == current_user.id)

        elif view == 'sent':
            q = q.filter(
                ForumPost.user_id == current_user.id,
                ForumPost.recipient_id.is_not(None)
            )

        else:                       # unknown ⇒ public
            q = q.filter(ForumPost.recipient_id.is_(None))

        return render_template('all_posts.html', posts=q.all())

    return app

app = create_app()


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)
