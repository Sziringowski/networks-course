import socket
import struct
import tkinter as tk
import argparse

def parse_args():
    p = argparse.ArgumentParser(description="remote draw client")
    p.add_argument('--host', default='127.0.0.1',
                   help='IP адрес или имя хоста сервера (default: 127.0.0.1)')
    p.add_argument('--port', type=int, default=9999,
                   help='порт сервера (default: 9999)')
    return p.parse_args()

class RemoteDrawClient:
    def __init__(self, host, port):
        try:
            self.sock = socket.create_connection((host, port), timeout=5)
            print(f"Connected to server at {host}:{port}")
        except Exception as e:
            print(f"Ошибка подключения к {host}:{port} → {e}")
            exit(1)

        self.prev_x = self.prev_y = None
        self.root = tk.Tk()
        self.root.title("client: draw here")
        self.canvas = tk.Canvas(self.root, bg='white', width=600, height=400)
        self.canvas.pack()
        self.canvas.bind("<B1-Motion>", self.on_drag)

    def on_drag(self, event):
        x, y = event.x, event.y
        if self.prev_x is not None:
            self.canvas.create_line(self.prev_x, self.prev_y, x, y,
                                    fill='black', width=2)
        self.prev_x, self.prev_y = x, y
        pkt = struct.pack('!ff', float(x), float(y))
        try:
            self.sock.sendall(pkt)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    args = parse_args()
    client = RemoteDrawClient(args.host, args.port)
    client.run()