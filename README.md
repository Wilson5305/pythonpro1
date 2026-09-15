# Student Course Management System

A complete desktop application for managing student admissions, course
fees, payments, and certificate eligibility — built with **Python**,
**Tkinter**, and **SQLite**, following an MVC-style structure.

## Features

1. **Add New Student** — admission form with auto-generated Register ID
   (starts at 1000, auto-increments), auto-filled Admission Date, course
   details, and fee details with live Balance Fees calculation.
2. **View All Students** — sortable grid with search, Course Type filter,
   Payment Status filter, inline Batch/Faculty info editing, and Excel
   export.
3. **Make Course Payment** — look up a student, enter a new payment
   (Cash / UPI / Bank Transfer / Card), automatically recalculates the
   Paid Amount and Balance, records the transaction in a payment history
   table, and pops up **"Student is eligible for Course Completion
   Certificate."** the moment the balance reaches zero.
4. **Certificate Eligibility** — lists only fully-paid students, with
   checkbox single/multi-select, list generation, Excel export, and a
   browser-based Print option.
5. **Search Student** — search by Register ID, name, phone, or email.
6. **Edit Student Details** — look up by Register ID and update any field;
   fees and balance recalculate live.
7. **Delete Student Record** — preview before permanently deleting a
   student and their full payment history.

## Requirements

- Python 3.8+
- Tkinter (bundled with most Python installs; on Linux you may need to
  install it separately, e.g. `sudo apt-get install python3-tk`)
- `openpyxl` (for Excel export)

Install the external dependencies:

```bash
pip install openpyxl tkcalendar
```

## Project Structure

```
student_course_management/
├── main.py            # Entry point, dashboard, Add/View/Search/Edit/Delete screens
├── database.py        # SQLite connection + schema creation
├── student.py          # Student model: validation + CRUD
├── payment.py          # Payment model + "Make Course Payment" GUI window
├── certificate.py      # "Certificate Eligibility" GUI window
├── reports.py           # Excel export + printable certificate list (HTML)
├── ui_helpers.py        # Shared colors, fonts, and reusable widget factories
├── student_management.db  # Created automatically on first run
├── exports/              # Excel files exported by the app
└── certificates/          # Printable HTML certificate lists
```

## Running the application

```bash
cd student_course_management
python main.py
```

The SQLite database file `student_management.db` is created automatically
on first launch, with all required tables (`students`, `payments`,
`settings`).

## Database Schema

**students**
`id, register_id, admission_date, student_name, qualification, phone,
email, course_name, course_type, total_fees, paid_amount, balance_fees,
batch_start_date, faculty_name, payment_status`

**payments**
`payment_id, register_id, payment_date, payment_method, paid_amount,
balance_amount, payment_status`

**settings**
Internal table used to persist the next auto-generated Register ID.

## Validation Rules

- Phone number must be exactly **10 digits**.
- Email must match a standard email format.
- Student Name, Course Name, Course Type, Total Fees, and Paid Amount are
  required and cannot be empty.
- Paid Amount can never exceed Total Fees (enforced both on admission and
  on every subsequent payment).

## Notes

- Course Type options: Slash Course (1 Month), Crash Course (1.5 Months),
  Professional Course, Tesbo Course, ThoorigAI Course - Course, ThoorigAI
  Course - Internship.
- Faculty contact shown in the sidebar and on the Add Student form:
  `thoorigaifaculty@gmail.com`.
- "Print" in the Certificate Eligibility module opens a print-friendly
  HTML page in your default browser; use Ctrl+P (or the on-page Print
  button) to print, since this is the standard cross-platform way to
  print from a Tkinter desktop app without extra OS-specific dependencies.
