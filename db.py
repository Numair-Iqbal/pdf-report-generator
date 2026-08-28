"""
db.py — SQLite connection + table setup.

Yahan hum ek hi file (report.db) use kar rahe hain jo poori "database" hai.
SQLite ke liye Python mein built-in 'sqlite3' module hai — kuch install nahi karna.
"""
import sqlite3

DB_PATH = "report.db"


def get_connection():
    """Har baar ek nayi connection deta hai. row_factory se rows dict jaisi milti hain."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tables banata hai agar pehle se nahi hain (safe to run multiple times)."""
    conn = get_connection()
    cur = conn.cursor()

    # orders table: hamara "raw data" jis par hum report banayenge
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # reports table: har generated PDF ka record (bookkeeping)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
