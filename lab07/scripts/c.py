import socket
import time

def ping_client():
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1)
        rtt_list = []
        lost = 0

        for seq in range(1, 11):
            send_time = time.time()
            message = f"Ping {seq} {send_time}"
            s.sendto(message.encode(), (host, port))
            try:
                data, addr = s.recvfrom(1024)
                rtt = (time.time() - send_time) * 1000
                rtt_list.append(rtt)
                print(f"Reply from {addr[0]}: bytes={len(data)} time={rtt:.2f}ms")
            except socket.timeout:
                lost += 1
                print("Request timed out")

        print(f"\n--- {host} ping statistics ---")
        print(f"10 packets transmitted, {10 - lost} received, {lost * 10}% packet loss")
        if rtt_list:
            print(f"rtt min/avg/max = {min(rtt_list):.2f}/{sum(rtt_list)/len(rtt_list):.2f}/{max(rtt_list):.2f} ms")

if __name__ == "__main__":
    ping_client()