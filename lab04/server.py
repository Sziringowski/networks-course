import http.server
import socketserver

PORT = 8080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Пример простого ответа на GET
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        response_body = b"<html><body><h1>Hello from Target Server</h1></body></html>"
        self.wfile.write(response_body)

    def do_POST(self):
        # Пример простого ответа на POST (эхо-тело запроса)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        response_text = f"""
        <html>
        <body>
            <h1>POST data received:</h1>
            <pre>{body.decode('utf-8', errors='replace')}</pre>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response_text.encode("utf-8"))

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Target server is listening on port {PORT}")
        httpd.serve_forever()
