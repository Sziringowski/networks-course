from socket import *
import os
import sys
import threading

# семафор 
class ThreadedHTTPServer:
    def __init__(self, port, concurrency_level):
        self.port = port
        self.concurrency_level = concurrency_level
        self.semaphore = threading.Semaphore(concurrency_level)

    def handle_request(self, client_socket):
        with self.semaphore:  # лимит
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                client_socket.close()
                return

            lines = request.split('\r\n')
            first_line = lines[0]

            parts = first_line.split()
            if len(parts) < 2:
                client_socket.close()
                return

            method, path = parts[0], parts[1]

            if method != 'GET':
                response = "HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed"
                client_socket.sendall(response.encode())
                client_socket.close()
                return

            # путь к файлу
            filepath = path.lstrip('/')
            if filepath == '':
                filepath = 'index.html'

            # абсолютный путь к файлу
            full_path = os.path.join(os.getcwd(), filepath)

            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    content = f.read()
                response = "HTTP/1.1 200 OK\r\n"
                response += f"Content-Length: {len(content)}\r\n"
                response += "Content-Type: text/html\r\n\r\n"
                response = response.encode() + content
            else:
                response = "HTTP/1.1 404 Not Found\r\n"
                response += "Content-Type: text/html\r\n\r\n"
                response += "<h1>404 Not Found</h1><p>The requested resource was not found on the server.</p>"
            
            client_socket.sendall(response)
            client_socket.close()

    def run_server(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', self.port))
        server_socket.listen(5)  # макс количество ожидающих соединений
        print(f"Server is running on port {self.port} with concurrency level {self.concurrency_level}...")

        while True:
            client_socket, _ = server_socket.accept()
            print("Accepted a new connection.")
            # новый поток для обработки запроса
            thread = threading.Thread(target=self.handle_request, args=(client_socket,))
            thread.start()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <server_port> <concurrency_level>")
        sys.exit(1)

    port = int(sys.argv[1])
    concurrency_level = int(sys.argv[2])
    server = ThreadedHTTPServer(port, concurrency_level)
    server.run_server()
