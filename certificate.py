"""
certificate.py
--------------
Certificate Eligibility module.

Shows only students with balance_fees == 0 (Fully Paid). Supports:
  - Checkbox-style selection (single or multiple) via a Treeview with a
    checkbox column rendered as a clickable text glyph (Tkinter's stock
    Treeview has no native checkbox widget, so this is the standard,
    dependency-free way to achieve checkbox behaviour).
  - Generate Certificate Eligibility List (preview of selected students)
  - Export Selected Students to Excel
  - Print Option (opens a print-friendly HTML page)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from student import StudentModel
import ui_helpers as ui
import reports

CHECK_ON = "\u2611"   # ☑
CHECK_OFF = "\u2610"  # ☐


class CertificateWindow(tk.Frame):
    """Embedded certificate eligibility module shown inside the main app shell."""

    def __init__(self, master, db):
        super().__init__(master, bg=ui.COLORS["bg"])
        self.db = db
        self.student_model = StudentModel(db)
        self.checked_ids = set()  # set of register_ids currently checked
        self.row_lookup = {}      # iid -> sqlite3.Row, for quick access

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------
    def _build_ui(self):
        header = tk.Frame(self, bg=ui.COLORS["primary"], height=60)
        header.pack(fill="x")
        tk.Label(header, text="Certificate Eligibility (Fully Paid Students)",
                  bg=ui.COLORS["primary"], fg="white",
                  font=ui.FONTS["heading"]).pack(side="left", padx=20, pady=15)

        toolbar = tk.Frame(self, bg=ui.COLORS["bg"])
        toolbar.pack(fill="x", padx=15, pady=10)

        ui.make_button(toolbar, "Select All", self._select_all,
                        bg=ui.COLORS["primary"], width=12).pack(side="left", padx=4)
        ui.make_button(toolbar, "Deselect All", self._deselect_all,
                        bg=ui.COLORS["muted"], width=12).pack(side="left", padx=4)
        ui.make_button(toolbar, "Generate List", self._generate_list,
                        bg=ui.COLORS["primary_dark"], width=14).pack(side="left", padx=4)
        ui.make_button(toolbar, "Export to Excel", self._export_excel,
                        bg=ui.COLORS["secondary"], width=14).pack(side="left", padx=4)
        ui.make_button(toolbar, "Print", self._print_list,
                        bg=ui.COLORS["warning"], width=10).pack(side="left", padx=4)
        ui.make_button(toolbar, "Refresh", self._load_data,
                        bg=ui.COLORS["muted"], width=10).pack(side="left", padx=4)

        # ---- Table ----
        table_outer, table_card = ui.make_card(self, padx=10, pady=10)
        table_outer.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("check", "register_id", "student_name", "course_name",
                   "admission_date", "status")
        headings = ("Select", "Register ID", "Student Name", "Course Name",
                    "Admission Date", "Completion Status")

        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=18)
        for col, head in zip(columns, headings):
            self.tree.heading(col, text=head)
            width = 80 if col == "check" else 160
            self.tree.column(col, width=width, anchor="center" if col == "check" else "w")

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Clicking a row toggles its checkbox (click anywhere on the row).
        self.tree.bind("<Button-1>", self._on_row_click)

        # ---- Footer summary ----
        self.summary_var = tk.StringVar(value="0 students eligible | 0 selected")
        tk.Label(self, textvariable=self.summary_var, bg=ui.COLORS["bg"],
                  fg=ui.COLORS["muted"], font=ui.FONTS["small"]).pack(
            anchor="w", padx=20, pady=(0, 10))

    # ------------------------------------------------------------------
    def _load_data(self):
        """Loads all fully-paid students into the table."""
        self.tree.delete(*self.tree.get_children())
        self.row_lookup.clear()
        self.checked_ids.clear()

        students = self.student_model.get_fully_paid_students()
        for student in students:
            iid = str(student["register_id"])
            self.tree.insert("", "end", iid=iid, values=(
                CHECK_OFF, student["register_id"], student["student_name"],
                student["course_name"], student["admission_date"], "Completed - Eligible"
            ))
            self.row_lookup[iid] = student

        self._update_summary()

    def _on_row_click(self, event):
        """Toggles the checkbox glyph when the user clicks on the 'check' column."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        row_iid = self.tree.identify_row(event.y)
        if not row_iid:
            return

        # Toggle on click anywhere in the row (more forgiving UX than
        # requiring an exact click on the checkbox glyph itself).
        self._toggle_row(row_iid)

    def _toggle_row(self, row_iid):
        values = list(self.tree.item(row_iid, "values"))
        register_id = int(values[1])
        if register_id in self.checked_ids:
            self.checked_ids.discard(register_id)
            values[0] = CHECK_OFF
        else:
            self.checked_ids.add(register_id)
            values[0] = CHECK_ON
        self.tree.item(row_iid, values=values)
        self._update_summary()

    def _select_all(self):
        for row_iid in self.tree.get_children():
            values = list(self.tree.item(row_iid, "values"))
            values[0] = CHECK_ON
            self.tree.item(row_iid, values=values)
            self.checked_ids.add(int(values[1]))
        self._update_summary()

    def _deselect_all(self):
        for row_iid in self.tree.get_children():
            values = list(self.tree.item(row_iid, "values"))
            values[0] = CHECK_OFF
            self.tree.item(row_iid, values=values)
        self.checked_ids.clear()
        self._update_summary()

    def _update_summary(self):
        total = len(self.tree.get_children())
        self.summary_var.set(f"{total} students eligible | {len(self.checked_ids)} selected")

    def _get_selected_students(self):
        """Returns the list of sqlite3.Row objects currently checked."""
        return [self.row_lookup[str(rid)] for rid in self.checked_ids
                if str(rid) in self.row_lookup]

    # ------------------------------------------------------------------
    def _generate_list(self):
        """Shows a quick preview/summary popup of the generated eligibility list."""
        selected = self._get_selected_students()
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one student.")
            return

        preview = "\n".join(
            f"#{s['register_id']} - {s['student_name']} ({s['course_name']})"
            for s in selected
        )
        messagebox.showinfo(
            "Certificate Eligibility List Generated",
            f"{len(selected)} student(s) are eligible for the Course Completion "
            f"Certificate:\n\n{preview}"
        )

    def _export_excel(self):
        selected = self._get_selected_students()
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one student to export.")
            return
        try:
            path = reports.export_certificate_list_to_excel(selected)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
            return
        messagebox.showinfo("Export Successful", f"Certificate list exported to:\n{path}")

    def _print_list(self):
        selected = self._get_selected_students()
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one student to print.")
            return
        try:
            path = reports.generate_printable_certificate_list(selected)
        except Exception as e:
            messagebox.showerror("Print Failed", str(e))
            return
        messagebox.showinfo(
            "Print Preview Opened",
            "A print-friendly page has been opened in your browser.\n"
            "Use Ctrl+P (or the Print button on the page) to print it."
        )
