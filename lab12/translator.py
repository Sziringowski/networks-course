import json
import socket
import threading
from tkinter import *
from tkinter import ttk
import os
import time


class PortTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Translator")
        self.config_file = "config.json"
        self.rules = []
        self.listeners = {}
        self.active_connections = []

        self.rules_tree = ttk.Treeview(root, columns=(
            'From Port', 'To IP', 'To Port', 'Status'), show='headings')
        self.rules_tree.heading('From Port', text='From Port')
        self.rules_tree.heading('To IP', text='To IP')
        self.rules_tree.heading('To Port', text='To Port')
        self.rules_tree.heading('Status', text='Status')
        self.rules_tree.pack()

        self.update_button = Button(
            root, text="Reload Config", command=self.reload_config)
        self.update_button.pack()

        self.load_config()
        self.update_rules_gui()

        self.last_mtime = os.path.getmtime(self.config_file)
        threading.Thread(target=self.monitor_config, daemon=True).start()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                new_rules = json.load(f)
                new_rules = [{'from_port': int(r['from_port']), 'to_ip': r['to_ip'], 'to_port': int(
                    r['to_port'])} for r in new_rules]
                current_ports = {r['from_port'] for r in self.rules}
                new_ports = {r['from_port'] for r in new_rules}

                for port in current_ports - new_ports:
                    self.stop_listener(port)

                for rule in new_rules:
                    if rule['from_port'] not in current_ports:
                        self.start_listener(rule)
                    else:
                        old_rule = next(
                            r for r in self.rules if r['from_port'] == rule['from_port'])
                        if old_rule['to_ip'] != rule['to_ip'] or old_rule['to_port'] != rule['to_port']:
                            self.stop_listener(rule['from_port'])
                            self.start_listener(rule)

                self.rules = new_rules
        except Exception as e:
            print(f"Error loading config: {e}")

    def start_listener(self, rule):
        from_port = rule['from_port']
        if from_port in self.listeners:
            return

        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(('', from_port))
            listener.listen(5)
            self.listeners[from_port] = listener
            threading.Thread(target=self.accept_connections,
                             args=(listener, rule), daemon=True).start()
        except Exception as e:
            print(f"Error starting listener on port {from_port}: {e}")

    def stop_listener(self, from_port):
        if from_port in self.listeners:
            listener = self.listeners.pop(from_port)
            listener.close()

    def accept_connections(self, listener, rule):
        while True:
            try:
                client_sock, addr = listener.accept()
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.connect((rule['to_ip'], rule['to_port']))
                threading.Thread(target=self.forward, args=(
                    client_sock, target_sock), daemon=True).start()
                threading.Thread(target=self.forward, args=(
                    target_sock, client_sock), daemon=True).start()
                self.active_connections.append((client_sock, target_sock))
            except:
                break

    def forward(self, source, destination):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)
        except:
            pass
        finally:
            source.close()
            destination.close()
            if (source, destination) in self.active_connections:
                self.active_connections.remove((source, destination))

    def monitor_config(self):
        while True:
            try:
                current_mtime = os.path.getmtime(self.config_file)
                if current_mtime != self.last_mtime:
                    self.load_config()
                    self.update_rules_gui()
                    self.last_mtime = current_mtime
                time.sleep(1)
            except:
                pass

    def update_rules_gui(self):
        for row in self.rules_tree.get_children():
            self.rules_tree.delete(row)
        for rule in self.rules:
            status = 'Active' if rule['from_port'] in self.listeners else 'Inactive'
            self.rules_tree.insert('', 'end', values=(
                rule['from_port'], rule['to_ip'], rule['to_port'], status))

    def reload_config(self):
        self.load_config()
        self.update_rules_gui()


if __name__ == "__main__":
    root = Tk()
    translator = PortTranslator(root)
    root.mainloop()
