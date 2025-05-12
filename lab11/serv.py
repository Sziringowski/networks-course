import socket
import threading
import struct
import queue
import tkinter as tk

HOST = 'localhost'
PORT = 9999

def client_thread(conn, data_queue):
    try:
        while True:
            buf = conn.recv(8)
            if not buf:
                break
            x, y = struct.unpack('!ff', buf)
            data_queue.put((x, y))
    except ConnectionError:
        pass
    finally:
        conn.close()

def gui_loop(data_queue):
    global prev_x, prev_y
    try:
        while True:
            x, y = data_queue.get_nowait()
            if prev_x is not None:
                canvas.create_line(prev_x, prev_y, x, y, fill='blue', width=2)
            prev_x, prev_y = x, y
    except queue.Empty:
        pass
    root.after(20, gui_loop, data_queue)

if __name__ == '__main__':
    data_queue = queue.Queue()
    prev_x = prev_y = None

    root = tk.Tk()
    root.title("server: remote drawing")
    canvas = tk.Canvas(root, bg='white', width=600, height=400)
    canvas.pack()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"server listening on {HOST}:{PORT} ...")

    def accept_conn():
        conn, addr = srv.accept()
        print("connected by", addr)
        threading.Thread(target=client_thread, args=(conn, data_queue), daemon=True).start()

    threading.Thread(target=accept_conn, daemon=True).start()

    root.after(20, gui_loop, data_queue)
    root.mainloop()