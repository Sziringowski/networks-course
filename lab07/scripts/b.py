import socket
import time

def ping_client():
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1)
        
        for seq in range(1, 11):
            send_time = time.time()
            message = f"Ping {seq} {send_time}"
            s.sendto(message.encode(), (host, port))
            try:
                data, addr = s.recvfrom(1024)
                rtt = (time.time() - send_time) * 1000  # ms
                print(f"Reply from {addr[0]}: bytes={len(data)} time={rtt:.2f}ms")
            except socket.timeout:
                print("Request timed out")

if __name__ == "__main__":
    ping_client()