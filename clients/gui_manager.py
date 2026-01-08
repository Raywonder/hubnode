#!/usr/bin/env python3
"""
CopyParty GUI Management Application
Cross-platform graphical interface for managing CopyParty directories and permissions
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Tuple
import subprocess
import platform

class CopyPartyGUIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CopyParty Management Console")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Configuration
        self.config_dir = Path.home() / ".copyparty_manager"
        self.config_dir.mkdir(exist_ok=True)
        self.db_path = self.config_dir / "manager.db"
        self.config_file = self.config_dir / "gui_config.json"

        # Initialize database
        self.init_database()

        # Load configuration
        self.config = self.load_config()

        # Initialize GUI
        self.create_widgets()
        self.refresh_data()

    def init_database(self):
        """Initialize SQLite database for GUI management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managed_directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                alias TEXT,
                permissions TEXT DEFAULT 'r',
                users TEXT,
                groups TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                auth_method TEXT,
                credentials TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                user TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def load_config(self) -> Dict:
        """Load GUI configuration"""
        default_config = {
            "server_host": "localhost",
            "server_port": 3923,
            "auto_refresh": True,
            "refresh_interval": 30,
            "theme": "default",
            "window_position": {"x": 100, "y": 100, "width": 900, "height": 700}
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except:
                pass

        return default_config

    def save_config(self):
        """Save GUI configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def create_widgets(self):
        """Create main GUI widgets"""
        # Create menu bar
        self.create_menu_bar()

        # Create main frame with notebook
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_directories_tab()
        self.create_users_tab()
        self.create_servers_tab()
        self.create_logs_tab()
        self.create_settings_tab()

        # Create status bar
        self.create_status_bar()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Configuration", command=self.import_config)
        file_menu.add_command(label="Export Configuration", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Server menu
        server_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Server", menu=server_menu)
        server_menu.add_command(label="Start CopyParty", command=self.start_server)
        server_menu.add_command(label="Stop CopyParty", command=self.stop_server)
        server_menu.add_command(label="Restart CopyParty", command=self.restart_server)
        server_menu.add_separator()
        server_menu.add_command(label="Generate Config", command=self.generate_config)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Open Web Interface", command=self.open_web_interface)
        tools_menu.add_command(label="Mount WebDAV", command=self.mount_webdav)
        tools_menu.add_command(label="Backup Configuration", command=self.backup_config)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)

    def create_directories_tab(self):
        """Create directories management tab"""
        dir_frame = ttk.Frame(self.notebook)
        self.notebook.add(dir_frame, text="Directories")

        # Toolbar
        toolbar = ttk.Frame(dir_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Add Directory", command=self.add_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Remove Directory", command=self.remove_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit Permissions", command=self.edit_permissions).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_directories).pack(side=tk.LEFT, padx=2)

        # Directories tree
        tree_frame = ttk.Frame(dir_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Path", "Alias", "Permissions", "Users", "Description")
        self.dir_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        for col in columns:
            self.dir_tree.heading(col, text=col)
            self.dir_tree.column(col, width=150)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dir_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.dir_tree.xview)
        self.dir_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.dir_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_users_tab(self):
        """Create users management tab"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="Users & Permissions")

        # User management interface
        ttk.Label(users_frame, text="User Management", font=("Arial", 14, "bold")).pack(pady=10)

        # User list
        user_list_frame = ttk.LabelFrame(users_frame, text="Current Users")
        user_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.user_listbox = tk.Listbox(user_list_frame)
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # User buttons
        user_btn_frame = ttk.Frame(users_frame)
        user_btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(user_btn_frame, text="Add User", command=self.add_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(user_btn_frame, text="Edit User", command=self.edit_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(user_btn_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=2)

    def create_servers_tab(self):
        """Create server configuration tab"""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="Server Config")

        # Server configuration form
        config_frame = ttk.LabelFrame(server_frame, text="Server Configuration")
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # Host
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.host_var = tk.StringVar(value=self.config.get("server_host", "localhost"))
        ttk.Entry(config_frame, textvariable=self.host_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        # Port
        ttk.Label(config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.port_var = tk.StringVar(value=str(self.config.get("server_port", 3923)))
        ttk.Entry(config_frame, textvariable=self.port_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        # Authentication method
        ttk.Label(config_frame, text="Auth Method:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.auth_var = tk.StringVar(value="local")
        auth_combo = ttk.Combobox(config_frame, textvariable=self.auth_var,
                                 values=["local", "whmcs", "ldap", "oauth", "api_key"])
        auth_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)

        config_frame.columnconfigure(1, weight=1)

        # Control buttons
        control_frame = ttk.Frame(server_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(control_frame, text="Save Configuration", command=self.save_server_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)

    def create_logs_tab(self):
        """Create logs viewing tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Access Logs")

        # Log viewer
        log_text_frame = ttk.Frame(logs_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_text_frame, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(log_controls, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Export Logs", command=self.export_logs).pack(side=tk.LEFT, padx=5)

    def create_settings_tab(self):
        """Create application settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # General settings
        general_frame = ttk.LabelFrame(settings_frame, text="General Settings")
        general_frame.pack(fill=tk.X, padx=10, pady=10)

        # Auto-refresh
        self.auto_refresh_var = tk.BooleanVar(value=self.config.get("auto_refresh", True))
        ttk.Checkbutton(general_frame, text="Auto-refresh data",
                       variable=self.auto_refresh_var).pack(anchor=tk.W, padx=5, pady=2)

        # Refresh interval
        ttk.Label(general_frame, text="Refresh interval (seconds):").pack(anchor=tk.W, padx=5, pady=2)
        self.refresh_interval_var = tk.StringVar(value=str(self.config.get("refresh_interval", 30)))
        ttk.Entry(general_frame, textvariable=self.refresh_interval_var, width=10).pack(anchor=tk.W, padx=5, pady=2)

        # Apply settings button
        ttk.Button(settings_frame, text="Apply Settings", command=self.apply_settings).pack(pady=10)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Connection status
        self.connection_label = ttk.Label(self.status_bar, text="Disconnected", foreground="red")
        self.connection_label.pack(side=tk.RIGHT, padx=5)

    def refresh_data(self):
        """Refresh all data displays"""
        self.refresh_directories()
        self.refresh_users()
        self.refresh_logs()
        self.update_connection_status()

    def refresh_directories(self):
        """Refresh directories tree view"""
        # Clear existing items
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)

        # Load from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT path, alias, permissions, users, description
            FROM managed_directories
            ORDER BY path
        ''')

        for row in cursor.fetchall():
            self.dir_tree.insert("", tk.END, values=row)

        conn.close()

    def refresh_users(self):
        """Refresh users list"""
        self.user_listbox.delete(0, tk.END)
        # This would connect to the actual user management system
        # For now, showing placeholder users
        users = ["admin", "devinecr", "tappedin", "dom", "guest"]
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def refresh_logs(self):
        """Refresh access logs"""
        self.log_text.delete(1.0, tk.END)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, action, target, user, details
            FROM access_logs
            ORDER BY timestamp DESC
            LIMIT 1000
        ''')

        for row in cursor.fetchall():
            timestamp, action, target, user, details = row
            log_entry = f"[{timestamp}] {action}: {target} (User: {user or 'system'})\n"
            if details:
                log_entry += f"    Details: {details}\n"
            self.log_text.insert(tk.END, log_entry)

        conn.close()

    def update_connection_status(self):
        """Update server connection status"""
        try:
            # Test connection to CopyParty server
            import urllib.request
            import urllib.error

            host = self.config.get("server_host", "localhost")
            port = self.config.get("server_port", 3923)
            url = f"http://{host}:{port}/"

            req = urllib.request.Request(url)
            urllib.request.urlopen(req, timeout=5)

            self.connection_label.config(text="Connected", foreground="green")
        except:
            self.connection_label.config(text="Disconnected", foreground="red")

    def add_directory(self):
        """Add new directory to CopyParty"""
        dialog = DirectoryDialog(self.root, "Add Directory")
        if dialog.result:
            path, alias, permissions, users, description = dialog.result

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO managed_directories (path, alias, permissions, users, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (path, alias, permissions, users, description))
                conn.commit()

                # Log the action
                self.log_action("ADD_DIRECTORY", path, details=f"Alias: {alias}, Permissions: {permissions}")

                self.refresh_directories()
                self.status_label.config(text=f"Added directory: {path}")

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Directory already exists in management")
            finally:
                conn.close()

    def remove_directory(self):
        """Remove directory from CopyParty"""
        selection = self.dir_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a directory to remove")
            return

        item = self.dir_tree.item(selection[0])
        path = item['values'][0]

        if messagebox.askyesno("Confirm", f"Remove directory '{path}' from CopyParty?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM managed_directories WHERE path = ?', (path,))
            conn.commit()
            conn.close()

            self.log_action("REMOVE_DIRECTORY", path)
            self.refresh_directories()
            self.status_label.config(text=f"Removed directory: {path}")

    def edit_permissions(self):
        """Edit directory permissions"""
        selection = self.dir_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a directory to edit")
            return

        item = self.dir_tree.item(selection[0])
        current_data = item['values']

        dialog = DirectoryDialog(self.root, "Edit Directory", current_data)
        if dialog.result:
            path, alias, permissions, users, description = dialog.result

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE managed_directories
                SET alias=?, permissions=?, users=?, description=?, last_modified=CURRENT_TIMESTAMP
                WHERE path=?
            ''', (alias, permissions, users, description, path))
            conn.commit()
            conn.close()

            self.log_action("EDIT_DIRECTORY", path, details=f"Updated permissions: {permissions}")
            self.refresh_directories()
            self.status_label.config(text=f"Updated directory: {path}")

    def log_action(self, action: str, target: str, user: str = None, details: str = None):
        """Log an action to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO access_logs (action, target, user, details)
            VALUES (?, ?, ?, ?)
        ''', (action, target, user or "gui_user", details))
        conn.commit()
        conn.close()

    def start_server(self):
        """Start CopyParty server"""
        try:
            system = platform.system().lower()
            if system == "windows":
                subprocess.Popen(["python", "copyparty_manager.py", "start"],
                               cwd=Path(__file__).parent, shell=True)
            else:
                subprocess.Popen(["python3", "copyparty_manager.py", "start"],
                               cwd=Path(__file__).parent)
            self.status_label.config(text="Starting CopyParty server...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")

    def stop_server(self):
        """Stop CopyParty server"""
        try:
            system = platform.system().lower()
            if system == "windows":
                subprocess.run(["python", "copyparty_manager.py", "stop"],
                              cwd=Path(__file__).parent, shell=True)
            else:
                subprocess.run(["python3", "copyparty_manager.py", "stop"],
                              cwd=Path(__file__).parent)
            self.status_label.config(text="CopyParty server stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")

    def restart_server(self):
        """Restart CopyParty server"""
        self.stop_server()
        self.root.after(2000, self.start_server)  # Wait 2 seconds before starting

    def open_web_interface(self):
        """Open CopyParty web interface in browser"""
        import webbrowser
        host = self.config.get("server_host", "localhost")
        port = self.config.get("server_port", 3923)
        url = f"http://{host}:{port}/"
        webbrowser.open(url)

    def mount_webdav(self):
        """Mount CopyParty as WebDAV drive"""
        system = platform.system().lower()
        host = self.config.get("server_host", "localhost")
        port = self.config.get("server_port", 3923)
        url = f"http://{host}:{port}/"

        try:
            if system == "darwin":  # macOS
                subprocess.run(["open", url])
            elif system == "windows":
                subprocess.run(["explorer", url])
            else:  # Linux
                messagebox.showinfo("WebDAV Mount",
                                   f"Mount URL: {url}\nUse your file manager to connect to this WebDAV URL")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mount WebDAV: {e}")

    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self.root, "Add User")
        if dialog.result:
            username, password, permissions = dialog.result
            # This would integrate with the actual user management system
            messagebox.showinfo("Success", f"User '{username}' would be added")
            self.refresh_users()

    def edit_user(self):
        """Edit selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return

        username = self.user_listbox.get(selection[0])
        dialog = UserDialog(self.root, "Edit User", username)
        if dialog.result:
            messagebox.showinfo("Success", f"User '{username}' would be updated")
            self.refresh_users()

    def delete_user(self):
        """Delete selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return

        username = self.user_listbox.get(selection[0])
        if messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            messagebox.showinfo("Success", f"User '{username}' would be deleted")
            self.refresh_users()

    def save_server_config(self):
        """Save server configuration"""
        self.config["server_host"] = self.host_var.get()
        self.config["server_port"] = int(self.port_var.get())
        self.save_config()
        self.status_label.config(text="Server configuration saved")

    def test_connection(self):
        """Test connection to CopyParty server"""
        self.update_connection_status()

    def apply_settings(self):
        """Apply application settings"""
        self.config["auto_refresh"] = self.auto_refresh_var.get()
        self.config["refresh_interval"] = int(self.refresh_interval_var.get())
        self.save_config()
        self.status_label.config(text="Settings applied")

    def generate_config(self):
        """Generate CopyParty configuration"""
        messagebox.showinfo("Info", "Configuration generation would be implemented here")

    def import_config(self):
        """Import configuration from file"""
        filename = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Info", f"Configuration import from {filename} would be implemented")

    def export_config(self):
        """Export configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Info", f"Configuration export to {filename} would be implemented")

    def backup_config(self):
        """Backup current configuration"""
        messagebox.showinfo("Info", "Configuration backup would be implemented here")

    def clear_logs(self):
        """Clear access logs"""
        if messagebox.askyesno("Confirm", "Clear all access logs?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM access_logs')
            conn.commit()
            conn.close()
            self.refresh_logs()

    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Logs exported to {filename}")

    def show_documentation(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", "Documentation would open here")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About",
                           "CopyParty GUI Manager v1.0\n"
                           "Cross-platform management interface for CopyParty\n\n"
                           "🤖 Generated with Claude Code")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


class DirectoryDialog:
    def __init__(self, parent, title, current_data=None):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.create_widgets(current_data)

    def create_widgets(self, current_data):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Path selection
        ttk.Label(main_frame, text="Directory Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=0, column=1, sticky=tk.EW, pady=2)

        self.path_var = tk.StringVar(value=current_data[0] if current_data else "")
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse", command=self.browse_directory).pack(side=tk.RIGHT, padx=(5, 0))

        # Alias
        ttk.Label(main_frame, text="Alias:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.alias_var = tk.StringVar(value=current_data[1] if current_data else "")
        ttk.Entry(main_frame, textvariable=self.alias_var).grid(row=1, column=1, sticky=tk.EW, pady=2)

        # Permissions
        ttk.Label(main_frame, text="Permissions:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.permissions_var = tk.StringVar(value=current_data[2] if current_data else "r")
        perm_combo = ttk.Combobox(main_frame, textvariable=self.permissions_var,
                                 values=["r", "rw", "rwx", "admin"])
        perm_combo.grid(row=2, column=1, sticky=tk.EW, pady=2)

        # Users
        ttk.Label(main_frame, text="Allowed Users:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.users_var = tk.StringVar(value=current_data[3] if current_data else "")
        ttk.Entry(main_frame, textvariable=self.users_var).grid(row=3, column=1, sticky=tk.EW, pady=2)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky=tk.NW, pady=2)
        self.description_text = tk.Text(main_frame, height=4, width=40)
        self.description_text.grid(row=4, column=1, sticky=tk.EW, pady=2)
        if current_data and len(current_data) > 4:
            self.description_text.insert(1.0, current_data[4] or "")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def browse_directory(self):
        """Browse for directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def ok_clicked(self):
        """Handle OK button click"""
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please specify a directory path")
            return

        self.result = (
            path,
            self.alias_var.get().strip(),
            self.permissions_var.get(),
            self.users_var.get().strip(),
            self.description_text.get(1.0, tk.END).strip()
        )
        self.dialog.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.dialog.destroy()


class UserDialog:
    def __init__(self, parent, title, username=None):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.create_widgets(username)

    def create_widgets(self, username):
        """Create user dialog widgets"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Username
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value=username or "")
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var)
        username_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        if username:
            username_entry.config(state="disabled")

        # Password
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky=tk.EW, pady=2)

        # Permissions
        ttk.Label(main_frame, text="Permissions:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.permissions_var = tk.StringVar(value="user")
        perm_combo = ttk.Combobox(main_frame, textvariable=self.permissions_var,
                                 values=["user", "admin", "readonly"])
        perm_combo.grid(row=2, column=1, sticky=tk.EW, pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def ok_clicked(self):
        """Handle OK button click"""
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username:
            messagebox.showerror("Error", "Please specify a username")
            return

        if not password:
            messagebox.showerror("Error", "Please specify a password")
            return

        self.result = (username, password, self.permissions_var.get())
        self.dialog.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.dialog.destroy()


if __name__ == "__main__":
    app = CopyPartyGUIManager()
    app.run()