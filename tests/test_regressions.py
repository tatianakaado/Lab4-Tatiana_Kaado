"""Regression tests for the two issues noted in the Lab 2 feedback."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from school_mgmt import Course, DatabaseManager, Instructor, Student, ValidationError


class ReassignmentTests(unittest.TestCase):
    def setUp(self):
        self.first = Instructor('First', 40, 'first@example.com', 'I1')
        self.second = Instructor('Second', 41, 'second@example.com', 'I2')
        self.course = Course('C1', 'Tools')
        self.course.assign_instructor(self.first)

    def test_reassignment_removes_old_link(self):
        self.course.assign_instructor(self.second)
        self.assertEqual(self.first.assigned_courses, [])
        self.assertEqual(self.second.assigned_courses, ['C1'])
        self.assertEqual(self.course.instructor, 'I2')

    def test_unassign_removes_old_link(self):
        self.course.assign_instructor(None)
        self.assertEqual(self.first.assigned_courses, [])
        self.assertIsNone(self.course.instructor)

    def test_instructor_entrypoint_is_bidirectional_and_idempotent(self):
        self.second.assign_course(self.course)
        self.second.assign_course(self.course)
        self.assertEqual(self.first.assigned_courses, [])
        self.assertEqual(self.second.assigned_courses, ['C1'])
        self.assertEqual(self.course.instructor, 'I2')

    def test_string_reassignment_cleans_tracked_old_link(self):
        self.course.assign_instructor('I2')
        self.assertEqual(self.first.assigned_courses, [])
        self.assertEqual(self.course.instructor, 'I2')

    def test_invalid_reassignment_preserves_current_link(self):
        with self.assertRaises(ValidationError):
            self.course.assign_instructor(' ')
        self.assertEqual(self.first.assigned_courses, ['C1'])
        self.assertEqual(self.course.instructor, 'I1')


class AtomicImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db = DatabaseManager(self.folder / 'school.db')
        self.db.seed_demo()
        self.before = self.db.to_payload()
        self.path = self.folder / 'input.json'

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, payload, exception):
        self.path.write_text(json.dumps(payload), encoding='utf-8')
        with self.assertRaises(exception):
            self.db.load_json(self.path)
        self.assertEqual(self.db.to_payload(), self.before)
        # Verify rollback on a new connection, not only cached Python objects.
        self.assertEqual(DatabaseManager(self.db.path).to_payload(), self.before)

    def test_malformed_json_preserves_all_records(self):
        self.path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(json.JSONDecodeError):
            self.db.load_json(self.path)
        self.assertEqual(self.db.to_payload(), self.before)

    def test_invalid_shapes_preserve_all_records(self):
        for payload in ({}, [], {'students': [], 'instructors': []},
                        {'students': {}, 'instructors': [], 'courses': []},
                        {'students': [None], 'instructors': [], 'courses': []}):
            with self.subTest(payload=payload):
                self.reject(payload, ValidationError)

    def test_missing_field_preserves_all_records(self):
        payload = copy.deepcopy(self.before)
        del payload['students'][0]['email']
        self.reject(payload, ValidationError)

    def test_duplicate_id_rolls_back_deleted_records(self):
        payload = copy.deepcopy(self.before)
        payload['students'].append(copy.deepcopy(payload['students'][0]))
        self.reject(payload, sqlite3.IntegrityError)

    def test_duplicate_email_rolls_back_deleted_records(self):
        payload = copy.deepcopy(self.before)
        payload['students'][1]['email'] = payload['students'][0]['email']
        self.reject(payload, sqlite3.IntegrityError)

    def test_missing_instructor_rolls_back_deleted_records(self):
        payload = copy.deepcopy(self.before)
        payload['courses'][0]['instructor'] = 'MISSING'
        for instructor in payload['instructors']:
            instructor['assigned_courses'] = []
        self.reject(payload, sqlite3.IntegrityError)

    def test_missing_enrollment_target_rolls_back_deleted_records(self):
        payload = copy.deepcopy(self.before)
        payload['students'][0]['registered_courses'].append('MISSING')
        self.reject(payload, sqlite3.IntegrityError)

    def test_conflicting_assignment_preserves_records(self):
        payload = copy.deepcopy(self.before)
        payload['instructors'][1]['assigned_courses'].append('EECE435L')
        self.reject(payload, ValidationError)

    def test_relationship_type_is_checked(self):
        payload = copy.deepcopy(self.before)
        payload['students'][0]['registered_courses'] = 'EECE435L'
        self.reject(payload, ValidationError)

    def test_successful_import_replaces_and_preserves_both_relationship_sides(self):
        payload = {
            'students': [Student('New', 20, 'new@example.com', 'NEW').to_dict()],
            'instructors': [Instructor('Teacher', 40, 'teacher@example.com', 'T', ['NEWC']).to_dict()],
            'courses': [Course('NEWC', 'New course', None, ['NEW']).to_dict()],
        }
        self.path.write_text(json.dumps(payload))
        self.db.load_json(self.path)
        self.assertEqual(self.db.students()[0].registered_courses, ['NEWC'])
        self.assertEqual(self.db.courses()[0].enrolled_students, ['NEW'])
        self.assertEqual(self.db.courses()[0].instructor, 'T')
        self.assertEqual(self.db.instructors()[0].assigned_courses, ['NEWC'])
        self.assertEqual(len(self.db.students()), 1)

    def test_explicit_empty_payload_clears_database(self):
        self.path.write_text(json.dumps(dict(students=[], instructors=[], courses=[])))
        self.db.load_json(self.path)
        self.assertTrue(self.db.is_empty())

    def test_database_reassignment_and_unassignment(self):
        self.db.assign_instructor('I002', 'EECE435L')
        instructors = {i.instructor_id: i for i in self.db.instructors()}
        self.assertNotIn('EECE435L', instructors['I001'].assigned_courses)
        self.assertIn('EECE435L', instructors['I002'].assigned_courses)
        self.db.assign_instructor(None, 'EECE435L')
        self.assertFalse(any('EECE435L' in i.assigned_courses for i in self.db.instructors()))

    def test_seed_does_not_overwrite_instructor_only_database(self):
        db = DatabaseManager(self.folder / 'partial.db')
        db.add_instructor(Instructor('Existing', 45, 'existing@example.com', 'I001'))
        db.seed_demo()
        self.assertEqual(len(db.instructors()), 1)
        self.assertEqual(db.instructors()[0].name, 'Existing')
        self.assertEqual(db.students(), [])


if __name__ == '__main__':
    unittest.main()
