import threading
import tomllib
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter
import pandas as pd
from dotenv import load_dotenv

from db_tools.database.query_type import QueryType
from db_tools.database.runner import DBConnectionRunner
from db_tools.exporter import export_data
from db_tools.extras import Struct, find_root_dir, get_available_connections
from db_tools.gui.connections import ConnectionsWindow


class CustomMessageBox(customtkinter.CTkToplevel):
    def __init__(self, parent, title, message, yes_text="Yes", no_text="No"):
        super().__init__(parent)

        self.title(title)

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        self_width = 450
        self_height = 150

        x = parent_x + (parent_width // 2) - (self_width // 2)
        y = parent_y + (parent_height // 2) - (self_height // 2)

        self.geometry(f"{self_width}x{self_height}+{x}+{y}")
        self.lift()  # Lift window on top
        self.attributes("-topmost", True)  # Stay on top
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.grab_set()  # Make window modal

        self.result = None

        self.message_label = customtkinter.CTkLabel(self, text=message, wraplength=430)
        self.message_label.pack(padx=20, pady=20, expand=True, fill="both")

        self.buttons_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(pady=10)

        self.yes_button = customtkinter.CTkButton(
            self.buttons_frame, text=yes_text, command=self._yes_clicked
        )
        self.yes_button.pack(side="left", padx=10)

        self.no_button = customtkinter.CTkButton(
            self.buttons_frame, text=no_text, command=self._no_clicked
        )
        self.no_button.pack(side="right", padx=10)

    def _yes_clicked(self):
        self.result = True
        self.destroy()

    def _no_clicked(self):
        self.result = False
        self.destroy()

    def _on_closing(self):
        self.result = False
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.result


class App(customtkinter.CTk):
    def __init__(self: "App"):
        super().__init__()
        self._load_configuration()

        # Load environment variables from .env file
        try:
            load_dotenv(find_root_dir(["pyproject.toml"]) / ".env")
        except Exception as e:
            error_msg = self.locale_config.messages.load_env_error.format(error=e)
            print(error_msg)

        self.title(self.locale_config.app.title)

        window_width = 1280
        window_height = 800

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.results_df = None
        self.connections_window = None

        # --- Main Layout ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Make right column expandable

        # --- Left Panel ---
        self.left_frame = customtkinter.CTkFrame(self, width=350, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(
            3, weight=1
        )  # Make connection list expandable

        # --- Connection Selector ---
        self.connection_names = sorted(get_available_connections())

        self.conn_label = customtkinter.CTkLabel(
            self.left_frame,
            text=self.locale_config.labels.connections,
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.conn_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.conn_filter_entry = customtkinter.CTkEntry(
            self.left_frame,
            placeholder_text=f"{self.locale_config.placeholders.filter_connections}...",
        )
        self.conn_filter_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.conn_filter_entry.bind("<KeyRelease>", self._filter_connections)

        self.select_all_var = customtkinter.StringVar(value="off")
        self.select_all_checkbox = customtkinter.CTkCheckBox(
            self.left_frame,
            text=self.locale_config.labels.select_all_connections,
            variable=self.select_all_var,
            onvalue="on",
            offvalue="off",
            command=self._toggle_select_all,
        )
        self.select_all_checkbox.grid(
            row=2, column=0, padx=10, pady=(5, 0), sticky="w"
        )

        self.conn_list_frame = customtkinter.CTkScrollableFrame(
            self.left_frame, label_text=""
        )
        self.conn_list_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        self.conn_checkboxes = {}
        self._update_connection_list()

        # --- Options Frame ---
        self.options_frame = customtkinter.CTkFrame(
            self.left_frame, corner_radius=0, fg_color="transparent"
        )
        self.options_frame.grid(row=4, column=0, padx=10, pady=10, sticky="sew")
        self.options_frame.grid_columnconfigure(1, weight=1)

        # Environment
        self.env_label = customtkinter.CTkLabel(
            self.options_frame, text=self.locale_config.labels.environment
        )
        self.env_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        # Define the environment details including ID and locale key for translation
        environment_details = {
            "staging": {"id": 1, "locale_key_attr": "staging"},
            "production": {"id": 2, "locale_key_attr": "production"},
            "replica": {"id": 3, "locale_key_attr": "replica"},
        }

        self.env_display_to_key = {}  # Map display string to internal key
        dropdown_display_values = []

        # Determine the initial selected value key
        initial_env_key = "staging"  # Default to 'staging' as the internal key

        for key, details in environment_details.items():
            # Get localized display name (e.g., "Staging")
            localized_name = getattr(
                self.locale_config.environments, details["locale_key_attr"]
            )

            # Create the full display string (e.g., "ID 1: Staging")
            display_string = f"ID {details['id']}: {localized_name}"

            self.env_display_to_key[
                display_string
            ] = key  # Map display string to internal key
            dropdown_display_values.append(display_string)

            # Check if this is the initial environment, so we can set the dropdown correctly
            if key == initial_env_key:
                initial_display_value = display_string

        self.environment_var = customtkinter.StringVar(
            value=initial_env_key
        )  # Stores the internal key (e.g., "staging")

        # Callback function for when a dropdown item is selected
        def env_dropdown_callback(choice):
            # Update environment_var with the actual key from our mapping
            self.environment_var.set(self.env_display_to_key[choice])

        self.env_dropdown = customtkinter.CTkOptionMenu(
            self.options_frame,
            values=dropdown_display_values,
            command=env_dropdown_callback,  # Assign the callback
        )
        self.env_dropdown.set(
            initial_display_value
        )  # Set the displayed initial value
        self.env_dropdown.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")

        # Parallelism
        self.parallel_var = customtkinter.StringVar(value="on")
        self.parallel_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.labels.run_in_parallel,
            variable=self.parallel_var,
            onvalue="on",
            offvalue="off",
        )
        self.parallel_checkbox.grid(
            row=1, column=0, columnspan=2, padx=(0, 10), pady=5, sticky="w"
        )

        # Max Workers
        self.max_workers_label = customtkinter.CTkLabel(
            self.options_frame, text=f"{self.locale_config.labels.max_workers}:"
        )
        self.max_workers_label.grid(row=2, column=0, padx=(0, 5), pady=5, sticky="w")

        self.max_workers_var = customtkinter.StringVar(value="8")
        self.max_workers_entry = customtkinter.CTkEntry(
            self.options_frame, textvariable=self.max_workers_var
        )
        self.max_workers_entry.grid(row=2, column=1, padx=(0, 10), pady=5, sticky="ew")

        # Cache
        self.cache_var = customtkinter.StringVar(value="on")
        self.cache_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.cache.use,
            variable=self.cache_var,
            onvalue="on",
            offvalue="off",
        )
        self.cache_checkbox.grid(row=3, column=0, padx=(0, 10), pady=5, sticky="w")

        self.ignore_cache_var = customtkinter.StringVar(value="off")
        self.ignore_cache_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.labels.ignore_cache,
            variable=self.ignore_cache_var,
            onvalue="on",
            offvalue="off",
        )
        self.ignore_cache_checkbox.grid(
            row=3, column=1, padx=(0, 10), pady=5, sticky="w"
        )

        # Export
        self.output_format_label = customtkinter.CTkLabel(
            self.options_frame, text=f"{self.locale_config.labels.output_format}:"
        )
        self.output_format_label.grid(row=4, column=0, padx=(0, 5), pady=5, sticky="w")

        self.output_format_var = customtkinter.StringVar(value="xlsx")
        self.output_format_dropdown = customtkinter.CTkOptionMenu(
            self.options_frame,
            variable=self.output_format_var,
            values=["xlsx", "json", "csv"],
        )
        self.output_format_dropdown.grid(
            row=4, column=1, padx=(0, 10), pady=5, sticky="ew"
        )

        self.format_excel_var = customtkinter.StringVar(value="on")
        self.format_excel_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.labels.format_excel,
            variable=self.format_excel_var,
            onvalue="on",
            offvalue="off",
        )
        self.format_excel_checkbox.grid(
            row=5, column=0, columnspan=2, padx=(0, 10), pady=5, sticky="w"
        )

        self.single_sheet_var = customtkinter.StringVar(value="on")
        self.single_sheet_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.formats.single_sheet,
            variable=self.single_sheet_var,
            onvalue="on",
            offvalue="off",
        )
        self.single_sheet_checkbox.grid(
            row=6, column=0, padx=(0, 10), pady=5, sticky="w"
        )

        self.single_file_var = customtkinter.StringVar(value="on")
        self.single_file_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text=self.locale_config.formats.single_file,
            variable=self.single_file_var,
            onvalue="on",
            offvalue="off",
        )
        self.single_file_checkbox.grid(
            row=6, column=1, padx=(0, 10), pady=5, sticky="w"
        )

        self.connection_column_label = customtkinter.CTkLabel(
            self.options_frame,
            text=f"{self.locale_config.labels.connection_column}:",
        )
        self.connection_column_label.grid(
            row=7, column=0, padx=(0, 5), pady=5, sticky="w"
        )

        self.connection_column_var = customtkinter.StringVar(
            value=self.locale_config.placeholders.connection_column_name
        )
        self.connection_column_entry = customtkinter.CTkEntry(
            self.options_frame, textvariable=self.connection_column_var
        )
        self.connection_column_entry.grid(
            row=7, column=1, padx=(0, 10), pady=5, sticky="ew"
        )

        # --- Commit Checkbox & Run Button ---
        self.bottom_frame = customtkinter.CTkFrame(
            self.left_frame, corner_radius=0, fg_color="transparent"
        )
        self.bottom_frame.grid(row=5, column=0, padx=10, pady=10, sticky="sew")
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        self.commit_var = customtkinter.StringVar(value="off")
        self.commit_checkbox = customtkinter.CTkCheckBox(
            self.bottom_frame,
            text=self.locale_config.labels.commit,
            variable=self.commit_var,
            onvalue="on",
            offvalue="off",
        )
        self.commit_checkbox.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")

        self.manage_connections_button = customtkinter.CTkButton(
            self.bottom_frame,
            text=self.locale_config.labels.manage_connections,
            command=self._open_connections_window,
        )
        self.manage_connections_button.grid(
            row=0, column=1, padx=(10, 0), pady=10, sticky="w"
        )

        self.run_button = customtkinter.CTkButton(
            self.bottom_frame,
            text=self.locale_config.labels.run_query,
            command=self._run_query_callback,
        )
        self.run_button.grid(row=0, column=2, padx=(10, 0), pady=10, sticky="e")

        # --- Right Panel (Query and Results) ---
        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_rowconfigure(
            1, weight=1
        )  # Make results table expandable
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.query_box = customtkinter.CTkTextbox(
            self.right_frame, height=150, border_width=2, font=("Consolas", 12)
        )
        self.query_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.query_box.insert("1.0", self.locale_config.placeholders.query_input)

        self._create_results_table()

        self.save_button = customtkinter.CTkButton(
            self.right_frame,
            text=self.locale_config.labels.save_results,
            command=self._save_results,
            state="disabled",
        )
        self.save_button.grid(row=2, column=0, padx=5, pady=5, sticky="e")

    def _ask_yes_no_custom(self, title, message):
        dialog = CustomMessageBox(
            self,
            title,
            message,
            yes_text=self.locale_config.buttons.yes,
            no_text=self.locale_config.buttons.no,
        )
        return dialog.get_input()

    def _load_configuration(self: "App"):
        root = find_root_dir(["pyproject.toml"])
        config_path = Path(root) / "config/config.toml"
        with open(config_path, "rb") as f:
            config = Struct(tomllib.load(f))

        locale = config.locale
        locale_config_path = Path(root) / f"config/locales/{locale}.toml"
        with open(locale_config_path, "rb") as f:
            self.locale_config = Struct(tomllib.load(f))

    def _open_connections_window(self: "App"):
        if (
            self.connections_window is None
            or not self.connections_window.winfo_exists()
        ):
            self.connections_window = ConnectionsWindow(
                self
            )  # create window if its None or destroyed
        self.connections_window.focus()

    def _browse_save_path(self: "App"):
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=(
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ),
        )
        if filename:
            self.save_path_var.set(filename)

    def _create_results_table(self: "App"):
        """Creates the results Treeview table and scrollbars."""
        style = ttk.Style(self)
        style.theme_use("default")

        table_frame = customtkinter.CTkFrame(self.right_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.results_table = ttk.Treeview(table_frame, show="headings")

        vsb = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.results_table.yview
        )
        vsb.grid(row=0, column=1, sticky="ns")

        hsb = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.results_table.xview
        )
        hsb.grid(row=1, column=0, sticky="ew")

        self.results_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.results_table.grid(row=0, column=0, sticky="nsew")

    def _update_connection_list(self: "App", filter_text=""):
        checked_connections = {
            name for name, var in self.conn_checkboxes.items() if var.get() == "on"
        }

        for widget in self.conn_list_frame.winfo_children():
            widget.destroy()

        self.conn_checkboxes = {}

        visible_conns = [
            c for c in self.connection_names if filter_text.lower() in c.lower()
        ]

        for i, conn_name in enumerate(visible_conns):
            var = customtkinter.StringVar(
                value="on" if conn_name in checked_connections else "off"
            )
            cb = customtkinter.CTkCheckBox(
                self.conn_list_frame,
                text=conn_name,
                variable=var,
                onvalue="on",
                offvalue="off",
            )
            cb.grid(row=i, column=0, padx=10, pady=(5, 0), sticky="w")
            self.conn_checkboxes[conn_name] = var

    def _filter_connections(self: "App", event=None):
        self._update_connection_list(self.conn_filter_entry.get())
        self.select_all_var.set("off")

    def _toggle_select_all(self: "App"):
        new_state = self.select_all_var.get()
        for var in self.conn_checkboxes.values():
            var.set(new_state)

    def _run_query_callback(self: "App"):
        selected_connections = [
            name for name, var in self.conn_checkboxes.items() if var.get() == "on"
        ]
        if not selected_connections:
            messagebox.showwarning(
                self.locale_config.messages.no_connections,
                self.locale_config.messages.select_connection,
            )
            return

        query = self.query_box.get("1.0", "end").strip()
        print(query)
        if not query or query.startswith("--"):
            messagebox.showwarning(
                self.locale_config.messages.enter_query,
                self.locale_config.messages.enter_query,
            )
            return

        commit_mode = self.commit_var.get() == "on"

        try:
            # Using a temp runner to verify query type.
            # The actual runner is created in the worker thread.
            temp_runner = DBConnectionRunner(environment=self.environment_var.get())
            query_type = temp_runner.verify_query_type(query)
            temp_runner.close_all()
        except ValueError as e:
            messagebox.showerror("Invalid Query", str(e))
            return

        if commit_mode and query_type != QueryType.DQL:
            if not self._ask_yes_no_custom(
                self.locale_config.confirmation.title1,
                self.locale_config.confirmation.message1,
            ):
                return
            if not self._ask_yes_no_custom(
                self.locale_config.confirmation.title2,
                self.locale_config.confirmation.message2,
            ):
                return
            if not self._ask_yes_no_custom(
                self.locale_config.confirmation.title3,
                self.locale_config.confirmation.message3,
            ):
                return

        self.run_button.configure(
            state="disabled", text=f"{self.locale_config.labels.running}..."
        )
        self.save_button.configure(state="disabled")
        self.results_df = None

        # Clear previous results
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        self.results_table["columns"] = []

        # Run the database query in a background thread
        thread = threading.Thread(
            target=self._execute_query_worker,
            args=(selected_connections, query, commit_mode),
        )
        thread.daemon = True
        thread.start()

    def _execute_query_worker(self: "App", connections, query, commit_mode):
        """Worker function to be run in a separate thread."""
        try:
            use_cache_callback = lambda: self._ask_yes_no_custom(
                self.locale_config.cache.found_title,
                self.locale_config.cache.found_message,
            )
            runner = DBConnectionRunner(
                environment=self.environment_var.get(),
                connections=connections,
                max_workers=int(self.max_workers_var.get()),
            )
            results_df = runner.execute_query_multi_db(
                query=query,
                commit=commit_mode,
                parallel=self.parallel_var.get() == "on",
                add_connection_column=True
                if self.connection_column_var.get()
                else False,
                connection_column_name=self.connection_column_var.get(),
                cache=self.cache_var.get() == "on",
                ignore_cache=self.ignore_cache_var.get() == "on",
                use_cache_callback=use_cache_callback,
            )
            self.after(0, self._update_ui_after_query, results_df)
        except Exception as e:
            self.after(0, self._update_ui_after_query, e)

    def _update_ui_after_query(self: "App", result):
        """Receives results from worker thread and updates UI. Runs in main thread."""
        self.run_button.configure(
            state="normal", text=self.locale_config.labels.run_query
        )

        if isinstance(result, Exception):
            error_msg = self.locale_config.messages.query_error_message.format(
                error=str(result)
            )
            messagebox.showerror(self.locale_config.messages.query_error, error_msg)
            return

        if isinstance(result, pd.DataFrame):
            self.results_df = result
            if result.empty:
                messagebox.showinfo(
                    self.locale_config.messages.no_results,
                    self.locale_config.messages.no_results_returned,
                )
                return

            self.save_button.configure(state="normal")

            # --- Populate Table ---
            self.results_table["columns"] = list(result.columns)
            for col in result.columns:
                self.results_table.heading(col, text=col)
                # Simple auto-width - can be improved
                self.results_table.column(
                    col, width=len(col) * 10, minwidth=50, stretch=True
                )

            for index, row in result.iterrows():
                self.results_table.insert("", "end", values=list(row))
        else:
            messagebox.showinfo(
                self.locale_config.messages.success,
                self.locale_config.messages.dml_success,
            )

    def _save_results(self: "App"):
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning(
                self.locale_config.messages.no_results,
                self.locale_config.messages.no_results_save,
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{self.output_format_var.get()}",
            filetypes=(
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ),
        )
        if not file_path:
            return

        try:
            export_data(
                file_path,
                self.results_df,
                self.output_format_var.get(),
                self.single_file_var.get() == "on",
                self.single_sheet_var.get() == "on",
                self.connection_column_var.get(),
                self.format_excel_var.get() == "on",
            )
            success_msg = self.locale_config.messages.save_success.format(
                file_path=file_path
            )
            messagebox.showinfo(self.locale_config.messages.success, success_msg)
        except Exception as e:
            error_msg = self.locale_config.messages.save_error_message.format(error=e)
            messagebox.showerror(self.locale_config.messages.save_error, error_msg)


if __name__ == "__main__":
    from db_tools.logger import setup_logging

    setup_logging()
    app = App()
    app.mainloop()
