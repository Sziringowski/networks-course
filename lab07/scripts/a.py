import socket
import random

def ping_server():
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print(f"Ping server listening on {host}:{port}")

        while True:
            data, addr = s.recvfrom(1024)
            print(f"Received from {addr}: {data.decode()}")
            if random.random() < 0.2:
                print("Simulating packet loss")
                continue
            response = data.decode().upper()
            s.sendto(response.encode(), addr)

if __name__ == "__main__":
    ping_server()