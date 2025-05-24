import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import time
import struct


class SpeedTestServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Server")

        self.tcp_frame = ttk.LabelFrame(root, text="TCP Server")
        self.tcp_frame.pack(padx=10, pady=5, fill="both")

        self.tcp_port_entry = ttk.Entry(self.tcp_frame)
        self.tcp_port_entry.pack()
        self.tcp_port_entry.insert(0, "12345")

        self.tcp_start_btn = ttk.Button(
            self.tcp_frame, text="Start TCP Server", command=self.start_tcp_server)
        self.tcp_start_btn.pack()

        self.udp_frame = ttk.LabelFrame(root, text="UDP Server")
        self.udp_frame.pack(padx=10, pady=5, fill="both")

        self.udp_port_entry = ttk.Entry(self.udp_frame)
        self.udp_port_entry.pack()
        self.udp_port_entry.insert(0, "12346")

        self.udp_start_btn = ttk.Button(
            self.udp_frame, text="Start UDP Server", command=self.start_udp_server)
        self.udp_start_btn.pack()

        self.log = scrolledtext.ScrolledText(root)
        self.log.pack(padx=10, pady=5, fill="both")

        self.tcp_server = None
        self.udp_server = None

    def log_message(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def start_tcp_server(self):
        port = int(self.tcp_port_entry.get())
        self.tcp_server = TcpServer(port, self.log_message)
        self.tcp_server.start()
        self.tcp_start_btn.config(state=tk.DISABLED)

    def start_udp_server(self):
        port = int(self.udp_port_entry.get())
        self.udp_server = UdpServer(port, self.log_message)
        self.udp_server.start()
        self.udp_start_btn.config(state=tk.DISABLED)


class TcpServer(threading.Thread):
    def __init__(self, port, log_callback):
        super().__init__()
        self.port = port
        self.log = log_callback
        self.running = True

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', self.port))
        self.sock.listen(5)
        self.log(f"TCP Server started on port {self.port}")
        while self.running:
            client, addr = self.sock.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        start = time.time()
        total = 0
        try:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                total += len(data)
        except:
            pass
        duration = time.time() - start
        speed = total / duration
        self.log(
            f"TCP: {total} bytes in {duration:.2f}s ({speed/1024:.2f} KB/s)")
        client.close()

    def stop(self):
        self.running = False
        self.sock.close()


class UdpServer(threading.Thread):
    def __init__(self, port, log_callback):
        super().__init__()
        self.port = port
        self.log = log_callback
        self.running = True
        self.stats = {
            'total': 0,
            'lost': 0,
            'delays': [],
            'sizes': [],
            'last_seq': -1
        }

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        self.sock.bind(('', self.port))
        self.log(f"UDP Server started on port {self.port}")

        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    recv_time = time.time()

                    if len(data) < 12:
                        continue

                    seq = int.from_bytes(data[:4], 'big')
                    send_time = struct.unpack('!d', data[4:12])[0]
                    packet_size = len(data)

                    delay = recv_time - send_time

                    self.stats['total'] += 1
                    self.stats['delays'].append(delay)
                    self.stats['sizes'].append(packet_size)

                    if self.stats['last_seq'] != -1:
                        lost = seq - self.stats['last_seq'] - 1
                        if lost > 0:
                            self.stats['lost'] += lost
                    self.stats['last_seq'] = seq

                except socket.timeout:
                    continue
        finally:
            self.show_stats()
            self.sock.close()

    def show_stats(self):
        if self.stats['total'] == 0:
            self.log("No packets received")
            return

        avg_delay = sum(self.stats['delays']) / self.stats['total'] * 1000
        max_delay = max(self.stats['delays']) * 1000
        min_delay = min(self.stats['delays']) * 1000
        avg_size = sum(self.stats['sizes']) / self.stats['total']

        stats_msg = (
            f"UDP Statistics:\n"
            f"Total received: {self.stats['total']}\n"
            f"Lost packets: {self.stats['lost']}\n"
            f"Avg delay: {avg_delay:.2f} ms\n"
            f"Max delay: {max_delay:.2f} ms\n"
            f"Min delay: {min_delay:.2f} ms\n"
            f"Avg packet size: {avg_size:.1f} bytes"
        )
        self.log(stats_msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedTestServerApp(root)
    root.mainloop()
