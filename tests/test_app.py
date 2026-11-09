import os
import tempfile
import unittest

import app as attendance_app


class AttendanceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        attendance_app.DATABASE = os.path.join(self.temp_dir.name, "test.db")
        attendance_app.init_db()
        self.client = attendance_app.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_student(self):
        return self.client.post("/students", json={"roll_number": "CS101", "name": "Aarav"})

    def test_add_and_get_student(self):
        response = self.add_student()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/students/CS101").json["name"], "Aarav")

    def test_duplicate_roll_number_is_rejected(self):
        self.add_student()
        self.assertEqual(self.add_student().status_code, 409)

    def test_attendance_percentage(self):
        self.add_student()
        self.client.post("/attendance", json={"roll_number": "CS101", "date": "2026-11-01", "status": "present"})
        self.client.post("/attendance", json={"roll_number": "CS101", "date": "2026-11-02", "status": "absent"})
        response = self.client.get("/students/CS101/percentage")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["attendance_percentage"], 50.0)

    def test_duplicate_attendance_is_rejected(self):
        self.add_student()
        payload = {"roll_number": "CS101", "date": "2026-11-01", "status": "present"}
        self.assertEqual(self.client.post("/attendance", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/attendance", json=payload).status_code, 409)


if __name__ == "__main__":
    unittest.main()
