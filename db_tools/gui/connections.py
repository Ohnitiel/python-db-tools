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
        self.locale_config = self.master.locale_config
        self.title(self.locale_config.window.connections)
        
        window_width = 800
        window_height = 600

        parent_x = master.winfo_x()
        parent_y = master.winfo_y()
        parent_width = master.winfo_width()
        parent_height = master.winfo_height()

        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.connections = get_available_connections()
        self.connections_path = find_root_dir(
            ["pyproject.toml"]
        ) / "config" / "database" / "connections"
        self.security_manager = SecurityManager()

        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both")

        self.connections_tab = self.tab_view.add(self.locale_config.labels.connections)
        self.add_edit_tab = self.tab_view.add(self.locale_config.labels.add_edit)

        self._create_connections_tab()
        self._create_add_edit_tab()

    def _create_connections_tab(self: "ConnectionsWindow"):
        self.connections_tab.grid_columnconfigure(1, weight=1)
        self.connections_tab.grid_rowconfigure(0, weight=1)

        self.connection_list_frame = customtkinter.CTkScrollableFrame(
            self.connections_tab,
            label_text=self.locale_config.labels.connections,
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
        self.name_label = customtkinter.CTkLabel(self.form_frame, text=f"{self.locale_config.labels.display_name}:")
        self.name_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = customtkinter.CTkEntry(self.form_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Staging Host
        self.staging_host_label = customtkinter.CTkLabel(
            self.form_frame, text=f"{self.locale_config.environments.staging}:"
        )
        self.staging_host_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.staging_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.staging_host_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Production Host
        self.production_host_label = customtkinter.CTkLabel(
            self.form_frame, text=f"{self.locale_config.environments.production}:"
        )
        self.production_host_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.production_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.production_host_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Replica Host
        self.replica_host_label = customtkinter.CTkLabel(
            self.form_frame, text=f"{self.locale_config.environments.replica}:"
        )
        self.replica_host_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.replica_host_entry = customtkinter.CTkEntry(self.form_frame)
        self.replica_host_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        # Port
        self.port_label = customtkinter.CTkLabel(self.form_frame, text=f"{self.locale_config.labels.port}:")
        self.port_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.port_entry = customtkinter.CTkEntry(self.form_frame)
        self.port_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # Database
        self.database_label = customtkinter.CTkLabel(self.form_frame, text=f"{self.locale_config.labels.database}:")
        self.database_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.database_entry = customtkinter.CTkEntry(self.form_frame)
        self.database_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        # Username
        self.username_label = customtkinter.CTkLabel(self.form_frame, text=f"{self.locale_config.labels.username}:")
        self.username_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = customtkinter.CTkEntry(self.form_frame)
        self.username_entry.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        # Password
        self.password_label = customtkinter.CTkLabel(self.form_frame, text=f"{self.locale_config.labels.password}:")
        self.password_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = customtkinter.CTkEntry(self.form_frame, show="*")
        self.password_entry.grid(row=7, column=1, padx=10, pady=10, sticky="ew")

        # Save Button
        self.save_button = customtkinter.CTkButton(
            self.form_frame, text=self.locale_config.labels.save, command=self._save_connection
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
        connection_not_found_details_text = self.locale_config.messages.connection_not_found.format(connection=connection_name)

        if not filename:
            details_label = customtkinter.CTkLabel(
                self.connection_details_frame,
                text=connection_not_found_details_text,
                font=customtkinter.CTkFont(size=16),
            )
            details_label.grid(row=0, column=0, padx=20, pady=20)
            return

        with open(self.connections_path / f"{filename}.toml", "rb") as f:
            config = tomllib.load(f)

        details_text = f"{self.locale_config.labels.details}: {connection_name}\n\n"
        conn_details = config["connections"][filename]
        details_text += f"{self.locale_config.labels.type}: {conn_details.get('type', 'N/A')}\n"
        details_text += f"{self.locale_config.labels.port}: {conn_details.get('port', 'N/A')}\n"
        details_text += f"{self.locale_config.labels.database}: {conn_details.get('database', 'N/A')}\n"
        details_text += f"{self.locale_config.labels.username}: {conn_details.get('username', 'N/A')}\n"

        if "staging" in conn_details:
            details_text += (
                f"{self.locale_config.environments.staging}: {conn_details['staging'].get('host', 'N/A')}\n"
            )
        if "production" in conn_details:
            details_text += (
                f"{self.locale_config.environments.production}: {conn_details['production'].get('host', 'N/A')}\n"
            )
        if "replica" in conn_details:
            details_text += (
                f"{self.locale_config.environments.replica}: {conn_details['replica'].get('host', 'N/A')}\n"
            )

        details_label = customtkinter.CTkLabel(
            self.connection_details_frame,
            text=details_text,
            justify="left",
        )
        details_label.pack(pady=10, padx=10, anchor="w")

        edit_button = customtkinter.CTkButton(
            self.connection_details_frame,
            text=self.locale_config.labels.edit,
            command=lambda: self._edit_connection(connection_name),
        )
        edit_button.pack(pady=10)

        remove_button = customtkinter.CTkButton(
            self.connection_details_frame,
            text=self.locale_config.labels.remove,
            command=lambda: self._remove_connection(connection_name),
            fg_color="red",
        )
        remove_button.pack(pady=10)

    def _edit_connection(self: "ConnectionsWindow", connection_name: str):
        self.tab_view.set(self.locale_config.labels.add_edit)

        filename = self._get_filename_from_display_name(connection_name)
        error_msg = self.locale_config.messages.connection_load_error.format(connection=connection_name)

        if not filename:
            messagebox.showerror(self.locale_config.messages.error, error_msg)
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
        error_msg = self.locale_config.messages.connection_not_found.format(connection=connection_name)

        if not filename:
            messagebox.showerror(self.locale_config.messages.error, error_msg)
            return

        confirm_msg = self.locale_config.messages.confirm_deletion_message.format(connection=connection_name)
        if messagebox.askyesno(
            self.locale_config.messages.confirm_deletion,
            confirm_msg,
        ):
            try:
                (self.connections_path / f"{filename}.toml").unlink()
                self._refresh_connection_list()
                for widget in self.connection_details_frame.winfo_children():
                    widget.destroy()
                success_msg = self.locale_config.messages.connection_removed.format(connection=connection_name)
                messagebox.showinfo(
                    self.locale_config.messages.success, success_msg
                )
            except FileNotFoundError:
                messagebox.showerror(
                    self.locale_config.messages.error, error_msg
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
            messagebox.showerror(self.locale_config.messages.error, self.locale_config.messages.at_least_one_host)
            return

        if not all([display_name, port, database, username]):
            messagebox.showerror(
                self.locale_config.messages.error,
                self.locale_config.messages.required_fields,
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
            success_msg = self.locale_config.messages.connection_saved.format(connection=display_name)
            messagebox.showinfo(self.locale_config.messages.success, success_msg)
            self._refresh_connection_list()
            self.tab_view.set(self.locale_config.labels.connections)
            self._clear_form()
        except Exception as e:
            error_msg = self.locale_config.messages.failed_to_save.format(error=e)
            messagebox.showerror(self.locale_config.messages.error, error_msg)

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
