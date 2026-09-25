"""
payment.py
----------
Model + View for the Course Payment module.

Model:  PaymentModel       -> all database operations for the `payments` table
View:   PaymentWindow       -> Tkinter Toplevel implementing the Payment Entry
                               screen described in the spec (student lookup,
                               fee summary, payment entry, balance recalculation,
                               and the "Fully Paid" certificate-eligible popup).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from student import StudentModel, ValidationError
import ui_helpers as ui

PAYMENT_METHODS = ["Cash", "UPI", "Bank Transfer", "Card"]


class PaymentError(Exception):
    """Raised when a payment operation fails validation."""
    pass


class PaymentModel:
    """All database operations related to Payment transactions."""

    def __init__(self, db):
        self.db = db

    def validate_payment_amount(self, amount):
        """Ensures the entered payment amount is a positive number."""
        try:
            value = float(amount)
        except (TypeError, ValueError):
            raise PaymentError("Paid amount must be a valid number.")
        if value <= 0:
            raise PaymentError("Paid amount must be greater than zero.")
        return value

    def record_payment(self, register_id, payment_date, payment_method,
                        paid_amount, balance_amount, payment_status):
        """
        Inserts a row into the payments history table.
        Called after StudentModel.apply_payment() has already updated
        the running totals on the students table.
        """
        if payment_method not in PAYMENT_METHODS:
            raise PaymentError("Invalid payment method selected.")

        self.db.execute("""
            INSERT INTO payments (
                register_id, payment_date, payment_method,
                paid_amount, balance_amount, payment_status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (register_id, payment_date, payment_method,
              paid_amount, balance_amount, payment_status))

    def get_payment_history(self, register_id):
        """Returns all payment transactions for a given student, most recent first."""
        return self.db.fetch_all("""
            SELECT * FROM payments
            WHERE register_id = ?
            ORDER BY payment_id DESC
        """, (register_id,))

    def get_all_payments(self):
        """Returns all payment transactions across all students (for reports)."""
        return self.db.fetch_all("SELECT * FROM payments ORDER BY payment_id DESC")

    @staticmethod
    def today():
        """Convenience: today's date as a string, used to default the Payment Date field."""
        return datetime.now().strftime("%Y-%m-%d")


# ===========================================================================
# VIEW: Course Payment Module window
# ===========================================================================
class PaymentWindow(tk.Frame):
    """
    Embedded payment module shown inside the main application shell.
      1. Student lookup by Register ID
      2. Display of Register ID, Name, Course, Total Fees, Previous Paid, Balance
      3. Payment entry fields (amount, date, method)
      4. Recalculates Paid/Balance, updates payment_status
      5. Records the transaction into the Payments history table
    """

    def __init__(self, master, db, on_payment_made=None):
        super().__init__(master, bg=ui.COLORS["bg"])
        self.db = db
        self.student_model = StudentModel(db)
        self.payment_model = PaymentModel(db)
        self.on_payment_made = on_payment_made  # callback to refresh other screens
        self.current_student = None

        self.pack(fill="both", expand=True)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ui.COLORS["primary"], height=60)
        header.pack(fill="x")
        tk.Label(header, text="Make Course Payment", bg=ui.COLORS["primary"],
                  fg="white", font=ui.FONTS["heading"]).pack(side="left", padx=20, pady=15)

        body = tk.Frame(self, bg=ui.COLORS["bg"], padx=20, pady=15)
        body.pack(fill="both", expand=True)

        # ---- Student lookup ----
        lookup_card_outer, lookup_card = ui.make_card(body)
        lookup_card_outer.pack(fill="x", pady=(0, 12))

        ui.make_label(lookup_card, "Search Student:", bold=True).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.search_widget = ui.LiveStudentSearch(
            lookup_card,
            self.student_model,
            on_select=lambda student: self._load_student_record(student),
            width=28,
        )
        self.search_widget.frame.grid(row=0, column=1, sticky="ew", pady=5)
        lookup_card.grid_columnconfigure(1, weight=1)

        # ---- Student / fee summary ----
        summary_outer, summary_card = ui.make_card(body)
        summary_outer.pack(fill="x", pady=(0, 12))

        self.summary_labels = {}
        fields = [
            ("Register ID", "register_id"), ("Student Name", "student_name"),
            ("Course Name", "course_name"), ("Total Fees", "total_fees"),
            ("Previous Paid Amount", "paid_amount"), ("Current Balance", "balance_fees"),
        ]
        for i, (label_text, key) in enumerate(fields):
            ui.make_label(summary_card, f"{label_text}:", bold=True).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=4)
            val_lbl = ui.make_label(summary_card, "--")
            val_lbl.grid(row=i, column=1, sticky="w", pady=4)
            self.summary_labels[key] = val_lbl

        # ---- Payment entry ----
        entry_outer, entry_card = ui.make_card(body)
        entry_outer.pack(fill="x", pady=(0, 12))

        ui.make_label(entry_card, "Payment Entry", bold=True, size=12).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ui.make_label(entry_card, "Paid Amount:").grid(row=1, column=0, sticky="w", pady=6)
        self.paid_amount_var = tk.StringVar()
        ui.make_entry(entry_card, self.paid_amount_var, width=25).grid(
            row=1, column=1, sticky="w", pady=6)

        ui.make_label(entry_card, "Payment Date (YYYY-MM-DD):").grid(
            row=2, column=0, sticky="w", pady=6)
        self.payment_date_var = tk.StringVar(value=PaymentModel.today())
        ui.make_entry(entry_card, self.payment_date_var, width=25).grid(
            row=2, column=1, sticky="w", pady=6)

        ui.make_label(entry_card, "Payment Method:").grid(row=3, column=0, sticky="w", pady=6)
        self.payment_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        method_combo = ttk.Combobox(entry_card, textvariable=self.payment_method_var,
                                     values=PAYMENT_METHODS, state="readonly", width=23)
        method_combo.grid(row=3, column=1, sticky="w", pady=6)

        # ---- Action buttons ----
        btn_frame = tk.Frame(body, bg=ui.COLORS["bg"])
        btn_frame.pack(fill="x", pady=10)
        ui.make_button(btn_frame, "Submit Payment", self._submit_payment,
                        bg=ui.COLORS["secondary"], width=16).pack(side="left", padx=5)
        ui.make_button(btn_frame, "Clear", self._clear_form,
                        bg=ui.COLORS["muted"], width=10).pack(side="left", padx=5)
        ui.make_button(btn_frame, "Close", self.destroy,
                        bg=ui.COLORS["danger"], width=10).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    def _lookup_student(self):
        """Legacy fallback for manual ID lookup; kept for compatibility."""
        reg_id_text = getattr(self, "register_id_var", tk.StringVar()).get().strip()
        if not reg_id_text.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid numeric Register ID.")
            return

        student = self.student_model.get_student_by_register_id(int(reg_id_text))
        if student:
            self._load_student_record(student)

    def _load_student_record(self, student):
        """Populate the fee summary for the selected student."""
        self.current_student = student

        if hasattr(self, "register_id_var"):
            self.register_id_var.set(str(student["register_id"]))

        self.summary_labels["register_id"].config(text=str(student["register_id"]))
        self.summary_labels["student_name"].config(text=student["student_name"])
        self.summary_labels["course_name"].config(text=student["course_name"])
        self.summary_labels["total_fees"].config(text=f"{student['total_fees']:.2f}")
        self.summary_labels["paid_amount"].config(text=f"{student['paid_amount']:.2f}")
        self.summary_labels["balance_fees"].config(text=f"{student['balance_fees']:.2f}")

        # Keep the student lookup and payment functionality intact without
        # showing an unsolicited payment/certificate popup when the balance is zero.

    def _submit_payment(self):
        """Validates and submits the payment, updating both tables."""
        if not self.current_student:
            messagebox.showerror("No Student Selected", "Please look up a student first.")
            return

        register_id = self.current_student["register_id"]

        try:
            amount = self.payment_model.validate_payment_amount(self.paid_amount_var.get())
            payment_date = self.payment_date_var.get().strip()
            if not payment_date:
                raise PaymentError("Payment date is required.")
            # Basic date sanity check
            datetime.strptime(payment_date, "%Y-%m-%d")

            method = self.payment_method_var.get()

            # Update the student's running totals (Paid/Balance/Status)
            new_paid, new_balance, status = self.student_model.apply_payment(
                register_id, amount)

            # Record the transaction in payment history
            self.payment_model.record_payment(
                register_id, payment_date, method, amount, new_balance, status)

        except (PaymentError, ValidationError) as e:
            messagebox.showerror("Payment Error", str(e))
            return
        except ValueError:
            messagebox.showerror("Invalid Date", "Payment date must be in YYYY-MM-DD format.")
            return

        # Refresh summary card with updated values
        self.summary_labels["paid_amount"].config(text=f"{new_paid:.2f}")
        self.summary_labels["balance_fees"].config(text=f"{new_balance:.2f}")

        messagebox.showinfo("Payment Recorded",
                             f"Payment of {amount:.2f} recorded successfully.\n"
                             f"New Balance: {new_balance:.2f}")

        # Do not trigger a certificate eligibility popup automatically when a
        # payment clears the balance. The certificate screen remains available
        # through the explicit UI action and is not forced on the user.

        if self.on_payment_made:
            self.on_payment_made()

        self.paid_amount_var.set("")

    def _clear_form(self):
        if hasattr(self, "register_id_var"):
            self.register_id_var.set("")
        self.search_widget.var.set("")
        self.search_widget._set_placeholder()
        self.paid_amount_var.set("")
        self.payment_date_var.set(PaymentModel.today())
        self.payment_method_var.set(PAYMENT_METHODS[0])
        self.current_student = None
        for lbl in self.summary_labels.values():
            lbl.config(text="--")
