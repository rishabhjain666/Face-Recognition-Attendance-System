import sqlite3
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_connection():
    """Create and return a database connection with autocommit enabled."""
    logging.debug("Creating database connection")
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    logging.debug("Initializing database")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS students (
                name TEXT PRIMARY KEY,
                image_path TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                timestamp TEXT,
                FOREIGN KEY (name) REFERENCES students(name)
            )''')
            logging.debug("Database tables created")
    finally:
        conn.close()

def add_student(name, path):
    """Add a student to the database."""
    logging.debug(f"Adding student: {name}, path: {path}")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO students (name, image_path) VALUES (?, ?)", (name, path))
            logging.debug(f"Student added: {name}")
    finally:
        conn.close()

def get_students():
    """Retrieve all student names from the database."""
    logging.debug("Fetching all students")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT name FROM students")
            students = [row['name'] for row in c.fetchall()]
            logging.debug(f"Fetched students: {students}")
            return students
    finally:
        conn.close()

def mark_attendance(names):
    """Mark attendance for given names with current timestamp."""
    logging.debug(f"Marking attendance for: {names}")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for name in names:
                c.execute("INSERT INTO attendance (name, timestamp) VALUES (?, ?)", (name, time))
            logging.debug("Attendance marked")
    finally:
        conn.close()

def get_attendance():
    """Retrieve all attendance records."""
    logging.debug("Fetching attendance records")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT name, timestamp FROM attendance ORDER BY timestamp DESC")
            records = [(row['name'], row['timestamp']) for row in c.fetchall()]
            logging.debug(f"Fetched {len(records)} attendance records")
            return records
    finally:
        conn.close()

def clear_all_data():
    """Clear all data from students and attendance tables."""
    logging.debug("Clearing all data")
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute("DELETE FROM attendance")
            c.execute("DELETE FROM students")
            logging.debug("All data cleared from database")
    finally:
        conn.close()