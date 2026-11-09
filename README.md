# AttendEase API

AttendEase is a small student attendance project built with Python, Flask and SQLite. It provides API routes to add students, mark attendance and check attendance records.

## Features

- Add a student using a roll number and name
- View all students or one student
- Mark a student present or absent for a date
- View a student's attendance history
- Calculate an attendance percentage
- Prevent duplicate attendance entries for the same student and date

## Requirements

- Python 3.10 or newer
- pip

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000`.

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Check that the API is running |
| POST | `/students` | Add a student |
| GET | `/students` | List students |
| GET | `/students/<roll_number>` | Get one student |
| POST | `/attendance` | Mark attendance |
| GET | `/students/<roll_number>/attendance` | View attendance history |
| GET | `/students/<roll_number>/percentage` | View attendance percentage |

## Example requests

Add a student:

```bash
curl -X POST http://127.0.0.1:5000/students -H "Content-Type: application/json" -d '{"roll_number":"CS101","name":"Aarav"}'
```

Mark attendance:

```bash
curl -X POST http://127.0.0.1:5000/attendance -H "Content-Type: application/json" -d '{"roll_number":"CS101","status":"present"}'
```

Check the percentage:

```bash
curl http://127.0.0.1:5000/students/CS101/percentage
```

You can include a date when marking attendance. Use the `YYYY-MM-DD` format. The SQLite database file is created automatically when the app starts.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Notes

This is a learning project and does not include user login or role-based access yet. Run it locally; do not use Flask's debug server as a public production server.
