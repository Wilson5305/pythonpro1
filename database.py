"""
database.py
------------
Handles all SQLite database connectivity, schema creation, and low-level
query execution for the Student Course Management System.

This module is intentionally kept free of any GUI code so it can be
reused/tested independently (clean separation for the MVC structure).
"""

import sqlite3
import os

# Database file is stored alongside the source code.
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_management.db")


class Database:
    """
    Thin wrapper around sqlite3 that:
      - Creates tables if they do not already exist.
      - Provides helper methods (execute/fetch) used by model classes.
      - Centralizes PRAGMA settings (foreign keys, etc.)
    """

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self._create_tables()

    def get_connection(self):
        """
        Returns a new sqlite3 connection with foreign keys enabled.
        A new connection per call keeps this safe to use from multiple
        Toplevel windows in the Tkinter app without threading issues.
        """
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # allows dict-like access to rows
        return conn

    def _create_tables(self):
        """Creates the Students and Payments tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # ---------------- STUDENTS TABLE ----------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                register_id INTEGER UNIQUE NOT NULL,
                admission_date TEXT NOT NULL,
                student_name TEXT NOT NULL,
                qualification TEXT,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                course_name TEXT NOT NULL,
                course_type TEXT NOT NULL,
                total_fees REAL NOT NULL DEFAULT 0,
                paid_amount REAL NOT NULL DEFAULT 0,
                balance_fees REAL NOT NULL DEFAULT 0,
                batch_start_date TEXT,
                faculty_name TEXT,
                payment_status TEXT NOT NULL DEFAULT 'Pending'
            )
        """)

        # ---------------- PAYMENTS TABLE ----------------
        # register_id references students.register_id (business key),
        # which is what the rest of the application uses to look students up.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                register_id INTEGER NOT NULL,
                payment_date TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                paid_amount REAL NOT NULL,
                balance_amount REAL NOT NULL,
                payment_status TEXT NOT NULL,
                FOREIGN KEY (register_id) REFERENCES students (register_id)
                    ON DELETE CASCADE
            )
        """)

        # ---------------- SETTINGS TABLE ----------------
        # Used to persist the "next register id" counter so that numbering
        # starts at 1000 and increments correctly even after deletions.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('next_register_id', '1000')
        """)

        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Generic helper methods used by model classes (student.py, payment.py)
    # ------------------------------------------------------------------

    def execute(self, query, params=()):
        """
        Executes an INSERT/UPDATE/DELETE statement.
        Returns the lastrowid (useful for INSERTs).
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def execute_transaction(self, statements):
        """
        Executes multiple (query, params) statements inside a single
        transaction on one connection. `statements` should be an iterable
        of (query, params) tuples. Returns True on success.
        """
        # Use an explicit connection here so we can control PRAGMA foreign_keys
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            # Temporarily disable foreign key enforcement for this migration
            cursor.execute("PRAGMA foreign_keys = OFF;")
            for query, params in statements:
                cursor.execute(query, params)
            conn.commit()
            # Restore foreign keys for the connection (no effect after commit,
            # but keeps behavior consistent if the connection were reused)
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
            except Exception:
                pass
            return True
        finally:
            conn.close()

    def fetch_all(self, query, params=()):
        """Executes a SELECT and returns all matching rows as a list of sqlite3.Row."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        """Executes a SELECT and returns a single row (or None)."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            conn.close()
