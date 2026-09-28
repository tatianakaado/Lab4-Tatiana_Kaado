"""Verify both actual GUI interfaces exchange persistent records."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication, QDialog
from pyqt_app import SchoolManagementQt
from tk_app import SchoolManagementTk


class InterfaceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tkinter desktop display unavailable: {exc}")
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.tk_window = tk.Toplevel(self.root)
        self.tk_window.withdraw()
        self.addCleanup(self.tk_window.destroy)
        self.tk_ui = SchoolManagementTk(self.tk_window, self.folder / "shared.db")
        self.qt_ui = SchoolManagementQt(self.folder / "shared.db")
        self.addCleanup(self.qt_ui.close)

    def add_tk_student(self):
        for key, value in {
            "id": "CROSS1", "name": "Shared Student", "age": "22",
            "email": "shared@example.com", "course": "EECE435L — Software Tools"
        }.items():
            self.tk_ui.student_vars[key].set(value)
        with patch("tk_app.messagebox.showerror") as error:
            self.tk_ui.add_student()
            error.assert_not_called()

    def test_tk_creation_qt_edit_and_tk_readback(self):
        self.add_tk_student()
        self.qt_ui.refresh_all()
        self.qt_ui.search.setText("shared@example.com")
        self.assertEqual(self.qt_ui.table.rowCount(), 1)
        self.assertEqual(self.qt_ui.table.item(0, 2).text(), "Shared Student")
        self.qt_ui.table.selectRow(0)
        with patch("pyqt_app.EditDialog") as dialog:
            dialog.return_value.exec_.return_value = QDialog.Accepted
            dialog.return_value.name.text.return_value = "Edited in PyQt"
            dialog.return_value.age.value.return_value = 23
            dialog.return_value.email.text.return_value = "shared@example.com"
            self.qt_ui.edit_selected()
        self.tk_ui.refresh_all()
        self.tk_ui.search_var.set("shared@example.com")
        self.tk_ui.refresh_table()
        rows = self.tk_ui.table.get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.tk_ui.table.item(rows[0], "values")[2], "Edited in PyQt")
        student = next(s for s in self.tk_ui.db.students() if s.student_id == "CROSS1")
        self.assertEqual(student.age, 23)
        self.assertEqual(student.registered_courses, ["EECE435L"])

    def test_json_export_from_tk_import_into_qt(self):
        self.add_tk_student()
        path = self.folder / "exchange.json"
        with patch("tk_app.filedialog.asksaveasfilename", return_value=str(path)):
            self.tk_ui.save_json()
        self.assertTrue(path.exists())
        separate_ui = SchoolManagementQt(self.folder / "separate.db")
        self.addCleanup(separate_ui.close)
        self.assertNotIn("CROSS1", [s.student_id for s in separate_ui.db.students()])
        with patch("pyqt_app.QFileDialog.getOpenFileName", return_value=(str(path), "")):
            with patch("pyqt_app.QMessageBox.critical") as error:
                separate_ui.load_json()
                error.assert_not_called()
        self.assertEqual(separate_ui.db.to_payload(), self.tk_ui.db.to_payload())
