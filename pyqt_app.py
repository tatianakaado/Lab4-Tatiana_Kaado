"""Part 3: PyQt5 front end for the School Management System."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from school_mgmt import Course, DatabaseManager, Instructor, Student, ValidationError


BASE_DIR = Path(__file__).resolve().parent


STYLE = """
QMainWindow, QWidget#central { background: #F4F7FB; color: #243447; }
QFrame#header { background: #312E81; border: none; }
QLabel#title { color: white; font-size: 25px; font-weight: 700; }
QLabel#subtitle { color: #C7D2FE; font-size: 12px; }
QFrame.card { background: white; border: 1px solid #E2E8F0; border-radius: 10px; }
QLabel.section { color: #1E1B4B; font-size: 17px; font-weight: 700; }
QLineEdit, QSpinBox, QComboBox {
  min-height: 31px; padding: 2px 8px; border: 1px solid #CBD5E1;
  border-radius: 5px; background: white;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 2px solid #4F46E5; }
QPushButton { min-height: 30px; padding: 2px 11px; border: 1px solid #CBD5E1; border-radius: 5px; background: #F8FAFC; }
QPushButton:hover { background: #EEF2FF; border-color: #818CF8; }
QPushButton#primary { color: white; background: #4F46E5; border: none; font-weight: 700; min-height: 36px; }
QPushButton#primary:hover { background: #4338CA; }
QPushButton#danger { color: #B42318; }
QTabWidget::pane { border: none; }
QTabBar::tab { padding: 9px 13px; background: #EEF2F7; border: none; }
QTabBar::tab:selected { color: #4338CA; background: white; font-weight: 700; border-bottom: 2px solid #4F46E5; }
QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 5px; gridline-color: #EDF2F7; alternate-background-color: #F8FAFC; }
QHeaderView::section { background: #312E81; color: white; border: none; padding: 8px; font-weight: 700; }
QStatusBar { background: #4F46E5; color: white; }
QStatusBar::item { border: none; }
"""


class EditDialog(QDialog):
    """Modal editor for an existing student, instructor, or course.
    
    Save accepts the dialog; Cancel rejects it. The caller validates and persists
    the edited values. Record identifiers are not editable.
    
    :param record_type: Record category: Student, Instructor, or Course.
    :type record_type: str
    :param values: Initial name and, for people, age and email.
    :type values: dict[str, str | int]
    :param parent: Owning widget; defaults to None.
    :type parent: QWidget or None
    """
    def __init__(self, record_type: str, values: dict[str, str | int], parent: QWidget | None = None) -> None:
        """Create fields appropriate to the selected record category.
        
        :param record_type: Record category.
        :type record_type: str
        :param values: Initial field values.
        :type values: dict[str, str | int]
        :param parent: Parent widget; defaults to None.
        :type parent: QWidget or None
        :raises KeyError: A required initial field is missing.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        super().__init__(parent)
        self.record_type = record_type
        self.setWindowTitle(f"Edit {record_type}")
        self.setMinimumWidth(390)
        layout = QFormLayout(self)
        self.name = QLineEdit(str(values["name"]))
        layout.addRow("Name", self.name)
        self.age: QSpinBox | None = None
        self.email: QLineEdit | None = None
        if record_type != "Course":
            self.age = QSpinBox()
            self.age.setRange(0, 130)
            self.age.setValue(int(values["age"]))
            self.email = QLineEdit(str(values["email"]))
            layout.addRow("Age", self.age)
            layout.addRow("Email", self.email)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class SchoolManagementQt(QMainWindow):
    """PyQt5 dashboard backed by a shared SQLite database.
    
    Construction initializes the schema, seeds a completely empty database,
    builds the forms and table, and loads the current records. A QApplication
    must already exist.
    
    :ivar db: Persistence service used by every form and toolbar action.
    :vartype db: school_mgmt.storage.DatabaseManager
    :ivar tabs: Student, instructor, and course input tabs.
    :vartype tabs: QTabWidget
    :ivar table: Read-only, searchable record table.
    :vartype table: QTableWidget
    
    :param db_path: Database location; defaults to school.db beside this module.
    :type db_path: pathlib.Path
    """
    def __init__(self, db_path: Path = BASE_DIR / "school.db") -> None:
        """Initialize storage, create the dashboard, and display existing records.
        
        :param db_path: SQLite path; defaults to the project school.db.
        :type db_path: pathlib.Path
        :raises sqlite3.Error: The database cannot be opened or initialized.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        super().__init__()
        self.db = DatabaseManager(db_path)
        self.db.seed_demo()
        self.setWindowTitle("School Management System")
        self.resize(1280, 770)
        self.setMinimumSize(1080, 680)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        """Create the header, input tabs, search field, table, toolbar, and status bar.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(88)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 13, 24, 10)
        title = QLabel("SCHOOL MANAGEMENT SYSTEM")
        title.setObjectName("title")
        subtitle = QLabel("PyQt5 dashboard  •  validated forms  •  SQLite persistence  •  CSV export")
        subtitle.setObjectName("subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        outer.addWidget(header)

        content = QHBoxLayout()
        content.setContentsMargins(18, 18, 18, 18)
        content.setSpacing(14)
        outer.addLayout(content, 1)

        form_card = QFrame()
        form_card.setProperty("class", "card")
        form_card.setFixedWidth(390)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        label = QLabel("Add a new record")
        label.setProperty("class", "section")
        form_layout.addWidget(label)
        self.tabs = QTabWidget()
        form_layout.addWidget(self.tabs, 1)
        self._build_student_tab()
        self._build_instructor_tab()
        self._build_course_tab()
        content.addWidget(form_card)

        table_card = QFrame()
        table_card.setProperty("class", "card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        heading_row = QHBoxLayout()
        heading = QLabel("All records")
        heading.setProperty("class", "section")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(QLabel("Search name, ID, email or course"))
        table_layout.addLayout(heading_row)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type to filter records…")
        self.search.textChanged.connect(self.refresh_table)
        table_layout.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["TYPE", "ID", "NAME / COURSE", "EMAIL / INSTRUCTOR", "COURSES / STUDENTS"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 88)
        self.table.setColumnWidth(1, 112)
        self.table.doubleClicked.connect(self.edit_selected)
        table_layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for text, callback, object_name in (
            ("Edit selected", self.edit_selected, ""), ("Delete", self.delete_selected, "danger"),
            ("Save JSON", self.save_json, ""), ("Load JSON", self.load_json, ""),
            ("Export CSV", self.export_csv, ""), ("Backup DB", self.backup_database, ""),
            ("Restore DB", self.restore_database, ""),
        ):
            button = QPushButton(text)
            button.setObjectName(object_name)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        table_layout.addLayout(actions)
        content.addWidget(table_card, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — database connected")

    def _new_tab(self, title: str) -> tuple[QWidget, QFormLayout]:
        """Append a tab with a form layout.
        
        :param title: Text shown on the tab.
        :type title: str
        :return: The tab widget and its layout.
        :rtype: tuple[QWidget, QFormLayout]
        """
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(4, 20, 4, 4)
        layout.setSpacing(11)
        self.tabs.addTab(widget, title)
        return widget, layout

    def _build_student_tab(self) -> None:
        """Create student identity fields and an optional course-registration selector.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        _widget, layout = self._new_tab("Student")
        self.student_id = QLineEdit(); self.student_id.setPlaceholderText("e.g. S2026004")
        self.student_name = QLineEdit(); self.student_name.setPlaceholderText("Full name")
        self.student_age = QSpinBox(); self.student_age.setRange(0, 130); self.student_age.setValue(20)
        self.student_email = QLineEdit(); self.student_email.setPlaceholderText("name@example.com")
        self.student_course = QComboBox()
        for label, widget in (("Student ID", self.student_id), ("Full name", self.student_name), ("Age", self.student_age), ("Email", self.student_email), ("Register in", self.student_course)):
            layout.addRow(label, widget)
        button = QPushButton("Add student"); button.setObjectName("primary"); button.clicked.connect(self.add_student)
        layout.addRow(button)

    def _build_instructor_tab(self) -> None:
        """Create instructor identity fields and an optional course-assignment selector.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        _widget, layout = self._new_tab("Instructor")
        self.instructor_id = QLineEdit(); self.instructor_id.setPlaceholderText("e.g. I003")
        self.instructor_name = QLineEdit(); self.instructor_name.setPlaceholderText("Full name")
        self.instructor_age = QSpinBox(); self.instructor_age.setRange(0, 130); self.instructor_age.setValue(35)
        self.instructor_email = QLineEdit(); self.instructor_email.setPlaceholderText("name@example.com")
        self.instructor_course = QComboBox()
        for label, widget in (("Instructor ID", self.instructor_id), ("Full name", self.instructor_name), ("Age", self.instructor_age), ("Email", self.instructor_email), ("Assign course", self.instructor_course)):
            layout.addRow(label, widget)
        button = QPushButton("Add instructor"); button.setObjectName("primary"); button.clicked.connect(self.add_instructor)
        layout.addRow(button)

    def _build_course_tab(self) -> None:
        """Create course ID/name fields and an optional instructor selector.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        _widget, layout = self._new_tab("Course")
        self.course_id = QLineEdit(); self.course_id.setPlaceholderText("e.g. EECE350")
        self.course_name = QLineEdit(); self.course_name.setPlaceholderText("Course title")
        self.course_instructor = QComboBox()
        layout.addRow("Course ID", self.course_id)
        layout.addRow("Course name", self.course_name)
        layout.addRow("Instructor", self.course_instructor)
        button = QPushButton("Add course"); button.setObjectName("primary"); button.clicked.connect(self.add_course)
        layout.addRow(button)

    def refresh_choices(self) -> None:
        """Reload course and instructor dropdowns while retaining available selections.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        course_boxes = (self.student_course, self.instructor_course)
        for box in course_boxes:
            current = box.currentData()
            box.clear(); box.addItem("No course selected", None)
            for course in self.db.courses():
                box.addItem(f"{course.course_id} — {course.course_name}", course.course_id)
            index = box.findData(current)
            if index >= 0: box.setCurrentIndex(index)
        current = self.course_instructor.currentData()
        self.course_instructor.clear(); self.course_instructor.addItem("Unassigned", None)
        for instructor in self.db.instructors():
            self.course_instructor.addItem(f"{instructor.instructor_id} — {instructor.name}", instructor.instructor_id)
        index = self.course_instructor.findData(current)
        if index >= 0: self.course_instructor.setCurrentIndex(index)

    def refresh_all(self) -> None:
        """Refresh dropdown choices and then the filtered records table.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        self.refresh_choices()
        self.refresh_table()

    def refresh_table(self) -> None:
        """Apply the current search text and redraw color-coded records and their count.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        rows = self.db.all_rows(self.search.text())
        self.table.setRowCount(len(rows))
        backgrounds = {"Student": QColor("#F3F8FF"), "Instructor": QColor("#FFFFFF"), "Course": QColor("#F2FBF6")}
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setBackground(backgrounds[row[0]])
                item.setToolTip(value)
                self.table.setItem(row_index, column_index, item)
        self.statusBar().showMessage(f"Showing {len(rows)} record{'s' if len(rows) != 1 else ''} — SQLite connected")

    def _run(self, action) -> None:
        """Execute a GUI action and display expected errors.
        
        Catches ValidationError, sqlite3.IntegrityError, ValueError, and OSError.
        Other exceptions propagate so programming errors are visible during development.
        
        :param action: Zero-argument callback to execute.
        :type action: Callable[[], object]
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        try:
            action()
        except (ValidationError, sqlite3.IntegrityError, ValueError, OSError) as exc:
            QMessageBox.critical(self, "Unable to complete action", str(exc))
            self.statusBar().showMessage(f"Error: {exc}")

    def add_student(self) -> None:
        """Validate the Student form, insert the student, and optionally register a course.
        
        On success, clear the text fields and refresh the records.
        Validation and database errors are displayed by :meth:`_run`.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        def action() -> None:
            """Perform the enclosing GUI action on accepted inputs.
            
            :return: No return value.
            :rtype: None
            """
            student = Student(self.student_name.text(), self.student_age.value(), self.student_email.text(), self.student_id.text())
            self.db.add_student(student)
            if self.student_course.currentData(): self.db.register_student(student.student_id, self.student_course.currentData())
            self.student_id.clear(); self.student_name.clear(); self.student_email.clear()
            self.refresh_all(); self.statusBar().showMessage(f"Student {student.student_id} added")
        self._run(action)

    def add_instructor(self) -> None:
        """Validate the Instructor form, insert the instructor, and optionally assign a course.
        
        On success, clear the text fields and refresh the records.
        Validation and database errors are displayed by :meth:`_run`.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        def action() -> None:
            """Perform the enclosing GUI action on accepted inputs.
            
            :return: No return value.
            :rtype: None
            """
            instructor = Instructor(self.instructor_name.text(), self.instructor_age.value(), self.instructor_email.text(), self.instructor_id.text())
            self.db.add_instructor(instructor)
            if self.instructor_course.currentData(): self.db.assign_instructor(instructor.instructor_id, self.instructor_course.currentData())
            self.instructor_id.clear(); self.instructor_name.clear(); self.instructor_email.clear()
            self.refresh_all(); self.statusBar().showMessage(f"Instructor {instructor.instructor_id} added")
        self._run(action)

    def add_course(self) -> None:
        """Validate the Course form and insert it with its selected instructor.
        
        On success, clear the text fields and refresh the records.
        Validation and database errors are displayed by :meth:`_run`.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        def action() -> None:
            """Perform the enclosing GUI action on accepted inputs.
            
            :return: No return value.
            :rtype: None
            """
            course = Course(self.course_id.text(), self.course_name.text(), self.course_instructor.currentData())
            self.db.add_course(course)
            self.course_id.clear(); self.course_name.clear()
            self.refresh_all(); self.statusBar().showMessage(f"Course {course.course_id} added")
        self._run(action)

    def _selected(self) -> tuple[str, str] | None:
        """Read the current row or prompt the user to select a record.
        
        :return: Record category and ID, or None when no row is selected.
        :rtype: tuple[str, str] or None
        """
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select a record", "Select a row in the table first.")
            return None
        return self.table.item(row, 0).text(), self.table.item(row, 1).text()

    def edit_selected(self) -> None:
        """Open an editor for the selected row and persist accepted field changes.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        selected = self._selected()
        if not selected: return
        record_type, record_id = selected
        def action() -> None:
            """Perform the enclosing GUI action on accepted inputs.
            
            :return: No return value.
            :rtype: None
            """
            if record_type == "Student":
                old = next(item for item in self.db.students() if item.student_id == record_id)
                dialog = EditDialog(record_type, {"name": old.name, "age": old.age, "email": old.email}, self)
                if dialog.exec_() != QDialog.Accepted: return
                self.db.update_student(record_id, Student(dialog.name.text(), dialog.age.value(), dialog.email.text(), record_id))
            elif record_type == "Instructor":
                old = next(item for item in self.db.instructors() if item.instructor_id == record_id)
                dialog = EditDialog(record_type, {"name": old.name, "age": old.age, "email": old.email}, self)
                if dialog.exec_() != QDialog.Accepted: return
                self.db.update_instructor(record_id, Instructor(dialog.name.text(), dialog.age.value(), dialog.email.text(), record_id))
            else:
                old = next(item for item in self.db.courses() if item.course_id == record_id)
                dialog = EditDialog(record_type, {"name": old.course_name}, self)
                if dialog.exec_() != QDialog.Accepted: return
                self.db.update_course(record_id, Course(record_id, dialog.name.text(), old.instructor))
            self.refresh_all(); self.statusBar().showMessage(f"{record_type} {record_id} updated")
        self._run(action)

    def delete_selected(self) -> None:
        """Ask for confirmation and delete the selected record and cascading relationships.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        selected = self._selected()
        if not selected: return
        record_type, record_id = selected
        if QMessageBox.question(self, "Confirm deletion", f"Delete {record_type.lower()} {record_id}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._run(lambda: (self.db.delete_record(record_type, record_id), self.refresh_all()))

    def save_json(self) -> None:
        """Choose a destination and export all database records as UTF-8 JSON.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save data", str(BASE_DIR / "data.json"), "JSON files (*.json)")
        if path: self._run(lambda: (self.db.save_json(path), self.statusBar().showMessage(f"Saved JSON: {Path(path).name}")))

    def load_json(self) -> None:
        """Choose a JSON file and atomically replace records after validation.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        A failed import leaves all pre-existing records intact.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        path, _ = QFileDialog.getOpenFileName(self, "Load data", str(BASE_DIR), "JSON files (*.json)")
        if path: self._run(lambda: (self.db.load_json(path), self.refresh_all(), self.statusBar().showMessage(f"Loaded JSON: {Path(path).name}")))

    def export_csv(self) -> None:
        """Choose a directory and export separate student, instructor, and course CSV files.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        directory = QFileDialog.getExistingDirectory(self, "Export CSV files", str(BASE_DIR / "exports"))
        if directory:
            self._run(lambda: (self.db.export_csv(directory), self.statusBar().showMessage(f"Exported three CSV files to {directory}")))

    def backup_database(self) -> None:
        """Choose a destination and create a SQLite backup with a timestamped default name.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        default = BASE_DIR / "backups" / f"school_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        path, _ = QFileDialog.getSaveFileName(self, "Back up database", str(default), "SQLite database (*.db)")
        if path: self._run(lambda: (self.db.backup(path), self.statusBar().showMessage(f"Backup created: {Path(path).name}")))

    def restore_database(self) -> None:
        """Choose a backup and replace the current database after confirmation.
        
        User-facing validation, integrity, value, and file errors are displayed
        by :meth:`_run`. Cancelling a file dialog or confirmation makes no change.
        
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        path, _ = QFileDialog.getOpenFileName(self, "Restore database", str(BASE_DIR / "backups"), "SQLite database (*.db)")
        if path and QMessageBox.question(self, "Restore database", "Replace current data with this backup?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._run(lambda: (self.db.restore(path), self.refresh_all(), self.statusBar().showMessage(f"Restored: {Path(path).name}")))


def main() -> None:
    """Start the Qt event loop, optionally capture the window, and exit.
    
    Run ``python pyqt_app.py`` for normal use. Pass ``--screenshot PATH``
    to save a PNG of the populated window and exit after one second.
    Importing this module never launches the application.
    
    :raises SystemExit: The Qt event loop terminates or argument parsing exits.
    :return: No return value; updates state or performs the described action.
    :rtype: None
    """
    parser = argparse.ArgumentParser(description="PyQt5 School Management System")
    parser.add_argument("--screenshot", type=Path, help="Capture the populated window and close")
    args = parser.parse_args()
    application = QApplication(sys.argv[:1])
    window = SchoolManagementQt()
    window.show()
    if args.screenshot:
        def capture() -> None:
            """Capture the running window as PNG and request event-loop shutdown."""
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(args.screenshot), "PNG")
            application.quit()
        QTimer.singleShot(1000, capture)
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
