"""JSON serialization and SQLite CRUD operations."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import Course, Instructor, Student, ValidationError


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 0),
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS instructors (
    instructor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 0),
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    instructor_id TEXT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS enrollments (
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
"""


class _ClosingConnection(sqlite3.Connection):
    """SQLite connection that commits/rolls back and closes on context exit.
    """

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Finish the transaction and always release its database handle.
        
        :param exc_type: Exception class, or None on success.
        :type exc_type: type or None
        :param exc_value: Active exception instance.
        :type exc_value: BaseException or None
        :param traceback: Active exception traceback.
        :type traceback: TracebackType or None
        :return: False, allowing any exception to propagate.
        :rtype: bool
        """
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class DatabaseManager:
    """SQLite persistence service for the PyQt school dashboard.
    
    Each operation opens a short-lived connection with foreign keys enabled.
    The context commits on success, rolls back on exceptions, and closes.
    
    :ivar path: SQLite database path.
    :vartype path: pathlib.Path
    
    :param path: Database file; defaults to school.db in the working directory.
    :type path: str or pathlib.Path
    """

    def __init__(self, path: str | Path = "school.db") -> None:
        """Create the database directory and initialize the schema.
        
        :param path: Database filename; defaults to school.db.
        :type path: str or pathlib.Path
        :raises OSError: The parent directory cannot be created.
        :raises sqlite3.Error: The database cannot be initialized.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        """Open a connection with named rows and foreign-key enforcement.
        
        :raises sqlite3.Error: Opening or configuring the database fails.
        :return: A context-managed connection that closes on exit.
        :rtype: sqlite3.Connection
        """
        connection = sqlite3.connect(self.path, factory=_ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create missing students, instructors, courses, and enrollments tables.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def is_empty(self) -> bool:
        """Check whether all three entity tables have no rows.
        
        :return: True only when students, instructors, and courses are all empty.
        :rtype: bool
        """
        with self.connect() as connection:
            return all(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
                for table in ("students", "instructors", "courses")
            )

    def add_student(self, student: Student) -> None:
        """Insert a student and its supplied relationships in one transaction.
        
        :param student: Validated model to insert.
        :type student: Student
        :raises sqlite3.IntegrityError: A key, uniqueness, or relationship constraint fails.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO students(student_id, name, age, email) VALUES (?, ?, ?, ?)",
                (student.student_id, student.name, student.age, student.email),
            )
            connection.executemany(
                "INSERT OR IGNORE INTO enrollments(student_id, course_id) VALUES (?, ?)",
                ((student.student_id, course_id) for course_id in student.registered_courses),
            )

    def add_instructor(self, instructor: Instructor) -> None:
        """Insert a instructor and its supplied relationships in one transaction.
        
        :param instructor: Validated model to insert.
        :type instructor: Instructor
        :raises sqlite3.IntegrityError: A key, uniqueness, or relationship constraint fails.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO instructors(instructor_id, name, age, email) VALUES (?, ?, ?, ?)",
                (instructor.instructor_id, instructor.name, instructor.age, instructor.email),
            )
            connection.executemany(
                "UPDATE courses SET instructor_id = ? WHERE course_id = ?",
                ((instructor.instructor_id, course_id) for course_id in instructor.assigned_courses),
            )

    def add_course(self, course: Course) -> None:
        """Insert a course and its supplied relationships in one transaction.
        
        :param course: Validated model to insert.
        :type course: Course
        :raises sqlite3.IntegrityError: A key, uniqueness, or relationship constraint fails.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO courses(course_id, course_name, instructor_id) VALUES (?, ?, ?)",
                (course.course_id, course.course_name, course.instructor),
            )
            connection.executemany(
                "INSERT OR IGNORE INTO enrollments(student_id, course_id) VALUES (?, ?)",
                ((student_id, course.course_id) for student_id in course.enrolled_students),
            )

    def register_student(self, student_id: str, course_id: str) -> None:
        """Create a student/course enrollment; repeated registration is harmless.
        
        :param student_id: Existing student ID.
        :type student_id: str
        :param course_id: Existing course ID.
        :type course_id: str
        :raises sqlite3.IntegrityError: A referenced record does not exist.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO enrollments(student_id, course_id) VALUES (?, ?)",
                (student_id, course_id),
            )

    def assign_instructor(self, instructor_id: str | None, course_id: str) -> None:
        """Assign or clear the single instructor stored on a course.
        
        Instructor course lists are derived from this foreign key when fetched;
        reassignment cannot leave a stale database link.
        
        :param instructor_id: Existing instructor ID, or None to unassign.
        :type instructor_id: str or None
        :param course_id: Course ID to update; no match makes no change.
        :type course_id: str
        :raises sqlite3.IntegrityError: The instructor does not exist.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "UPDATE courses SET instructor_id = ? WHERE course_id = ?",
                (instructor_id, course_id),
            )

    def update_student(self, old_id: str, student: Student) -> None:
        """Update an existing student by its original identifier.
        
        Primary-key changes cascade to referencing records. Relationship lists
        on the supplied model are not used by this update operation.
        
        :param old_id: Identifier to match; no match leaves records unchanged.
        :type old_id: str
        :param student: Replacement scalar fields.
        :type student: Student
        :raises sqlite3.IntegrityError: An updated value violates a database constraint.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "UPDATE students SET student_id=?, name=?, age=?, email=? WHERE student_id=?",
                (student.student_id, student.name, student.age, student.email, old_id),
            )

    def update_instructor(self, old_id: str, instructor: Instructor) -> None:
        """Update an existing instructor by its original identifier.
        
        Primary-key changes cascade to referencing records. Relationship lists
        on the supplied model are not used by this update operation.
        
        :param old_id: Identifier to match; no match leaves records unchanged.
        :type old_id: str
        :param instructor: Replacement scalar fields.
        :type instructor: Instructor
        :raises sqlite3.IntegrityError: An updated value violates a database constraint.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "UPDATE instructors SET instructor_id=?, name=?, age=?, email=? WHERE instructor_id=?",
                (instructor.instructor_id, instructor.name, instructor.age, instructor.email, old_id),
            )

    def update_course(self, old_id: str, course: Course) -> None:
        """Update an existing course by its original identifier.
        
        Updates the course name, identifier, and instructor. Enrollment links
        remain in place; identifier changes cascade through foreign keys.
        
        :param old_id: Identifier to match; no match leaves records unchanged.
        :type old_id: str
        :param course: Replacement scalar fields.
        :type course: Course
        :raises sqlite3.IntegrityError: An updated value violates a database constraint.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        with self.connect() as connection:
            connection.execute(
                "UPDATE courses SET course_id=?, course_name=?, instructor_id=? WHERE course_id=?",
                (course.course_id, course.course_name, course.instructor, old_id),
            )

    def delete_record(self, record_type: str, record_id: str) -> None:
        """Delete one allowed record type and apply foreign-key cleanup.
        
        Removing a student/course deletes its enrollments. Removing an instructor
        sets affected courses to unassigned. A missing record is a no-op.
        
        :param record_type: Student, Instructor, or Course.
        :type record_type: str
        :param record_id: Identifier to remove.
        :type record_id: str
        :raises ValueError: The record type is not allowed.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        tables = {"Student": ("students", "student_id"), "Instructor": ("instructors", "instructor_id"), "Course": ("courses", "course_id")}
        if record_type not in tables:
            raise ValueError(f"Unknown record type: {record_type}")
        table, id_column = tables[record_type]
        with self.connect() as connection:
            connection.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (record_id,))

    def students(self) -> list[Student]:
        """Fetch all students and their current relationship IDs.
        
        :return: New model objects sorted by identifier.
        :rtype: list[Student]
        """
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT s.*, GROUP_CONCAT(e.course_id) AS courses
                   FROM students s LEFT JOIN enrollments e ON e.student_id=s.student_id
                   GROUP BY s.student_id ORDER BY s.student_id"""
            ).fetchall()
        return [Student(r["name"], r["age"], r["email"], r["student_id"], self._split(r["courses"])) for r in rows]

    def instructors(self) -> list[Instructor]:
        """Fetch all instructors and their current relationship IDs.
        
        :return: New model objects sorted by identifier.
        :rtype: list[Instructor]
        """
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT i.*, GROUP_CONCAT(c.course_id) AS courses
                   FROM instructors i LEFT JOIN courses c ON c.instructor_id=i.instructor_id
                   GROUP BY i.instructor_id ORDER BY i.instructor_id"""
            ).fetchall()
        return [Instructor(r["name"], r["age"], r["email"], r["instructor_id"], self._split(r["courses"])) for r in rows]

    def courses(self) -> list[Course]:
        """Fetch all courses and their current relationship IDs.
        
        :return: New model objects sorted by identifier.
        :rtype: list[Course]
        """
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT c.*, GROUP_CONCAT(e.student_id) AS students
                   FROM courses c LEFT JOIN enrollments e ON e.course_id=c.course_id
                   GROUP BY c.course_id ORDER BY c.course_id"""
            ).fetchall()
        return [Course(r["course_id"], r["course_name"], r["instructor_id"], self._split(r["students"])) for r in rows]

    @staticmethod
    def _split(value: str | None) -> list[str]:
        """Decode a comma-separated aggregate from a relationship query.
        
        The existing Lab 2 aggregation assumes identifiers do not contain commas.
        
        :param value: GROUP_CONCAT output, or None.
        :type value: str or None
        :return: Split IDs, or an empty list.
        :rtype: list[str]
        """
        return value.split(",") if value else []

    def all_rows(self, query: str = "") -> list[tuple[str, str, str, str, str]]:
        """Build display rows and optionally filter them by case-insensitive text.
        
        :param query: Substring to search across displayed fields; defaults to empty.
        :type query: str
        :return: Rows containing category, ID, name, email/instructor, and relationships.
        :rtype: list[tuple[str, str, str, str, str]]
        """
        needle = query.strip().casefold()
        rows: list[tuple[str, str, str, str, str]] = []
        for student in self.students():
            rows.append(("Student", student.student_id, student.name, student.email, ", ".join(student.registered_courses) or "—"))
        for instructor in self.instructors():
            rows.append(("Instructor", instructor.instructor_id, instructor.name, instructor.email, ", ".join(instructor.assigned_courses) or "—"))
        for course in self.courses():
            rows.append(("Course", course.course_id, course.course_name, course.instructor or "Unassigned", ", ".join(course.enrolled_students) or "—"))
        if not needle:
            return rows
        return [row for row in rows if needle in " ".join(row).casefold()]

    def to_payload(self) -> dict[str, list[dict]]:
        """Collect all models in the JSON interchange structure.
        
        :return: students, instructors, and courses lists.
        :rtype: dict[str, list[dict]]
        """
        return {
            "students": [item.to_dict() for item in self.students()],
            "instructors": [item.to_dict() for item in self.instructors()],
            "courses": [item.to_dict() for item in self.courses()],
        }

    def save_json(self, path: str | Path) -> Path:
        """Write all records as indented UTF-8 JSON.
        
        :param path: Destination file; parent directory must exist.
        :type path: str or pathlib.Path
        :raises OSError: The destination cannot be written.
        :return: Destination path.
        :rtype: pathlib.Path
        """
        destination = Path(path)
        destination.write_text(json.dumps(self.to_payload(), indent=2), encoding="utf-8")
        return destination

    def load_json(self, path: str | Path) -> None:
        """Validate JSON and replace all records in one rollback-safe transaction.
        
        All three top-level lists are required; empty lists explicitly clear the
        database. Enrollments are the union of student and course declarations.
        Instructor declarations are merged only if consistent with course assignments.
        Parsing and model validation happen before deletion; all database writes
        share one transaction. Any failure preserves the previous records.
        
        :param path: UTF-8 JSON file with students, instructors, and courses lists.
        :type path: str or pathlib.Path
        :raises OSError: The source cannot be read.
        :raises json.JSONDecodeError: The file is not valid JSON.
        :raises ValidationError: The structure, fields, or instructor relationships are invalid.
        :raises sqlite3.IntegrityError: Duplicate IDs/emails or missing relationship targets violate constraints.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not all(
            key in payload and isinstance(payload[key], list)
            for key in ("students", "instructors", "courses")
        ):
            raise ValidationError("JSON must contain students, instructors and courses lists.")
        try:
            for key, relation in (("students", "registered_courses"),
                                  ("instructors", "assigned_courses"),
                                  ("courses", "enrolled_students")):
                for item in payload[key]:
                    if not isinstance(item, dict):
                        raise ValidationError(f"Each {key} entry must be an object.")
                    if not isinstance(item.get(relation, []), list) or not all(
                        isinstance(value, str) and value.strip()
                        for value in item.get(relation, [])
                    ):
                        raise ValidationError(f"{relation} must be a list of nonempty IDs.")
            students = [Student.from_dict(item) for item in payload["students"]]
            instructors = [Instructor.from_dict(item) for item in payload["instructors"]]
            courses = [Course.from_dict(item) for item in payload["courses"]]
            course_map = {course.course_id: course for course in courses}
            for instructor in instructors:
                for course_id in instructor.assigned_courses:
                    if course_id not in course_map:
                        raise ValidationError(f"Unknown assigned course: {course_id}")
                    course = course_map[course_id]
                    if course.instructor not in (None, instructor.instructor_id):
                        raise ValidationError(f"Conflicting instructor for course: {course_id}")
                    course.instructor = instructor.instructor_id
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValidationError(f"Invalid JSON record: {exc}") from exc
        # Deletion and every insertion share one transaction: any error rolls back.
        with self.connect() as connection:
            connection.execute("DELETE FROM enrollments")
            connection.execute("DELETE FROM courses")
            connection.execute("DELETE FROM students")
            connection.execute("DELETE FROM instructors")
            connection.executemany(
                "INSERT INTO instructors VALUES (?, ?, ?, ?)",
                [(i.instructor_id, i.name, i.age, i.email) for i in instructors],
            )
            connection.executemany(
                "INSERT INTO courses VALUES (?, ?, ?)",
                [(c.course_id, c.course_name, c.instructor) for c in courses],
            )
            connection.executemany(
                "INSERT INTO students VALUES (?, ?, ?, ?)",
                [(s.student_id, s.name, s.age, s.email) for s in students],
            )
            enrollments = {
                (s.student_id, course_id)
                for s in students for course_id in s.registered_courses
            } | {
                (student_id, c.course_id)
                for c in courses for student_id in c.enrolled_students
            }
            connection.executemany(
                "INSERT INTO enrollments VALUES (?, ?)", sorted(enrollments),
            )

    def backup(self, destination: str | Path) -> Path:
        """Create a consistent SQLite backup, creating parent directories as needed.
        
        :param destination: Backup file; an existing destination is overwritten.
        :type destination: str or pathlib.Path
        :raises OSError: The directory cannot be created.
        :raises sqlite3.Error: The database backup fails.
        :return: Written backup path.
        :rtype: pathlib.Path
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, sqlite3.connect(destination, factory=_ClosingConnection) as target:
            source.backup(target)
        return destination

    def restore(self, source: str | Path) -> None:
        """Replace the database with an existing SQLite backup.
        
        The GUI asks for confirmation before calling this method. This operation
        replaces current records; use a backup created by this application.
        
        :param source: Backup database to restore.
        :type source: str or pathlib.Path
        :raises FileNotFoundError: The source path does not exist.
        :raises sqlite3.Error: The source is invalid or copying fails.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        with sqlite3.connect(source, factory=_ClosingConnection) as backup, self.connect() as target:
            backup.backup(target)
        self.initialize()

    def export_csv(self, directory: str | Path) -> list[Path]:
        """Write one CSV file per entity, joining relationship IDs with commas.
        
        A dataset with no records produces an empty file. Existing files are overwritten.
        
        :param directory: Output directory, created if needed.
        :type directory: str or pathlib.Path
        :raises OSError: An output file or directory cannot be written.
        :return: students.csv, instructors.csv, and courses.csv paths.
        :rtype: list[pathlib.Path]
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        datasets: Iterable[tuple[str, list[dict]]] = (
            ("students.csv", [item.to_dict() for item in self.students()]),
            ("instructors.csv", [item.to_dict() for item in self.instructors()]),
            ("courses.csv", [item.to_dict() for item in self.courses()]),
        )
        for filename, records in datasets:
            path = directory / filename
            fieldnames = list(records[0]) if records else []
            with path.open("w", newline="", encoding="utf-8") as handle:
                if fieldnames:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    for record in records:
                        writer.writerow({key: ", ".join(value) if isinstance(value, list) else value for key, value in record.items()})
            outputs.append(path)
        return outputs

    def seed_demo(self) -> None:
        """Populate sample instructors, courses, and students only if storage is empty.
        
        Returns without changing a database that contains any entity records.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        if not self.is_empty():
            return
        instructors = [
            Instructor("Dr. Lina Haddad", 41, "lina.haddad@aub.edu.lb", "I001"),
            Instructor("Dr. Karim Nasser", 38, "karim.nasser@aub.edu.lb", "I002"),
        ]
        for instructor in instructors:
            self.add_instructor(instructor)
        courses = [
            Course("EECE435L", "Software Tools Laboratory", "I001"),
            Course("EECE330", "Data Structures", "I002"),
            Course("EECE340", "Signals and Systems", "I001"),
        ]
        for course in courses:
            self.add_course(course)
        students = [
            Student("Tatiana Kaado", 21, "tgk12@mail.aub.edu", "202400900", ["EECE435L", "EECE330"]),
            Student("Maya Khoury", 20, "maya.khoury@mail.aub.edu", "S2026002", ["EECE435L"]),
            Student("Omar Saleh", 22, "omar.saleh@mail.aub.edu", "S2026003", ["EECE340"]),
        ]
        for student in students:
            self.add_student(student)
