
from config import Config

from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, render_template
from threading import Thread
import sqlite3
import os
from form import EPLTeamForm
from extensions import db
from nba import nba_bp
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from models import User, PlayerComparison
from models import Submission
from flask_migrate import Migrate

from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from forms import BBLStatsForm, LoginForm, RegisterForm, TemplateDataNBA
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os
from bbl import BBLBestMatchFunctions as BBL_BMF
from functools import wraps
import csv

# Setup the flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

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

# Team model
# class Team(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), nullable=False)
#     avg_shots = db.Column(db.Float, nullable=False)
#     avg_goals = db.Column(db.Float, nullable=False)
#     avg_fouls = db.Column(db.Float, nullable=False)
#     avg_cards = db.Column(db.Float, nullable=False)
#     shot_accuracy = db.Column(db.Float, nullable=False)

def create_app(test_config=None):
    

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key')

    # Default config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Override config if testing
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'login'    

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
        team_data = Team.query.all()
        serialized = [{
            'name': team.name,
            'avg_shots': team.avg_shots,
            'avg_goals': team.avg_goals,
            'avg_fouls': team.avg_fouls,
            'avg_cards': team.avg_cards,
            'shot_accuracy': team.shot_accuracy
        } for team in team_data]
        return render_template('epl/epl.html', team_data=serialized, csrf_token=generate_csrf())

    @app.route('/afl')
    @login_required
    def afl_page():
        return render_template('afl.html')

    @app.route('/nba')
    @login_required
    def nba_page():
        return render_template('nba.html')

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

    @app.route('/get_team_data', methods=['GET'])
    @login_required
    def get_team_data():
        team_data = Team.query.all()
        return jsonify([{ 'name': team.name, 'avg_shots': team.avg_shots, 'avg_goals': team.avg_goals, 'avg_fouls': team.avg_fouls, 'avg_cards': team.avg_cards, 'shot_accuracy': team.shot_accuracy } for team in team_data])

    @app.route('/teams')
    @login_required
    def teams():
        return render_template('teams.html')

    @app.route('/data')
    @login_required
    def data():
        form = TemplateDataNBA()
        # If it is a POST request, process the form data
        if form.validate_on_submit():
            return render_template('data.html', form=form)
        # If it is a GET request, just render the template
        return render_template('data.html', form=form)

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

    # Register routes (move your existing routes here or import from views.py)
    return app



app = create_app()


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)
