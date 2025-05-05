

from flask import Flask, request, jsonify, send_from_directory, render_template
from threading import Thread
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    avg_shots = db.Column(db.Float, nullable=False)
    avg_goals = db.Column(db.Float, nullable=False)
    avg_fouls = db.Column(db.Float, nullable=False)
    avg_cards = db.Column(db.Float, nullable=False)
    shot_accuracy = db.Column(db.Float, nullable=False)
    matched_team = db.Column(db.String(80), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()



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



# Example user data (replace this with the database query later)
# users = [
#     {"username": "john_doe"},
#     {"username": "jane_smith"},
#     {"username": "jackson"},
#     {"username": "jill_brown"},
#     {"username": "james_bond"}
# ]

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



@app.route('/epl')
def epl_page():
    return render_template('epl/epl.html')

@app.route('/afl')
def afl_page():
    return render_template('afl.html')

@app.route('/nba')
def nba_page():
    return render_template('nba.html')

@app.route('/bbl')
def bbl_page():
    return render_template('bbl.html')


@app.route('/teams')
def teams():
    return render_template('teams.html')


@app.route('/data')
def data():
    return render_template('data.html')





@app.route('/save_comparison', methods=['POST'])
@login_required
def save_comparison():
    data = request.json
    comparison = Comparison(
        user_id=session['user_id'],
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





# Route to handle user search
@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('query', '').lower()  # Get the query parameter from the request
    if not query:
        return jsonify({"users": []})  # Return an empty list if no query is provided

    # Filter users whose username contains the query (case-insensitive)
    matching_users = [user for user in users if query in user["username"].lower()]
    return jsonify({"users": matching_users})  # Return the matching users as JSON




# Route to serve static files (e.g., HTML, CSS, JS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# # Start Flask server in a separate thread
# def start_flask():
#     app.run(port=5000, debug=True, use_reloader=False)



if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)





