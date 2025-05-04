# from http.server import HTTPServer, SimpleHTTPRequestHandler
# import os

# class CORSRequestHandler(SimpleHTTPRequestHandler):
#     def end_headers(self):
#         self.send_header('Access-Control-Allow-Origin', '*')
#         self.send_header('Access-Control-Allow-Methods', 'GET')
#         self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
#         return super().end_headers()

#     def do_GET(self):
#         # Set content type for CSV files
#         if self.path.endswith('.csv'):
#             self.send_response(200)
#             self.send_header('Content-type', 'text/csv')
#             self.end_headers()
#             with open(os.path.join(os.getcwd(), self.path[1:]), 'rb') as file:
#                 self.wfile.write(file.read())
#         else:
#             super().do_GET()

# def run(server_class=HTTPServer, handler_class=CORSRequestHandler, port=8000):
#     server_address = ('', port)
#     httpd = server_class(server_address, handler_class)
#     print(f"Starting server on port {port}")
#     print(f"Open http://localhost:{port}/afl.html in your browser")
#     httpd.serve_forever()

# if __name__ == '__main__':
#     run() 

from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
from threading import Thread
import os
import requests

# Initialize Flask app
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)

API_KEY = os.getenv('SPORTSDATAIO_KEY', 'your_key_here')

# Example user data (replace with your DB later)
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
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify({"users": []})
    matching = [u for u in users if query in u["username"].lower()]
    return jsonify({"users": matching})

# Home page: fetch standings and pass into template
@app.route('/')
def home():
    standings = []
    try:
        url = f'https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key={API_KEY}'
        resp = requests.get(url)
        resp.raise_for_status()
        standings = resp.json()
    except requests.RequestException as e:
        app.logger.error(f'Error fetching standings: {e}')
    return render_template('index.html', username="Jessie", standings=standings)

# Static content pages
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
    return render_template('nba/nba.html')

@app.route('/bbl')
def bbl_page():
    return render_template('bbl.html')

# Teams page (supports /teams, /teams.html, /teams/<team_key>)
@app.route('/teams')
@app.route('/teams.html')
@app.route('/teams/<team_key>')
def teams(team_key=None):
    team_map = {
        'BOS': 'Boston Celtics',
        'LAL': 'Los Angeles Lakers',
        'GS':  'Golden State Warriors',
        'MIA': 'Miami Heat',
        # … add more …
    }
    logos = {
        k: url_for('static', filename=f'logos/{k}.png')
        for k in team_map
    }
    return render_template(
        'teams.html',
        teams=team_map,
        logos=logos,
        selected_team=team_key
    )

# Data page (“Find Your Match”)
@app.route('/data')
@app.route('/data.html')
def data():
    return render_template('data.html')

# NBA standings JSON endpoint
@app.route('/nba-stats')
def nba_stats():
    url = f'https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key={API_KEY}'
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        app.logger.error(f'Error fetching standings: {e}')
        return jsonify({'error': 'Failed to fetch data'}), 500

# Route to serve static files (if needed alongside Flask’s /static/)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def start_flask():
    # run Flask on port 3000 (same as your existing script)
    app.run(port=3000, debug=True, use_reloader=False)

def start_static_server():
    from http.server import HTTPServer, SimpleHTTPRequestHandler

    class CORSRequestHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            return super().end_headers()

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print("Starting static file server on port 8000")
    print("Open http://localhost:8000/index.html in your browser")
    httpd.serve_forever()

if __name__ == '__main__':
    Thread(target=start_flask).start()
    start_static_server()
