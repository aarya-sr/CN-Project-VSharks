from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):

    def send_response_data(self, data):
        body = json.dumps(data).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Backend", "A")
        self.send_header("Cache-Control", "max-age=30")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send_response_data({
                "backend": "A",
                "status": "running"
            })

        elif self.path == "/api/status":
            self.send_response_data({
                "backend": "A",
                "status": "ok"
            })

        else:
            self.send_response(404)
            self.end_headers()

server = HTTPServer(("0.0.0.0", 3001), Handler)

print("Backend A running on 10.7.23.31:3001")

server.serve_forever()
