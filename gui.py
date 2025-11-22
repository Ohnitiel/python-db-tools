import threading
from tkinter import filedialog, messagebox, ttk

import customtkinter
import pandas as pd
from dotenv import load_dotenv

from db_tools.database.runner import DBConnectionRunner
from db_tools.exporter import export_data
from db_tools.extras import find_root_dir, get_available_connections


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Load environment variables from .env file
        try:
            load_dotenv(find_root_dir(["pyproject.toml"]) / ".env")
        except Exception as e:
            print(f"Could not load .env file: {e}")

        self.title("Database Multi-Tool")
        self.geometry("1280x800")
        self.results_df = None

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
            text="Connections",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.conn_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.conn_filter_entry = customtkinter.CTkEntry(
            self.left_frame, placeholder_text="Filter connections..."
        )
        self.conn_filter_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.conn_filter_entry.bind("<KeyRelease>", self._filter_connections)
        self.select_all_var = customtkinter.StringVar(value="off")
        self.select_all_checkbox = customtkinter.CTkCheckBox(
            self.left_frame,
            text="Select All",
            variable=self.select_all_var,
            onvalue="on",
            offvalue="off",
            command=self._toggle_select_all,
        )
        self.select_all_checkbox.grid(row=2, column=0, padx=10, pady=(5, 0), sticky="w")
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
        self.env_label = customtkinter.CTkLabel(self.options_frame, text="Environment:")
        self.env_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.environment_var = customtkinter.StringVar(value="staging")
        self.env_dropdown = customtkinter.CTkOptionMenu(
            self.options_frame,
            variable=self.environment_var,
            values=["staging", "production", "replica"],
        )
        self.env_dropdown.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")

        # Parallelism
        self.parallel_var = customtkinter.StringVar(value="on")
        self.parallel_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text="Run in Parallel",
            variable=self.parallel_var,
            onvalue="on",
            offvalue="off",
        )
        self.parallel_checkbox.grid(
            row=1, column=0, columnspan=2, padx=(0, 10), pady=5, sticky="w"
        )

        # Max Workers
        self.max_workers_label = customtkinter.CTkLabel(
            self.options_frame, text="Max Workers:"
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
            text="Use Cache",
            variable=self.cache_var,
            onvalue="on",
            offvalue="off",
        )
        self.cache_checkbox.grid(row=3, column=0, padx=(0, 10), pady=5, sticky="w")
        self.ignore_cache_var = customtkinter.StringVar(value="off")
        self.ignore_cache_checkbox = customtkinter.CTkCheckBox(
            self.options_frame,
            text="Ignore Cache",
            variable=self.ignore_cache_var,
            onvalue="on",
            offvalue="off",
        )
        self.ignore_cache_checkbox.grid(
            row=3, column=1, padx=(0, 10), pady=5, sticky="w"
        )

        # Export
        self.output_format_label = customtkinter.CTkLabel(
            self.options_frame, text="Output Format:"
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
            text="Format Excel",
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
            text="Single Sheet",
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
            text="Single File",
            variable=self.single_file_var,
            onvalue="on",
            offvalue="off",
        )
        self.single_file_checkbox.grid(
            row=6, column=1, padx=(0, 10), pady=5, sticky="w"
        )

        self.connection_column_label = customtkinter.CTkLabel(
            self.options_frame, text="Connection Column:"
        )
        self.connection_column_label.grid(
            row=7, column=0, padx=(0, 5), pady=5, sticky="w"
        )
        self.connection_column_var = customtkinter.StringVar(value="connection")
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
            text="--commit",
            variable=self.commit_var,
            onvalue="on",
            offvalue="off",
        )
        self.commit_checkbox.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
        self.run_button = customtkinter.CTkButton(
            self.bottom_frame, text="Run Query", command=self._run_query_callback
        )
        self.run_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="e")

        # --- Right Panel (Query and Results) ---
        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_rowconfigure(1, weight=1)  # Make results table expandable
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.query_box = customtkinter.CTkTextbox(
            self.right_frame, height=150, border_width=2, font=("Consolas", 12)
        )
        self.query_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.query_box.insert("1.0", "-- Write your SQL query here...")

        self._create_results_table()

        self.save_button = customtkinter.CTkButton(
            self.right_frame,
            text="Save Results",
            command=self._save_results,
            state="disabled",
        )
        self.save_button.grid(row=2, column=0, padx=5, pady=5, sticky="e")

    def _browse_save_path(self):
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

    def _create_results_table(self):
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

    def _update_connection_list(self, filter_text=""):
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

    def _filter_connections(self, event=None):
        self._update_connection_list(self.conn_filter_entry.get())
        self.select_all_var.set("off")

    def _toggle_select_all(self):
        new_state = self.select_all_var.get()
        for var in self.conn_checkboxes.values():
            var.set(new_state)

    def _run_query_callback(self):
        selected_connections = [
            name for name, var in self.conn_checkboxes.items() if var.get() == "on"
        ]
        if not selected_connections:
            messagebox.showwarning(
                "No Connections", "Please select at least one database connection."
            )
            return

        query = self.query_box.get("1.0", "end-2c").strip()
        if not query or query.startswith("--"):
            messagebox.showwarning("No Query", "Please enter a SQL query to execute.")
            return

        self.run_button.configure(state="disabled", text="Running...")
        self.save_button.configure(state="disabled")
        self.results_df = None
        # Clear previous results
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        self.results_table["columns"] = []

        commit_mode = self.commit_var.get() == "on"

        # Run the database query in a background thread
        thread = threading.Thread(
            target=self._execute_query_worker,
            args=(selected_connections, query, commit_mode),
        )
        thread.daemon = True
        thread.start()

    def _execute_query_worker(self, connections, query, commit_mode):
        """Worker function to be run in a separate thread."""
        try:
            use_cache_callback = lambda: messagebox.askyesno(
                "Cache Found",
                "A cached result for this query was found. Do you want to use it?",
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

    def _update_ui_after_query(self, result):
        """Receives results from worker thread and updates UI. Runs in main thread."""
        self.run_button.configure(state="normal", text="Run Query")

        if isinstance(result, Exception):
            messagebox.showerror("Query Error", f"An error occurred:\n{str(result)}")
            return

        if isinstance(result, pd.DataFrame):
            self.results_df = result
            if result.empty:
                messagebox.showinfo(
                    "No Results",
                    "The query executed successfully but returned no data.",
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
                "Success", "DML query executed successfully on all connections."
            )

    def _save_results(self):
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Results", "There are no results to save.")
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
            messagebox.showinfo("Success", f"Results successfully saved to {file_path}")
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"An error occurred while saving the file:\n{e}"
            )


if __name__ == "__main__":
    from db_tools.logger import setup_logging

    setup_logging()

    app = App()
    app.mainloop()
