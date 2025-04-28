from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_GET(self):
        # Set content type for CSV files
        if self.path.endswith('.csv'):
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.end_headers()
            with open(os.path.join(os.getcwd(), self.path[1:]), 'rb') as file:
                self.wfile.write(file.read())
        else:
            super().do_GET()

def run(server_class=HTTPServer, handler_class=CORSRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    print(f"Open http://localhost:{port}/afl.html in your browser")
    httpd.serve_forever()

if __name__ == '__main__':
    run() 