import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from database import Database
from student import StudentModel, ValidationError, COURSE_TYPES
from payment import PaymentWindow
from certificate import CertificateWindow
import reports
import ui_helpers as ui

LOGO_FILENAME = "thoorigai_logo.png"
FACULTY_EMAIL = "thoorigaifaculty@gmail.com"


# ===========================================================================
# Reusable scrollable container (used by the Add/Edit Student forms so the
# form remains usable on smaller screens / lower resolutions).
# ===========================================================================
class ScrollableFrame(tk.Frame):
    """A vertically scrollable frame. Place child widgets inside `.body`."""

    def __init__(self, parent, bg=None):
        super().__init__(parent, bg=bg or ui.COLORS["bg"])
        canvas = tk.Canvas(self, bg=bg or ui.COLORS["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = tk.Frame(canvas, bg=bg or ui.COLORS["bg"])

        self.body.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Mouse wheel scrolling support (Windows/Linux + macOS deltas)
        def _on_mousewheel(event):
            delta = -1 * (event.delta // 120) if event.delta else 0
            canvas.yview_scroll(delta, "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)


# ===========================================================================
# Main Application
# ===========================================================================
class StudentManagementApp(tk.Tk):
    """Root application window hosting the sidebar dashboard and content area."""

    def __init__(self):
        super().__init__()
        self.title("Student Course Management System")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        self.configure(bg=ui.COLORS["bg"])

        ui.configure_styles(self)

        # ---- Shared backend objects ----
        self.db = Database()
        self.student_model = StudentModel(self.db)

        self._build_layout()
        self.show_dashboard_home()

    # ------------------------------------------------------------------
    # Layout: sidebar + main content area
    # ------------------------------------------------------------------
    def _build_layout(self):
        self.sidebar = tk.Frame(self, bg=ui.COLORS["sidebar_bg"], width=240)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=ui.COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()

    def _build_sidebar(self):
        title_frame = tk.Frame(self.sidebar, bg=ui.COLORS["sidebar_bg"])
        title_frame.pack(fill="x", pady=(25, 30), padx=15)

        logo_path = os.path.join(os.path.dirname(__file__), LOGO_FILENAME)
        if os.path.exists(logo_path):
            try:
                logo_image = tk.PhotoImage(file=logo_path)
                self.logo_image = logo_image
                tk.Label(title_frame, image=logo_image, bg=ui.COLORS["sidebar_bg"]).pack(
                    anchor="w", pady=(0, 10)
                )
            except tk.TclError:
                tk.Label(title_frame, text="🎓 ThoorigAI", bg=ui.COLORS["sidebar_bg"],
                          fg="white", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        else:
            tk.Label(title_frame, text="🎓 ThoorigAI", bg=ui.COLORS["sidebar_bg"],
                      fg="white", font=("Segoe UI", 16, "bold")).pack(anchor="w")

        tk.Label(title_frame, text="Course Management", bg=ui.COLORS["sidebar_bg"],
                  fg=ui.COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w")

        menu_items = [
            ("🏠  Dashboard", self.show_dashboard_home),
            ("➕  Add New Student", self.show_add_student),
            ("📋  View All Students", self.show_view_students),
            ("💳  Make Course Payment", self.open_payment_window),
            ("🎖️  Certificate Eligibility", self.open_certificate_window),
            ("🔍  Search Student", self.show_search_student),
            ("✏️  Edit Student Details", self.show_edit_student),
            ("🗑️  Delete Student Record", self.show_delete_student),
        ]

        self.sidebar_buttons = []
        for text, command in menu_items:
            btn = tk.Button(
                self.sidebar, text=text, command=command, anchor="w",
                bg=ui.COLORS["sidebar_bg"], fg="white", font=ui.FONTS["sidebar"],
                relief="flat", bd=0, padx=20, pady=12, cursor="hand2",
                activebackground=ui.COLORS["sidebar_hover"], activeforeground="white"
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=ui.COLORS["sidebar_hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=ui.COLORS["sidebar_bg"]))
            self.sidebar_buttons.append(btn)

        footer = tk.Label(self.sidebar, text=f"Faculty Contact:\n{FACULTY_EMAIL}",
                           bg=ui.COLORS["sidebar_bg"], fg=ui.COLORS["muted"],
                           font=ui.FONTS["small"], justify="left", wraplength=200)
        footer.pack(side="bottom", pady=20, padx=15, anchor="w")

    def _clear_content(self):
        """Removes all widgets from the main content area before showing a new screen."""
        for widget in self.content.winfo_children():
            widget.destroy()

    def _page_header(self, title, subtitle=""):
        header = tk.Frame(self.content, bg=ui.COLORS["bg"])
        header.pack(fill="x", padx=25, pady=(20, 10))
        tk.Label(header, text=title, bg=ui.COLORS["bg"], fg=ui.COLORS["text_dark"],
                  font=ui.FONTS["title"]).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, bg=ui.COLORS["bg"], fg=ui.COLORS["muted"],
                      font=ui.FONTS["label"]).pack(anchor="w")
        return header

    # ------------------------------------------------------------------
    # DASHBOARD HOME
    # ------------------------------------------------------------------
    def show_dashboard_home(self):
        self._clear_content()
        self._page_header("Dashboard", "Welcome to the Student Course Management System")

        stats_frame = tk.Frame(self.content, bg=ui.COLORS["bg"])
        stats_frame.pack(fill="x", padx=25, pady=10)

        all_students = self.student_model.get_all_students()
        total_students = len(all_students)
        fully_paid = sum(1 for s in all_students if s["balance_fees"] <= 0)
        pending = total_students - fully_paid
        total_collected = sum(s["paid_amount"] for s in all_students)

        stats = [
            ("Total Students", total_students, ui.COLORS["primary"]),
            ("Fully Paid", fully_paid, ui.COLORS["secondary"]),
            ("Pending Payments", pending, ui.COLORS["warning"]),
            ("Total Collected (₹)", f"{total_collected:,.0f}", ui.COLORS["primary_dark"]),
        ]
        for i, (label, value, color) in enumerate(stats):
            card_outer, card = ui.make_card(stats_frame, padx=15, pady=15)
            card_outer.grid(row=0, column=i, padx=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=str(value), bg=ui.COLORS["card_bg"], fg=color,
                      font=("Segoe UI", 22, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=ui.COLORS["card_bg"], fg=ui.COLORS["muted"],
                      font=ui.FONTS["label"]).pack(anchor="w")

        # Quick action shortcuts
        actions_outer, actions_card = ui.make_card(self.content, padx=20, pady=20)
        actions_outer.pack(fill="x", padx=25, pady=20)
        tk.Label(actions_card, text="Quick Actions", bg=ui.COLORS["card_bg"],
                  font=ui.FONTS["subtitle"]).pack(anchor="w", pady=(0, 10))
        btn_row = tk.Frame(actions_card, bg=ui.COLORS["card_bg"])
        btn_row.pack(anchor="w")
        ui.make_button(btn_row, "➕ Add Student", self.show_add_student,
                        bg=ui.COLORS["primary"]).pack(side="left", padx=5)
        ui.make_button(btn_row, "💳 Make Payment", self.open_payment_window,
                        bg=ui.COLORS["secondary"]).pack(side="left", padx=5)
        ui.make_button(btn_row, "🎖️ Certificates", self.open_certificate_window,
                        bg=ui.COLORS["warning"]).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # 1. ADD NEW STUDENT
    # ------------------------------------------------------------------
    def show_add_student(self):
        self._clear_content()
        self._page_header("Add New Student", "Fill in student, course, and fee details")

        scroll = ScrollableFrame(self.content)
        scroll.pack(fill="both", expand=True, padx=25, pady=10)
        form_host = scroll.body

        card_outer, card = ui.make_card(form_host, padx=25, pady=25)
        card_outer.pack(fill="x", expand=True)

        vars_ = {}

        # ---- Student details ----
        ui.make_label(card, "Student Details", bold=True, size=13,
                       color=ui.COLORS["primary"]).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        next_id = self.student_model.get_next_register_id()
        ui.make_label(card, "Register ID:").grid(row=1, column=0, sticky="w", pady=6)
        register_id_var = tk.StringVar(value=str(next_id))
        vars_["register_id"] = register_id_var
        ui.make_entry(card, register_id_var, width=28).grid(
            row=1, column=1, sticky="w", pady=6)

        from datetime import datetime
        ui.make_label(card, "Admission Date:").grid(row=1, column=2, sticky="w", pady=6, padx=(20, 0))
        admission_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        vars_["admission_date"] = admission_date_var
        DateEntry(
            card, textvariable=admission_date_var, date_pattern="yyyy-mm-dd",
            font=ui.FONTS["label"], width=25
        ).grid(row=1, column=3, sticky="w", pady=6)

        # ---- Editable student fields ----
        def add_field(row, col, label, key, width=28):
            ui.make_label(card, f"{label}:").grid(row=row, column=col, sticky="w", pady=6,
                                                    padx=(20, 0) if col else 0)
            var = tk.StringVar()
            entry = ui.make_entry(card, var, width=width)
            entry.grid(row=row, column=col + 1, sticky="w", pady=6,
                       padx=(0, 20) if col else 0)
            vars_[key] = var
            return entry

        add_field(2, 0, "Student Name *", "student_name")
        add_field(2, 2, "Qualification", "qualification")
        add_field(3, 0, "Phone Number *", "phone")
        add_field(3, 2, "Email Address *", "email")

        # ---- Course Details ----
        ui.make_label(card, "Course Details", bold=True, size=13,
                       color=ui.COLORS["primary"]).grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(20, 10))

        add_field(5, 0, "Course Name *", "course_name")

        ui.make_label(card, "Course Type *:").grid(row=5, column=2, sticky="w", pady=6, padx=(20, 0))
        course_type_var = tk.StringVar(value=COURSE_TYPES[0])
        vars_["course_type"] = course_type_var
        ttk.Combobox(card, textvariable=course_type_var, values=COURSE_TYPES,
                     state="readonly", width=26).grid(row=5, column=3, sticky="w", pady=6)

        # ---- Fee Details ----
        ui.make_label(card, "Fee Details", bold=True, size=13,
                       color=ui.COLORS["primary"]).grid(
            row=6, column=0, columnspan=4, sticky="w", pady=(20, 10))

        add_field(7, 0, "Course Total Fees *", "total_fees")
        add_field(7, 2, "Course Paid Amount *", "paid_amount")

        balance_var = tk.StringVar(value="0.00")
        ui.make_label(card, "Balance Fees (Auto):").grid(row=8, column=0, sticky="w", pady=6)
        balance_label = ui.make_label(card, "0.00", bold=True, color=ui.COLORS["secondary"])
        balance_label.grid(row=8, column=1, sticky="w", pady=6)

        def recalc_balance(*_):
            try:
                total = float(vars_["total_fees"].get() or 0)
                paid = float(vars_["paid_amount"].get() or 0)
                balance = total - paid
                balance_label.config(
                    text=f"{balance:.2f}",
                    fg=ui.COLORS["secondary"] if balance <= 0 else ui.COLORS["warning"]
                )
            except ValueError:
                balance_label.config(text="--")

        vars_["total_fees"].trace_add("write", recalc_balance)
        vars_["paid_amount"].trace_add("write", recalc_balance)

        # ---- Batch Information (optional at admission time) ----
        ui.make_label(card, "Batch Information (optional)", bold=True, size=13,
                       color=ui.COLORS["primary"]).grid(
            row=9, column=0, columnspan=4, sticky="w", pady=(20, 10))
        add_field(10, 0, "Batch Start Date (YYYY-MM-DD)", "batch_start_date")
        add_field(10, 2, "Faculty Name", "faculty_name")

        ui.make_label(card, f"Faculty contact: {FACULTY_EMAIL}", color=ui.COLORS["muted"]).grid(
            row=11, column=0, columnspan=4, sticky="w", pady=(5, 0))

        # ---- Save button ----
        btn_frame = tk.Frame(card, bg=ui.COLORS["card_bg"])
        btn_frame.grid(row=12, column=0, columnspan=4, pady=(25, 0), sticky="w")

        def save_student():
            data = {k: v.get() for k, v in vars_.items()}
            try:
                new_id = self.student_model.add_student(data)
            except ValidationError as e:
                messagebox.showerror("Validation Error", str(e))
                return
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not save student: {e}")
                return

            messagebox.showinfo("Success", f"Student added successfully!\nRegister ID: {new_id}")
            self.show_add_student()  # refresh form with the next available ID

        ui.make_button(btn_frame, "💾 Save Student", save_student,
                        bg=ui.COLORS["secondary"], width=18).pack(side="left", padx=5)
        ui.make_button(btn_frame, "Clear Form", self.show_add_student,
                        bg=ui.COLORS["muted"], width=14).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # 2. VIEW ALL STUDENTS
    # ------------------------------------------------------------------
    def show_view_students(self):
        self._clear_content()
        self._page_header("View All Students", "Browse, search, filter, and manage student records")

        # ---- Toolbar: search + filters + export ----
        toolbar_outer, toolbar = ui.make_card(self.content, padx=15, pady=12)
        toolbar_outer.pack(fill="x", padx=25, pady=(0, 10))

        ui.make_label(toolbar, "Search:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        search_var = tk.StringVar()
        search_entry = ui.make_entry(toolbar, search_var, width=22)
        search_entry.grid(row=0, column=1, padx=(0, 15))

        ui.make_label(toolbar, "Course Type:").grid(row=0, column=2, padx=(0, 5), sticky="w")
        course_filter_var = tk.StringVar(value="All")
        ttk.Combobox(toolbar, textvariable=course_filter_var,
                     values=["All"] + COURSE_TYPES, state="readonly", width=24).grid(
            row=0, column=3, padx=(0, 15))

        ui.make_label(toolbar, "Payment Status:").grid(row=0, column=4, padx=(0, 5), sticky="w")
        status_filter_var = tk.StringVar(value="All")
        ttk.Combobox(toolbar, textvariable=status_filter_var,
                     values=["All", "Fully Paid", "Pending"], state="readonly", width=14).grid(
            row=0, column=5, padx=(0, 15))

        def apply_filters():
            keyword = search_var.get().strip()
            if keyword:
                rows = self.student_model.search_students(keyword)
            else:
                rows = self.student_model.filter_students(
                    course_filter_var.get(), status_filter_var.get())
            populate_tree(rows)

        def reset_filters():
            search_var.set("")
            course_filter_var.set("All")
            status_filter_var.set("All")
            populate_tree(self.student_model.get_all_students())

        ui.make_button(toolbar, "Apply", apply_filters, bg=ui.COLORS["primary"],
                        width=10).grid(row=0, column=6, padx=5)
        ui.make_button(toolbar, "Reset", reset_filters, bg=ui.COLORS["muted"],
                        width=10).grid(row=0, column=7, padx=5)

        def export_excel():
            rows = current_rows["data"]
            if not rows:
                messagebox.showwarning("No Data", "There are no students to export.")
                return
            try:
                path = reports.export_students_to_excel(rows)
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
                return
            messagebox.showinfo("Export Successful", f"Students exported to:\n{path}")

        ui.make_button(toolbar, "📤 Export to Excel", export_excel,
                        bg=ui.COLORS["secondary"], width=16).grid(row=0, column=8, padx=5)

        # ---- Table ----
        table_outer, table_card = ui.make_card(self.content, padx=10, pady=10)
        table_outer.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        columns = ("register_id", "admission_date", "student_name", "qualification",
                   "course_name", "course_type", "phone", "email",
                   "balance_fees", "status", "batch_start_date", "faculty_name")
        headings = ("Reg. ID", "Admission Date", "Student Name", "Qualification",
                    "Course Name", "Course Type", "Phone", "Email",
                    "Balance Fees", "Status", "Batch Start", "Faculty")

        tree = ttk.Treeview(table_card, columns=columns, show="headings")
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, width=110, anchor="w")
        tree.column("email", width=160)
        tree.column("student_name", width=140)

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        current_rows = {"data": []}

        def populate_tree(rows):
            tree.delete(*tree.get_children())
            current_rows["data"] = rows
            for r in rows:
                status = "Fully Paid" if r["balance_fees"] <= 0 else "Pending"
                tree.insert("", "end", iid=str(r["register_id"]), values=(
                    r["register_id"], r["admission_date"], r["student_name"],
                    r["qualification"] or "", r["course_name"], r["course_type"],
                    r["phone"], r["email"], f"{r['balance_fees']:.2f}", status,
                    r["batch_start_date"] or "", r["faculty_name"] or ""
                ))

        populate_tree(self.student_model.get_all_students())

        # ---- Batch / Faculty inline edit panel ----
        edit_outer, edit_card = ui.make_card(self.content, padx=15, pady=12)
        edit_outer.pack(fill="x", padx=25, pady=(0, 20))

        ui.make_label(edit_card, "Update Batch Info for Selected Student:", bold=True).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        ui.make_label(edit_card, "Batch Start Date:").grid(row=1, column=0, sticky="w")
        batch_var = tk.StringVar()
        ui.make_entry(edit_card, batch_var, width=18).grid(row=1, column=1, padx=(5, 20))

        ui.make_label(edit_card, "Faculty Name:").grid(row=1, column=2, sticky="w")
        faculty_var = tk.StringVar()
        ui.make_entry(edit_card, faculty_var, width=18).grid(row=1, column=3, padx=(5, 20))

        def on_select(_event=None):
            selected = tree.selection()
            if not selected:
                return
            values = tree.item(selected[0], "values")
            batch_var.set(values[10])
            faculty_var.set(values[11])

        tree.bind("<<TreeviewSelect>>", on_select)

        def save_batch_info():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a student row first.")
                return
            register_id = int(selected[0])
            self.student_model.update_batch_info(register_id, batch_var.get(), faculty_var.get())
            messagebox.showinfo("Updated", "Batch information updated successfully.")
            apply_filters()

        ui.make_button(edit_card, "Update Batch Info", save_batch_info,
                        bg=ui.COLORS["primary"], width=18).grid(row=1, column=4, padx=10)

    # ------------------------------------------------------------------
    # 3. COURSE PAYMENT (opens Toplevel from payment.py)
    # ------------------------------------------------------------------
    def open_payment_window(self):
        PaymentWindow(self, self.db, on_payment_made=self._refresh_if_visible)

    # ------------------------------------------------------------------
    # 4. CERTIFICATE ELIGIBILITY (opens Toplevel from certificate.py)
    # ------------------------------------------------------------------
    def open_certificate_window(self):
        CertificateWindow(self, self.db)

    def _refresh_if_visible(self):
        """Lightweight refresh hook so dashboard stats stay current after a payment."""
        pass  # Dashboard recalculates from DB each time it's shown; nothing to do here.

    # ------------------------------------------------------------------
    # 5. SEARCH STUDENT
    # ------------------------------------------------------------------
    def show_search_student(self):
        self._clear_content()
        self._page_header("Search Student", "Search by Register ID, Name, Phone, or Email")

        search_outer, search_card = ui.make_card(self.content, padx=20, pady=15)
        search_outer.pack(fill="x", padx=25, pady=(0, 10))

        ui.make_label(search_card, "Search Keyword:").pack(side="left", padx=(0, 10))
        keyword_var = tk.StringVar()
        entry = ui.make_entry(search_card, keyword_var, width=35)
        entry.pack(side="left", padx=(0, 10))

        table_outer, table_card = ui.make_card(self.content, padx=10, pady=10)
        table_outer.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        columns = ("register_id", "student_name", "phone", "email",
                   "course_name", "course_type", "balance_fees", "status")
        headings = ("Reg. ID", "Student Name", "Phone", "Email",
                    "Course Name", "Course Type", "Balance Fees", "Status")
        tree = ttk.Treeview(table_card, columns=columns, show="headings")
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True)

        def do_search():
            keyword = keyword_var.get().strip()
            tree.delete(*tree.get_children())
            if not keyword:
                messagebox.showinfo("Search", "Please enter a search keyword.")
                return
            results = self.student_model.search_students(keyword)
            if not results:
                messagebox.showinfo("No Results", f"No students found matching '{keyword}'.")
            for r in results:
                status = "Fully Paid" if r["balance_fees"] <= 0 else "Pending"
                tree.insert("", "end", values=(
                    r["register_id"], r["student_name"], r["phone"], r["email"],
                    r["course_name"], r["course_type"], f"{r['balance_fees']:.2f}", status
                ))

        entry.bind("<Return>", lambda e: do_search())
        ui.make_button(search_card, "🔍 Search", do_search, bg=ui.COLORS["primary"],
                        width=12).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # 6. EDIT STUDENT DETAILS
    # ------------------------------------------------------------------
    def show_edit_student(self):
        self._clear_content()
        self._page_header("Edit Student Details", "Look up a student by Register ID, then update their record")

        lookup_outer, lookup_card = ui.make_card(self.content, padx=20, pady=15)
        lookup_outer.pack(fill="x", padx=25, pady=(0, 10))

        ui.make_label(lookup_card, "Register ID:").pack(side="left", padx=(0, 10))
        reg_id_var = tk.StringVar()
        entry = ui.make_entry(lookup_card, reg_id_var, width=20)
        entry.pack(side="left", padx=(0, 10))

        form_container = tk.Frame(self.content, bg=ui.COLORS["bg"])
        form_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        def load_student():
            reg_id_text = reg_id_var.get().strip()
            if not reg_id_text.isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid numeric Register ID.")
                return
            student = self.student_model.get_student_by_register_id(int(reg_id_text))
            if not student:
                messagebox.showerror("Not Found", f"No student found with Register ID {reg_id_text}.")
                return
            render_edit_form(student)

        entry.bind("<Return>", lambda e: load_student())
        ui.make_button(lookup_card, "Load Student", load_student,
                        bg=ui.COLORS["primary"], width=14).pack(side="left", padx=5)

        def render_edit_form(student):
            for w in form_container.winfo_children():
                w.destroy()

            card_outer, card = ui.make_card(form_container, padx=25, pady=25)
            card_outer.pack(fill="x")

            vars_ = {}

            ui.make_label(card, f"Editing Register ID:", bold=True,
                           size=13, color=ui.COLORS["primary"]).grid(
                row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

            # Editable Register ID field
            ui.make_label(card, "Register ID:").grid(row=1, column=0, sticky="w", pady=6)
            reg_id_var = tk.StringVar(value=str(student["register_id"]))
            ui.make_entry(card, reg_id_var, width=18).grid(row=1, column=1, sticky="w", pady=6,
                                                           padx=(0, 20))


            def add_field(row, col, label, key, initial, width=28):
                ui.make_label(card, f"{label}:").grid(row=row, column=col, sticky="w", pady=6,
                                                        padx=(20, 0) if col else 0)
                var = tk.StringVar(value=initial)
                ui.make_entry(card, var, width=width).grid(
                    row=row, column=col + 1, sticky="w", pady=6, padx=(0, 20) if col else 0)
                vars_[key] = var

            add_field(2, 0, "Student Name", "student_name", student["student_name"])
            add_field(2, 2, "Qualification", "qualification", student["qualification"] or "")
            add_field(3, 0, "Phone Number", "phone", student["phone"])
            add_field(3, 2, "Email Address", "email", student["email"])
            add_field(4, 0, "Course Name", "course_name", student["course_name"])

            ui.make_label(card, "Course Type:").grid(row=4, column=2, sticky="w", pady=6, padx=(20, 0))
            course_type_var = tk.StringVar(value=student["course_type"])
            vars_["course_type"] = course_type_var
            ttk.Combobox(card, textvariable=course_type_var, values=COURSE_TYPES,
                         state="readonly", width=26).grid(row=4, column=3, sticky="w", pady=6)

            add_field(5, 0, "Total Fees", "total_fees", str(student["total_fees"]))
            add_field(5, 2, "Paid Amount", "paid_amount", str(student["paid_amount"]))
            add_field(6, 0, "Batch Start Date", "batch_start_date", student["batch_start_date"] or "")
            add_field(6, 2, "Faculty Name", "faculty_name", student["faculty_name"] or "")

            balance_label = ui.make_label(card, f"{student['balance_fees']:.2f}", bold=True,
                                           color=ui.COLORS["secondary"])
            ui.make_label(card, "Current Balance:").grid(row=7, column=0, sticky="w", pady=6)
            balance_label.grid(row=7, column=1, sticky="w", pady=6)

            def recalc(*_):
                try:
                    total = float(vars_["total_fees"].get() or 0)
                    paid = float(vars_["paid_amount"].get() or 0)
                    bal = total - paid
                    balance_label.config(text=f"{bal:.2f}",
                                          fg=ui.COLORS["secondary"] if bal <= 0 else ui.COLORS["warning"])
                except ValueError:
                    balance_label.config(text="--")

            vars_["total_fees"].trace_add("write", recalc)
            vars_["paid_amount"].trace_add("write", recalc)

            def save_changes():
                data = {k: v.get() for k, v in vars_.items()}
                # include editable register id if changed
                data["register_id"] = reg_id_var.get()
                try:
                    self.student_model.update_student(student["register_id"], data)
                except ValidationError as e:
                    messagebox.showerror("Validation Error", str(e))
                    return
                except Exception as e:
                    messagebox.showerror("Database Error", str(e))
                    return
                messagebox.showinfo("Success", "Student details updated successfully.")
                load_student()

            btn_frame = tk.Frame(card, bg=ui.COLORS["card_bg"])
            btn_frame.grid(row=7, column=0, columnspan=4, pady=(20, 0), sticky="w")
            ui.make_button(btn_frame, "💾 Save Changes", save_changes,
                            bg=ui.COLORS["secondary"], width=16).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # 7. DELETE STUDENT RECORD
    # ------------------------------------------------------------------
    def show_delete_student(self):
        self._clear_content()
        self._page_header("Delete Student Record", "This action permanently removes the student and their payment history")

        lookup_outer, lookup_card = ui.make_card(self.content, padx=20, pady=15)
        lookup_outer.pack(fill="x", padx=25, pady=(0, 10))

        ui.make_label(lookup_card, "Register ID:").pack(side="left", padx=(0, 10))
        reg_id_var = tk.StringVar()
        entry = ui.make_entry(lookup_card, reg_id_var, width=20)
        entry.pack(side="left", padx=(0, 10))

        details_outer, details_card = ui.make_card(self.content, padx=20, pady=20)
        details_outer.pack(fill="x", padx=25, pady=(0, 20))
        details_label = ui.make_label(details_card, "Enter a Register ID and click 'Load' to preview the record.",
                                       color=ui.COLORS["muted"])
        details_label.pack(anchor="w")

        state = {"student": None}

        def load_student():
            reg_id_text = reg_id_var.get().strip()
            if not reg_id_text.isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid numeric Register ID.")
                return
            student = self.student_model.get_student_by_register_id(int(reg_id_text))
            if not student:
                messagebox.showerror("Not Found", f"No student found with Register ID {reg_id_text}.")
                state["student"] = None
                details_label.config(text="No student loaded.")
                return
            state["student"] = student
            details_label.config(
                text=(f"Register ID: {student['register_id']}\n"
                      f"Name: {student['student_name']}\n"
                      f"Course: {student['course_name']} ({student['course_type']})\n"
                      f"Balance Fees: {student['balance_fees']:.2f}"),
                fg=ui.COLORS["text_dark"]
            )

        def delete_student():
            student = state["student"]
            if not student:
                messagebox.showwarning("No Student Loaded", "Please load a student record first.")
                return
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to permanently delete the record for "
                f"'{student['student_name']}' (Register ID {student['register_id']})?\n\n"
                f"This will also delete all associated payment history. "
                f"This action cannot be undone."
            )
            if not confirm:
                return
            try:
                self.student_model.delete_student(student["register_id"])
            except ValidationError as e:
                messagebox.showerror("Error", str(e))
                return
            messagebox.showinfo("Deleted", "Student record deleted successfully.")
            reg_id_var.set("")
            state["student"] = None
            details_label.config(text="No student loaded.", fg=ui.COLORS["muted"])

        entry.bind("<Return>", lambda e: load_student())
        ui.make_button(lookup_card, "Load", load_student,
                        bg=ui.COLORS["primary"], width=10).pack(side="left", padx=5)
        ui.make_button(lookup_card, "🗑️ Delete Student", delete_student,
                        bg=ui.COLORS["danger"], width=16).pack(side="left", padx=5)


# ===========================================================================
# Application entry point
# ===========================================================================
def main():
    app = StudentManagementApp()
    app.mainloop()


if __name__ == "__main__":
    main()
