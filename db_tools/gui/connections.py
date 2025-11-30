import uuid
import tomllib
from pathlib import Path
from tkinter import messagebox
import customtkinter
import tomli_w
from ..extras import find_root_dir, get_available_connections
from ..security import SecurityManager


class ConnectionsWindow(customtkinter.CTkToplevel):
    def __init__(self: "ConnectionsWindow", master):
        super().__init__(master)
        self.master = master
        self.title("Manage Connections")
        self.geometry("800x600")
        self.connections = get_available_connections()
        self.connections_path = find_root_dir(
            ["pyproject.toml"]
        ) / "config" / "database" / "connections"
        self.security_manager = SecurityManager()
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both")
        self.connections_tab = self.tab_view.add("Connections")
        self.add_edit_tab = self.tab_view.add("Add/Edit")
        self._create_connections_tab()
        self._create_add_edit_tab()

    def _create_connections_tab(self: "ConnectionsWindow"):
        self.connections_tab.grid_columnconfigure(1, weight=1)
        self.connections_tab.grid_rowconfigure(0, weight=1)
        self.connection_list_frame = customtkinter.CTkScrollableFrame(
            self.connections_tab,
            label_text="Connections",
            width=250,
        )
        self.connection_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        self.connection_buttons = []
        self._refresh_connection_list()
        self.connection_details_frame = customtkinter.CTkFrame(self.connections_tab)
        self.connection_details_frame.grid(
            row=0, column=1, padx=10, pady=10, sticky="nsew"
        )
        self.connection_details_frame.grid_columnconfigure(0, weight=1)

    def _create_add_edit_tab(self: "ConnectionsWindow"):
        self.add_edit_tab.grid_columnconfigure(0, weight=1)
        self.add_edit_tab.grid_rowconfigure(0, weight=1)
        self.form_frame = customtkinter.CTkFrame(self.add_edit_tab)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.form_frame.grid_columnconfigure(1, weight=1)
        # Display Name
        self.name_label = customtkinter.CTkLabel(self.form_frame, text="Display Name:")
        self.name_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = customtkinter.CTkEntry(self.form_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        # Staging Host
        self.staging_host_label = customtkinter.CTkLabel(
            self.form_frame, text="Staging Host:"
        )
        self.staging_host_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.staging_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.staging_host_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        # Production Host
        self.production_host_label = customtkinter.CTkLabel(
            self.form_frame, text="Production Host:"
        )
        self.production_host_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.production_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.production_host_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        # Replica Host
        self.replica_host_label = customtkinter.CTkLabel(
            self.form_frame, text="Replica Host:"
        )
        self.replica_host_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.replica_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.replica_host_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        # Port
        self.port_label = customtkinter.CTkLabel(self.form_frame, text="Port:")
        self.port_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.port_entry = customtkinter.CTkEntry(self.form_frame)
        self.port_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        # Database
        self.database_label = customtkinter.CTkLabel(self.form_frame, text="Database:")
        self.database_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.database_entry = customtkinter.CTkEntry(self.form_frame)
        self.database_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
        # Username
        self.username_label = customtkinter.CTkLabel(self.form_frame, text="Username:")
        self.username_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = customtkinter.CTkEntry(self.form_frame)
        self.username_entry.grid(row=6, column=1, padx=10, pady=10, sticky="ew")
        # Password
        self.password_label = customtkinter.CTkLabel(self.form_frame, text="Password:")
        self.password_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = customtkinter.CTkEntry(self.form_frame, show="*")
        self.password_entry.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
        # Save Button
        self.save_button = customtkinter.CTkButton(
            self.form_frame, text="Save", command=self._save_connection
        )
        self.save_button.grid(row=8, column=0, columnspan=2, padx=10, pady=20)
        self.connection_name = None

    def _refresh_connection_list(self: "ConnectionsWindow"):
        self.connections = get_available_connections()
        for button in self.connection_buttons:
            button.destroy()
        self.connection_buttons = []
        for toml_file in self.connections_path.glob("*.toml"):
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
                conn_key = list(data.get("connections", {}).keys())[0]
                display_name = (
                    data.get("connections", {})
                    .get(conn_key, {})
                    .get("name", toml_file.stem)
                )
                btn = customtkinter.CTkButton(
                    self.connection_list_frame,
                    text=display_name,
                    command=lambda c=display_name: self._show_connection_details(c),
                )
                btn.pack(fill="x", padx=5, pady=5)
                self.connection_buttons.append(btn)
        self.master._update_connection_list()

    def _get_filename_from_display_name(self, display_name: str) -> str | None:
        for toml_file in self.connections_path.glob("*.toml"):
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
                conn_key = list(data.get("connections", {}).keys())[0]
                if (
                    data.get("connections", {})
                    .get(conn_key, {})
                    .get("name") == display_name
                ):
                    return toml_file.stem
        return None

    def _show_connection_details(self: "ConnectionsWindow", connection_name: str):
        for widget in self.connection_details_frame.winfo_children():
            widget.destroy()

        filename = self._get_filename_from_display_name(connection_name)
        if not filename:
            details_label = customtkinter.CTkLabel(
                self.connection_details_frame,
                text=f"Connection '{connection_name}' not found.",
                font=customtkinter.CTkFont(size=16),
            )
            details_label.grid(row=0, column=0, padx=20, pady=20)
            return

        with open(self.connections_path / f"{filename}.toml", "rb") as f:
            config = tomllib.load(f)

        details_text = f"Details for {connection_name}\n\n"
        conn_details = config["connections"][filename]
        details_text += f"Type: {conn_details.get('type', 'N/A')}\n"
        details_text += f"Port: {conn_details.get('port', 'N/A')}\n"
        details_text += f"Database: {conn_details.get('database', 'N/A')}\n"
        details_text += f"Username: {conn_details.get('username', 'N/A')}\n"
        if "staging" in conn_details:
            details_text += (
                f"Staging Host: {conn_details['staging'].get('host', 'N/A')}\n"
            )
        if "production" in conn_details:
            details_text += (
                f"Production Host: {conn_details['production'].get('host', 'N/A')}\n"
            )
        if "replica" in conn_details:
            details_text += (
                f"Replica Host: {conn_details['replica'].get('host', 'N/A')}\n"
            )
        details_label = customtkinter.CTkLabel(
            self.connection_details_frame,
            text=details_text,
            justify="left",
        )
        details_label.pack(pady=10, padx=10, anchor="w")
        edit_button = customtkinter.CTkButton(
            self.connection_details_frame,
            text="Edit",
            command=lambda: self._edit_connection(connection_name),
        )
        edit_button.pack(pady=10)
        remove_button = customtkinter.CTkButton(
            self.connection_details_frame,
            text="Remove",
            command=lambda: self._remove_connection(connection_name),
            fg_color="red",
        )
        remove_button.pack(pady=10)

    def _edit_connection(self: "ConnectionsWindow", connection_name: str):
        self.tab_view.set("Add/Edit")
        filename = self._get_filename_from_display_name(connection_name)
        if not filename:
            messagebox.showerror("Error", f"Could not load connection '{connection_name}'.")
            return

        self.connection_name = filename
        with open(self.connections_path / f"{filename}.toml", "rb") as f:
            config = tomllib.load(f)
        conn_details = config["connections"][filename]
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, conn_details.get("name", ""))
        self.staging_host_entry.delete(0, "end")
        self.staging_host_entry.insert(
            0, conn_details.get("staging", {}).get("host", "")
        )
        self.production_host_entry.delete(0, "end")
        self.production_host_entry.insert(
            0, conn_details.get("production", {}).get("host", "")
        )
        self.replica_host_entry.delete(0, "end")
        self.replica_host_entry.insert(
            0, conn_details.get("replica", {}).get("host", "")
        )
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, str(conn_details.get("port", "")))
        self.database_entry.delete(0, "end")
        self.database_entry.insert(0, conn_details.get("database", ""))
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, conn_details.get("username", ""))
        self.password_entry.delete(0, "end")

    def _remove_connection(self: "ConnectionsWindow", connection_name: str):
        filename = self._get_filename_from_display_name(connection_name)
        if not filename:
            messagebox.showerror("Error", f"Connection '{connection_name}' not found.")
            return

        if messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to remove the connection '{connection_name}'?",
        ):
            try:
                (self.connections_path / f"{filename}.toml").unlink()
                self._refresh_connection_list()
                for widget in self.connection_details_frame.winfo_children():
                    widget.destroy()
                messagebox.showinfo(
                    "Success", f"Connection '{connection_name}' removed."
                )
            except FileNotFoundError:
                messagebox.showerror(
                    "Error", f"Connection '{connection_name}' not found."
                )

    def _save_connection(self: "ConnectionsWindow"):
        display_name = self.name_entry.get()
        staging_host = self.staging_host_entry.get()
        production_host = self.production_host_entry.get()
        replica_host = self.replica_host_entry.get()
        port = self.port_entry.get()
        database = self.database_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.connection_name is None:
            self.connection_name = str(uuid.uuid4())

        if not any([staging_host, production_host, replica_host]):
            messagebox.showerror("Error", "At least one host must be provided.")
            return
        if not all([display_name, port, database, username]):
            messagebox.showerror(
                "Error",
                "Display name, port, database, and username are required.",
            )
            return
        connection_data = {
            "connections": {
                self.connection_name: {
                    "name": display_name,
                    "type": "postgresql",
                    "port": int(port),
                    "database": database,
                    "username": username,
                }
            }
        }
        if staging_host:
            connection_data["connections"][self.connection_name]["staging"] = {
                "host": staging_host
            }
        if production_host:
            connection_data["connections"][self.connection_name]["production"] = {
                "host": production_host
            }
        if replica_host:
            connection_data["connections"][self.connection_name]["replica"] = {
                "host": replica_host
            }
        if password:
            encrypted_password = self.security_manager.encrypt_password(password)
            connection_data["connections"][self.connection_name][
                "password"
            ] = encrypted_password
        file_path = self.connections_path / f"{self.connection_name}.toml"
        try:
            with open(file_path, "wb") as f:
                tomli_w.dump(connection_data, f)
            messagebox.showinfo("Success", f"Connection '{display_name}' saved.")
            self._refresh_connection_list()
            self.tab_view.set("Connections")
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save connection: {e}")

    def _clear_form(self: "ConnectionsWindow"):
        self.name_entry.configure(state="normal")
        self.name_entry.delete(0, "end")
        self.staging_host_entry.delete(0, "end")
        self.production_host_entry.delete(0, "end")
        self.replica_host_entry.delete(0, "end")
        self.port_entry.delete(0, "end")
        self.database_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.connection_name = None
