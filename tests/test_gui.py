"""Exercise actual PyQt widgets with isolated temporary storage."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from pyqt_app import SchoolManagementQt, EditDialog

class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.window = SchoolManagementQt(self.root / 'school.db')

    def tearDown(self):
        self.window.close()
        self.temp.cleanup()

    def test_initial_records_and_search(self):
        self.assertEqual(self.window.table.rowCount(), 8)
        self.window.search.setText('Tatiana')
        self.assertEqual(self.window.table.rowCount(), 1)
        self.assertEqual(self.window.table.item(0, 2).text(), 'Tatiana Kaado')

    def test_create_student_with_registration(self):
        w = self.window
        w.student_id.setText('GUI1')
        w.student_name.setText('GUI Student')
        w.student_email.setText('gui@example.com')
        w.student_course.setCurrentIndex(w.student_course.findData('EECE435L'))
        w.add_student()
        student = next(s for s in w.db.students() if s.student_id == 'GUI1')
        self.assertEqual(student.registered_courses, ['EECE435L'])
        self.assertEqual(w.table.rowCount(), 9)

    def test_bad_json_shows_error_and_preserves_records(self):
        w = self.window
        before = w.db.to_payload()
        path = self.root / 'bad.json'
        payload = json.loads(json.dumps(before))
        payload['students'].append(payload['students'][0])
        path.write_text(json.dumps(payload))
        with patch('pyqt_app.QFileDialog.getOpenFileName', return_value=(str(path), '')):
            with patch('pyqt_app.QMessageBox.critical') as error:
                w.load_json()
                error.assert_called_once()
        self.assertEqual(w.db.to_payload(), before)
        self.assertEqual(w.table.rowCount(), 8)
        self.assertIn('Error:', w.statusBar().currentMessage())

    def test_edit_dialog_uses_fields_for_record_type(self):
        person = EditDialog('Student', {'name': 'Test', 'age': 22, 'email': 't@example.com'}, self.window)
        self.assertEqual(person.age.value(), 22)
        self.assertEqual(person.email.text(), 't@example.com')
        course = EditDialog('Course', {'name': 'Tools'}, self.window)
        self.assertIsNone(course.age)
        self.assertIsNone(course.email)
        person.close()
        course.close()
