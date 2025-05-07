import socket
import time
import threading

def heartbeat_server():
    host = 'localhost'
    port = 12346
    timeout = 5  # s

    clients = {}

    def monitor_clients():
        while True:
            current_time = time.time()
            for addr in list(clients.keys()):
                if current_time - clients[addr] > timeout:
                    print(f"Client {addr} is down")
                    del clients[addr]
            time.sleep(1)

    threading.Thread(target=monitor_clients, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print(f"Heartbeat server listening on {host}:{port}")
        while True:
            data, addr = s.recvfrom(1024)
            clients[addr] = time.time()
            print(f"Heartbeat from {addr}: {data.decode()}")

if __name__ == "__main__":
    heartbeat_server()