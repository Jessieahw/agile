

from flask import Flask, request, jsonify, send_from_directory, render_template
from threading import Thread
import sqlite3
import os

# Initialize Flask app
app = Flask(__name__)

# Example user data (replace this with the database query later)
users = [
    {"username": "john_doe"},
    {"username": "jane_smith"},
    {"username": "jackson"},
    {"username": "jill_brown"},
    {"username": "james_bond"}
]

# Route to handle user search
@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('query', '').lower()  # Get the query parameter from the request
    if not query:
        return jsonify({"users": []})  # Return an empty list if no query is provided

    # Filter users whose username contains the query (case-insensitive)
    matching_users = [user for user in users if query in user["username"].lower()]
    return jsonify({"users": matching_users})  # Return the matching users as JSON

# Route to serve the landing page (e.g., index.html)
@app.route('/')
def landing_page():
    print("Landing page served")
    return render_template('index.html',username="Jessie")

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

# BBL PAGE SECTION:
def get_top_batters(conn, user_stats):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.player_name,
               AVG(b.runs) AS avg_runs,
               MAX(b.runs) AS high_score,
               AVG(b.runs * 1.0 / NULLIF(b.balls,0)) AS avg_strike_rate,
               AVG(b.runs) * 1.0 / COUNT(*) AS avg_bat_avg
        FROM BBL_Players p
        JOIN BBL_BattingInnings b ON p.player_id = b.player_id
        GROUP BY p.player_id
        HAVING COUNT(*) > 5
    """)
    players = cur.fetchall()
    results = []
    for row in players:
        # Use only available stats for distance
        dist = (
            (user_stats['bat_runs'] - row['avg_runs']) ** 2 +
            (user_stats['bat_high'] - row['high_score']) ** 2 +
            (user_stats['bat_sr'] - row['avg_strike_rate']) ** 2 +
            (user_stats['bat_avg'] - row['avg_bat_avg']) ** 2
        ) ** 0.5
        results.append({'name': row['player_name'], 'distance': dist})
    results.sort(key=lambda x: x['distance'])
    return results[:10]

def get_top_bowlers(conn, user_stats):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.player_name,
               AVG(bi.overs) AS avg_overs,
               AVG(bi.wickets) AS avg_wkts,
               AVG(bi.runs) AS avg_runs,
               AVG(bi.economy) AS avg_eco
        FROM BBL_Players p
        JOIN BBL_BowlingInnings bi ON p.player_id = bi.player_id
        GROUP BY p.player_id
        HAVING COUNT(*) > 5
    """)
    players = cur.fetchall()
    results = []
    for row in players:
        dist = (
            (user_stats['bowl_overs'] - row['avg_overs']) ** 2 +
            (user_stats['bowl_wkts'] - row['avg_wkts']) ** 2 +
            (user_stats['bowl_runs'] - row['avg_runs']) ** 2 +
            (user_stats['bowl_eco'] - row['avg_eco']) ** 2
        ) ** 0.5
        results.append({'name': row['player_name'], 'distance': dist})
    results.sort(key=lambda x: x['distance'])
    return results[:10]

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
            matches_bat = get_top_batters(conn, bat_data)

        # 4. Bowling: fetch averages, compute distances, get top 10
        if all(bowl_data.values()):
            matches_bowl = get_top_bowlers(conn, bowl_data)

        conn.close()
    return render_template('bbl.html', matches_bat=matches_bat, matches_bowl=matches_bowl)

# Route to serve static files (e.g., HTML, CSS, JS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Start Flask server in a separate thread
def start_flask():
    app.run(port=5000, debug=True, use_reloader=False)
    
# # Start the static file server
# def start_static_server():
#     from http.server import HTTPServer, SimpleHTTPRequestHandler

#     class CORSRequestHandler(SimpleHTTPRequestHandler):
#         def end_headers(self):
#             self.send_header('Access-Control-Allow-Origin', '*')
#             self.send_header('Access-Control-Allow-Methods', 'GET')
#             self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
#             return super().end_headers()

#     server_address = ('', 8000)
#     httpd = HTTPServer(server_address, CORSRequestHandler)
#     print("Starting static file server on port 8000")
#     print("Open http://localhost:8000/index.html in your browser")
#     httpd.serve_forever()


@app.route('/teams')
def teams():
    return render_template('teams.html')

@app.route('/data')
def data():
    return render_template('data.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)


