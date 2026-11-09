import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from flask import Flask, jsonify, request

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), "attendance.db")


@contextmanager
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
                UNIQUE(student_id, attendance_date),
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """)


def student_to_dict(student):
    return {"id": student["id"], "roll_number": student["roll_number"], "name": student["name"]}


@app.get("/")
def home():
    return jsonify({"message": "AttendEase API is running"})


@app.post("/students")
def add_student():
    data = request.get_json(silent=True) or {}
    roll_number = str(data.get("roll_number", "")).strip()
    name = str(data.get("name", "")).strip()
    if not roll_number or not name:
        return jsonify({"error": "roll_number and name are required"}), 400
    try:
        with get_db() as connection:
            cursor = connection.execute(
                "INSERT INTO students (roll_number, name) VALUES (?, ?)", (roll_number, name)
            )
            student_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "A student with this roll number already exists"}), 409
    return jsonify({"message": "Student added", "student": {
        "id": student_id, "roll_number": roll_number, "name": name
    }}), 201


@app.get("/students")
def get_students():
    with get_db() as connection:
        students = connection.execute(
            "SELECT id, roll_number, name FROM students ORDER BY roll_number"
        ).fetchall()
    return jsonify([student_to_dict(student) for student in students])


@app.get("/students/<roll_number>")
def get_student(roll_number):
    with get_db() as connection:
        student = connection.execute(
            "SELECT id, roll_number, name FROM students WHERE roll_number = ?", (roll_number,)
        ).fetchone()
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student_to_dict(student))


@app.post("/attendance")
def mark_attendance():
    data = request.get_json(silent=True) or {}
    roll_number = str(data.get("roll_number", "")).strip()
    attendance_date = str(data.get("date", date.today().isoformat())).strip()
    status = str(data.get("status", "present")).strip().lower()
    if not roll_number:
        return jsonify({"error": "roll_number is required"}), 400
    if status not in ("present", "absent"):
        return jsonify({"error": "status must be present or absent"}), 400
    try:
        date.fromisoformat(attendance_date)
    except ValueError:
        return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    with get_db() as connection:
        student = connection.execute(
            "SELECT id FROM students WHERE roll_number = ?", (roll_number,)
        ).fetchone()
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        try:
            connection.execute(
                "INSERT INTO attendance (student_id, attendance_date, status) VALUES (?, ?, ?)",
                (student["id"], attendance_date, status)
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "Attendance has already been marked for this date"}), 409
    return jsonify({"message": "Attendance marked", "roll_number": roll_number,
                    "date": attendance_date, "status": status}), 201


@app.get("/students/<roll_number>/attendance")
def get_attendance(roll_number):
    with get_db() as connection:
        student = connection.execute(
            "SELECT id FROM students WHERE roll_number = ?", (roll_number,)
        ).fetchone()
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        records = connection.execute(
            "SELECT attendance_date, status FROM attendance WHERE student_id = ? ORDER BY attendance_date",
            (student["id"],)
        ).fetchall()
    return jsonify([{"date": row["attendance_date"], "status": row["status"]} for row in records])


@app.get("/students/<roll_number>/percentage")
def attendance_percentage(roll_number):
    with get_db() as connection:
        student = connection.execute(
            "SELECT id FROM students WHERE roll_number = ?", (roll_number,)
        ).fetchone()
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        result = connection.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present "
            "FROM attendance WHERE student_id = ?", (student["id"],)
        ).fetchone()
    total = result["total"]
    present = result["present"] or 0
    percentage = round((present / total) * 100, 2) if total else 0.0
    return jsonify({"roll_number": roll_number, "total_classes": total,
                    "present": present, "absent": total - present,
                    "attendance_percentage": percentage})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
