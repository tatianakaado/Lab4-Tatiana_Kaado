from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from school_mgmt import Course, DatabaseManager, Instructor, Student, ValidationError


class ModelTests(unittest.TestCase):
    def test_validation_rejects_invalid_age_and_email(self) -> None:
        with self.assertRaises(ValidationError):
            Student("Test", -1, "test@example.com", "S1")
        with self.assertRaises(ValidationError):
            Student("Test", 20, "not-an-email", "S1")

    def test_course_links_student_and_instructor(self) -> None:
        student = Student("Student One", 19, "student@example.com", "S1")
        instructor = Instructor("Instructor One", 40, "instructor@example.com", "I1")
        course = Course("C1", "Course One")
        course.add_student(student)
        course.assign_instructor(instructor)
        self.assertIn("C1", student.registered_courses)
        self.assertIn("S1", course.enrolled_students)
        self.assertIn("C1", instructor.assigned_courses)
        self.assertEqual(course.instructor, "I1")

    def test_polymorphic_introductions(self) -> None:
        people = [
            Student("Student One", 19, "student@example.com", "S1"),
            Instructor("Instructor One", 40, "instructor@example.com", "I1"),
        ]
        introductions = [person.introduce() for person in people]
        self.assertIn("student S1", introductions[0])
        self.assertIn("instructor I1", introductions[1])


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db = DatabaseManager(self.folder / "school.db")
        self.db.add_instructor(Instructor("Instructor One", 40, "instructor@example.com", "I1"))
        self.db.add_course(Course("C1", "Course One", "I1"))
        self.db.add_student(Student("Student One", 19, "student@example.com", "S1", ["C1"]))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_schema_and_relationships(self) -> None:
        self.assertEqual(self.db.students()[0].registered_courses, ["C1"])
        self.assertEqual(self.db.instructors()[0].assigned_courses, ["C1"])
        self.assertEqual(self.db.courses()[0].enrolled_students, ["S1"])
        with self.db.connect() as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"students", "instructors", "courses", "enrollments"}.issubset(tables))

    def test_crud(self) -> None:
        self.db.update_student("S1", Student("Student Updated", 20, "updated@example.com", "S1"))
        self.assertEqual(self.db.students()[0].name, "Student Updated")
        self.db.delete_record("Student", "S1")
        self.assertEqual(self.db.students(), [])

    def test_json_round_trip(self) -> None:
        path = self.db.save_json(self.folder / "data.json")
        payload = json.loads(path.read_text())
        self.assertEqual(payload["courses"][0]["course_id"], "C1")
        second = DatabaseManager(self.folder / "restored.db")
        second.load_json(path)
        self.assertEqual(second.students()[0].registered_courses, ["C1"])

    def test_backup_and_restore(self) -> None:
        backup = self.db.backup(self.folder / "backup.db")
        self.db.delete_record("Student", "S1")
        self.db.restore(backup)
        self.assertEqual(self.db.students()[0].student_id, "S1")

    def test_csv_export(self) -> None:
        paths = self.db.export_csv(self.folder / "csv")
        self.assertEqual(len(paths), 3)
        self.assertTrue(all(path.exists() for path in paths))
        self.assertIn("Student One", paths[0].read_text())


if __name__ == "__main__":
    unittest.main()
