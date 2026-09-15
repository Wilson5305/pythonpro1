"""
Simple CLI test to verify updating a student's register_id migrates payments.
Run: python scripts/test_update_register.py
"""
import os
from database import Database
from student import StudentModel

base_dir = os.path.dirname(__file__)
test_db = os.path.join(base_dir, "test_student_management.db")

# start fresh
if os.path.exists(test_db):
    os.remove(test_db)

print(f"Using test DB: {test_db}")

db = Database(test_db)
model = StudentModel(db)

# Create a student
data = {
    "student_name": "Test Student",
    "qualification": "BSc",
    "phone": "9999999999",
    "email": "test@example.com",
    "course_name": "Demo Course",
    "course_type": "Professional Course",
    "total_fees": "1000",
    "paid_amount": "200",
    "batch_start_date": "2026-09-01",
    "faculty_name": "Dr. Demo",
}
old_id = model.add_student(data)
print("Added student with register_id:", old_id)

# Insert a payment linked to the student
db.execute(
    "INSERT INTO payments (register_id, payment_date, payment_method, paid_amount, balance_amount, payment_status) VALUES (?, date('now'), ?, ?, ?, ?)",
    (old_id, 'Cash', 200.0, 800.0, 'Pending')
)
print("Inserted payment for register_id", old_id)

print("Students before update:")
for r in model.get_all_students():
    print(dict(r))

print("Payments before update:")
for p in db.fetch_all("SELECT * FROM payments"):
    print(dict(p))

# Now update the student's register_id
new_id = old_id + 10
student = model.get_student_by_register_id(old_id)
if not student:
    raise SystemExit("Student not found")
# Build update payload from existing values but with new register id
payload = {
    "register_id": str(new_id),
    "student_name": student['student_name'],
    "qualification": student['qualification'] or '',
    "phone": student['phone'],
    "email": student['email'],
    "course_name": student['course_name'],
    "course_type": student['course_type'],
    "total_fees": str(student['total_fees']),
    "paid_amount": str(student['paid_amount']),
    "batch_start_date": student['batch_start_date'] or '',
    "faculty_name": student['faculty_name'] or '',
}

print(f"Updating register_id {old_id} -> {new_id}")
model.update_student(old_id, payload)

print("Students after update:")
for r in model.get_all_students():
    print(dict(r))

print("Payments after update:")
for p in db.fetch_all("SELECT * FROM payments"):
    print(dict(p))

print("Test complete")
