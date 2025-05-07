import socket
import time

def heartbeat_client():
    host = 'localhost'
    port = 12346

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        seq = 1
        while True:
            message = f"HEARTBEAT {seq} {time.time()}"
            s.sendto(message.encode(), (host, port))
            print(f"Sent heartbeat {seq}")
            seq += 1
            time.sleep(1)

if __name__ == "__main__":
    heartbeat_client()