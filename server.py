

from flask import Flask, request, jsonify, send_from_directory, render_template
from threading import Thread
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
    return render_template('nba/nba.html')

@app.route('/bbl')
def bbl_page():
    return render_template('bbl.html')




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


