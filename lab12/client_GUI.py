import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import time
import os
import struct


class SpeedTestClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Client")

        ttk.Label(root, text="Server IP:").pack()
        self.ip_entry = ttk.Entry(root)
        self.ip_entry.pack()
        self.ip_entry.insert(0, "127.0.0.1")

        self.tcp_frame = ttk.LabelFrame(root, text="TCP Test")
        self.tcp_frame.pack(padx=10, pady=5, fill="both")

        self.tcp_port_entry = ttk.Entry(self.tcp_frame)
        self.tcp_port_entry.pack()
        self.tcp_port_entry.insert(0, "12345")

        self.tcp_duration_entry = ttk.Entry(self.tcp_frame)
        self.tcp_duration_entry.pack()
        self.tcp_duration_entry.insert(0, "10")

        self.tcp_start_btn = ttk.Button(
            self.tcp_frame, text="Start TCP Test", command=self.start_tcp_test)
        self.tcp_start_btn.pack()

        self.udp_frame = ttk.LabelFrame(root, text="UDP Test")
        self.udp_frame.pack(padx=10, pady=5, fill="both")

        self.udp_port_entry = ttk.Entry(self.udp_frame)
        self.udp_port_entry.pack()
        self.udp_port_entry.insert(0, "12346")

        self.udp_duration_entry = ttk.Entry(self.udp_frame)
        self.udp_duration_entry.pack()
        self.udp_duration_entry.insert(0, "10")

        self.udp_start_btn = ttk.Button(
            self.udp_frame, text="Start UDP Test", command=self.start_udp_test)
        self.udp_start_btn.pack()

        self.log = scrolledtext.ScrolledText(root)
        self.log.pack(padx=10, pady=5, fill="both")

    def log_message(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def start_tcp_test(self):
        ip = self.ip_entry.get()
        port = int(self.tcp_port_entry.get())
        duration = int(self.tcp_duration_entry.get())
        threading.Thread(target=self.run_tcp_test,
                         args=(ip, port, duration)).start()

    def run_tcp_test(self, ip, port, duration):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            start = time.time()
            end_time = start + duration
            total = 0
            while time.time() < end_time:
                data = os.urandom(1024)
                sock.sendall(data)
                total += len(data)
            duration = time.time() - start
            speed = total / duration
            self.log_message(
                f"TCP Sent: {total} bytes, Speed: {speed/1024:.2f} KB/s")
            sock.close()
        except Exception as e:
            self.log_message(f"TCP Error: {e}")

    def start_udp_test(self):
        ip = self.ip_entry.get()
        port = int(self.udp_port_entry.get())
        duration = int(self.udp_duration_entry.get())
        threading.Thread(target=self.run_udp_test,
                         args=(ip, port, duration)).start()

    def run_udp_test(self, ip, port, duration):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            seq = 0
            start = time.time()
            end_time = start + duration
            packet_size = 1024

            while time.time() < end_time:
                send_time = time.time()
                header = (
                    seq.to_bytes(4, 'big') +
                    struct.pack('!d', send_time))
                data = header + os.urandom(packet_size - len(header))

                sock.sendto(data, (ip, port))
                seq += 1

            self.log_message(f"UDP Sent: {seq} packets")
            sock.close()
        except Exception as e:
            self.log_message(f"UDP Error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedTestClientApp(root)
    root.mainloop()
