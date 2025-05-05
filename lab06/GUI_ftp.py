import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from ftplib import FTP
import os
import tempfile

class FTPClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FTP Client")
        self.ftp = None
        self.current_path = ""
        
        # Connection frame
        self.conn_frame = ttk.Frame(root, padding=10)
        self.conn_frame.grid(row=0, column=0, sticky="ew")
        
        self.server_entry = ttk.Entry(self.conn_frame, width=20)
        self.server_entry.grid(row=0, column=1, padx=5)
        ttk.Label(self.conn_frame, text="Server:").grid(row=0, column=0)
        
        self.port_entry = ttk.Entry(self.conn_frame, width=6)
        self.port_entry.grid(row=0, column=3, padx=5)
        self.port_entry.insert(0, "21")
        ttk.Label(self.conn_frame, text="Port:").grid(row=0, column=2)
        
        self.user_entry = ttk.Entry(self.conn_frame, width=15)
        self.user_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(self.conn_frame, text="User:").grid(row=1, column=0)
        
        self.pass_entry = ttk.Entry(self.conn_frame, width=15, show="*")
        self.pass_entry.grid(row=1, column=3, padx=5)
        ttk.Label(self.conn_frame, text="Password:").grid(row=1, column=2)
        
        self.connect_btn = ttk.Button(self.conn_frame, text="Connect", 
                                    command=self.connect)
        self.connect_btn.grid(row=0, column=4, rowspan=2, padx=10)
        
        # File operations frame
        self.ops_frame = ttk.Frame(root, padding=10)
        self.ops_frame.grid(row=1, column=0, sticky="ew")
        
        self.crud_buttons = [
            ("Create", self.create_file),
            ("Retrieve", self.retrieve_file),
            ("Update", self.update_file),
            ("Delete", self.delete_file)
        ]
        
        for i, (text, cmd) in enumerate(self.crud_buttons):
            ttk.Button(self.ops_frame, text=text, command=cmd).grid(
                row=0, column=i, padx=5)
        
        # File list
        self.tree = ttk.Treeview(root, columns=("Size", "Type"), 
                               selectmode="browse")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.tree.heading("#0", text="Name")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Type", text="Type")
        
        self.tree.bind("<Double-1>", self.navigate_directory)
        
        # Content display
        self.content_text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.content_text.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Status bar
        self.status = ttk.Label(root, text="Not connected", 
                              relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=4, column=0, sticky="ew")
        
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
    def connect(self):
        try:
            self.ftp = FTP()
            self.ftp.connect(
                self.server_entry.get(),
                int(self.port_entry.get()))
            self.ftp.login(
                self.user_entry.get(),
                self.pass_entry.get())
            self.current_path = ""
            self.update_file_list()
            self.status.config(text="Connected successfully")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def update_file_list(self):
        if not self.ftp:
            return
        
        self.tree.delete(*self.tree.get_children())
        try:
            files = []
            self.ftp.retrlines('LIST', lambda x: files.append(x))
            
            for line in files:
                parts = line.split()
                if len(parts) < 6:
                    continue
                
                name = " ".join(parts[8:])
                ftype = "DIR" if parts[0].startswith("d") else "FILE"
                size = parts[4]
                
                self.tree.insert("", "end", text=name, 
                               values=(size, ftype), tags=(ftype,))
            
            self.tree.tag_configure("DIR", foreground="blue")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def navigate_directory(self, event):
        item = self.tree.selection()[0]
        name = self.tree.item(item, "text")
        ftype = self.tree.item(item, "values")[1]
        
        if ftype == "DIR":
            try:
                self.ftp.cwd(name)
                self.current_path = self.ftp.pwd()
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def create_file(self):
        self.edit_file_content(new_file=True)
    
    def update_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        self.edit_file_content()
    
    def edit_file_content(self, new_file=False):
        filename = ""
        content = ""
        
        if not new_file:
            item = self.tree.selection()[0]
            filename = self.tree.item(item, "text")
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    self.ftp.retrbinary(f"RETR {filename}", tmp.write)
                    tmp.seek(0)
                    content = tmp.read().decode()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit File" if not new_file else "Create File")
        
        text_area = scrolledtext.ScrolledText(edit_win, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content)
        
        def save_file():
            nonlocal filename
            if new_file:
                filename = filedialog.asksaveasfilename(
                    title="Enter filename",
                    initialdir="/",
                    filetypes=[("All files", "*.*")])
                if not filename:
                    return
                filename = os.path.basename(filename)
            
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(text_area.get("1.0", tk.END).encode())
                    tmp.seek(0)
                    self.ftp.storbinary(f"STOR {filename}", tmp)
                self.update_file_list()
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(edit_win, text="Save", command=save_file).pack(pady=5)
    
    def retrieve_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.selection()[0]
        filename = self.tree.item(item, "text")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                self.ftp.retrbinary(f"RETR {filename}", tmp.write)
                tmp.seek(0)
                content = tmp.read().decode()
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def delete_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.selection()[0]
        filename = self.tree.item(item, "text")
        ftype = self.tree.item(item, "values")[1]
        
        if messagebox.askyesno("Confirm", f"Delete {filename}?"):
            try:
                if ftype == "DIR":
                    self.ftp.rmd(filename)
                else:
                    self.ftp.delete(filename)
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = FTPClientApp(root)
    root.mainloop()