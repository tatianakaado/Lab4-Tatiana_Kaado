"""Part 2: Tkinter front end for the School Management System."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from school_mgmt import Course, DatabaseManager, Instructor, Student, ValidationError


BASE_DIR = Path(__file__).resolve().parent
COLORS = {
    "navy": "#17324D",
    "blue": "#146C94",
    "cyan": "#19A7CE",
    "paper": "#F6F8FB",
    "white": "#FFFFFF",
    "text": "#243447",
    "muted": "#637381",
    "success": "#177245",
    "danger": "#B42318",
}


class SchoolManagementTk:
    def __init__(self, root: tk.Tk, db_path: Path = BASE_DIR / "school.db") -> None:
        self.root = root
        self.db = DatabaseManager(db_path)
        self.db.seed_demo()
        self.root.title("School Management System")
        self.root.geometry("1240x760+60+40")
        self.root.minsize(1050, 680)
        self.root.configure(bg=COLORS["paper"])
        self.search_var = tk.StringVar()
        self.student_vars = {key: tk.StringVar() for key in ("id", "name", "age", "email", "course")}
        self.instructor_vars = {key: tk.StringVar() for key in ("id", "name", "age", "email", "course")}
        self.course_vars = {key: tk.StringVar() for key in ("id", "name", "instructor")}
        self.status_var = tk.StringVar(value="Ready — database connected")
        self._configure_style()
        self._build_ui()
        self.refresh_all()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["paper"])
        style.configure("Card.TFrame", background=COLORS["white"])
        style.configure("TLabel", background=COLORS["paper"], foreground=COLORS["text"], font=("Arial", 11))
        style.configure("Card.TLabel", background=COLORS["white"], foreground=COLORS["text"], font=("Arial", 11))
        style.configure("Section.TLabel", background=COLORS["white"], foreground=COLORS["navy"], font=("Arial", 15, "bold"))
        style.configure("Accent.TButton", background=COLORS["blue"], foreground="white", font=("Arial", 10, "bold"), padding=(12, 8))
        style.map("Accent.TButton", background=[("active", COLORS["cyan"])])
        style.configure("TButton", font=("Arial", 10), padding=(10, 7))
        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)
        style.configure("Treeview", rowheight=31, font=("Arial", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", background=COLORS["navy"], foreground="white", font=("Arial", 10, "bold"), padding=7)
        style.map("Treeview.Heading", background=[("active", COLORS["blue"])])
        style.configure("TNotebook", background=COLORS["white"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=(13, 8))

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=COLORS["navy"], height=86)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="SCHOOL MANAGEMENT SYSTEM", bg=COLORS["navy"], fg="white", font=("Arial", 23, "bold")).pack(anchor="w", padx=28, pady=(16, 0))
        tk.Label(header, text="Students  •  Instructors  •  Courses  •  SQLite", bg=COLORS["navy"], fg="#B9D7EA", font=("Arial", 11)).pack(anchor="w", padx=29, pady=(2, 0))

        workspace = ttk.Frame(self.root, padding=18)
        workspace.pack(fill="both", expand=True)
        workspace.columnconfigure(0, weight=0, minsize=390)
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        form_card = ttk.Frame(workspace, style="Card.TFrame", padding=16)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        ttk.Label(form_card, text="Add a new record", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        notebook = ttk.Notebook(form_card)
        notebook.pack(fill="both", expand=True)
        self._build_student_form(notebook)
        self._build_instructor_form(notebook)
        self._build_course_form(notebook)

        data_card = ttk.Frame(workspace, style="Card.TFrame", padding=16)
        data_card.grid(row=0, column=1, sticky="nsew")
        data_card.columnconfigure(0, weight=1)
        data_card.rowconfigure(2, weight=1)

        title_row = ttk.Frame(data_card, style="Card.TFrame")
        title_row.grid(row=0, column=0, sticky="ew")
        ttk.Label(title_row, text="All records", style="Section.TLabel").pack(side="left")
        ttk.Label(title_row, text="Search name, ID, email or course", style="Card.TLabel").pack(side="right")
        search_entry = ttk.Entry(data_card, textvariable=self.search_var, font=("Arial", 11))
        search_entry.grid(row=1, column=0, sticky="ew", pady=(9, 12))
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_table())

        columns = ("type", "id", "name", "contact", "details")
        table_frame = ttk.Frame(data_card, style="Card.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {"type": "TYPE", "id": "ID", "name": "NAME / COURSE", "contact": "EMAIL / INSTRUCTOR", "details": "COURSES / STUDENTS"}
        widths = {"type": 84, "id": 105, "name": 180, "contact": 205, "details": 150}
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=widths[column], minwidth=70, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.tag_configure("Student", background="#F3F9FC")
        self.table.tag_configure("Course", background="#F6FBF7")
        self.table.bind("<Double-1>", lambda _event: self.edit_selected())

        actions = ttk.Frame(data_card, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        for text, command in (
            ("Edit selected", self.edit_selected), ("Delete", self.delete_selected),
            ("Save JSON", self.save_json), ("Load JSON", self.load_json),
            ("Backup DB", self.backup_database), ("Restore DB", self.restore_database),
        ):
            ttk.Button(actions, text=text, command=command).pack(side="left", padx=(0, 6))

        status = tk.Label(self.root, textvariable=self.status_var, anchor="w", bg=COLORS["blue"], fg="white", font=("Arial", 10), padx=20, pady=7)
        status.pack(fill="x", side="bottom")

    def _form_tab(self, notebook: ttk.Notebook, title: str) -> ttk.Frame:
        frame = ttk.Frame(notebook, style="Card.TFrame", padding=(8, 18))
        notebook.add(frame, text=title)
        frame.columnconfigure(1, weight=1)
        return frame

    def _field(self, frame: ttk.Frame, row: int, label: str, variable: tk.StringVar, values: list[str] | None = None) -> ttk.Widget:
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 9))
        if values is None:
            widget: ttk.Widget = ttk.Entry(frame, textvariable=variable)
        else:
            widget = ttk.Combobox(frame, textvariable=variable, values=values, state="readonly")
        widget.grid(row=row, column=1, sticky="ew", pady=6)
        return widget

    def _build_student_form(self, notebook: ttk.Notebook) -> None:
        frame = self._form_tab(notebook, "Student")
        self._field(frame, 0, "Student ID", self.student_vars["id"])
        self._field(frame, 1, "Full name", self.student_vars["name"])
        self._field(frame, 2, "Age", self.student_vars["age"])
        self._field(frame, 3, "Email", self.student_vars["email"])
        self.student_course = self._field(frame, 4, "Register in", self.student_vars["course"], [])
        ttk.Button(frame, text="Add student", style="Accent.TButton", command=self.add_student).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(18, 6))
        ttk.Label(frame, text="Choose a course to register immediately, or leave it blank.", style="Card.TLabel", wraplength=310).grid(row=6, column=0, columnspan=2, sticky="w", pady=(7, 0))

    def _build_instructor_form(self, notebook: ttk.Notebook) -> None:
        frame = self._form_tab(notebook, "Instructor")
        self._field(frame, 0, "Instructor ID", self.instructor_vars["id"])
        self._field(frame, 1, "Full name", self.instructor_vars["name"])
        self._field(frame, 2, "Age", self.instructor_vars["age"])
        self._field(frame, 3, "Email", self.instructor_vars["email"])
        self.instructor_course = self._field(frame, 4, "Assign course", self.instructor_vars["course"], [])
        ttk.Button(frame, text="Add instructor", style="Accent.TButton", command=self.add_instructor).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(18, 6))

    def _build_course_form(self, notebook: ttk.Notebook) -> None:
        frame = self._form_tab(notebook, "Course")
        self._field(frame, 0, "Course ID", self.course_vars["id"])
        self._field(frame, 1, "Course name", self.course_vars["name"])
        self.course_instructor = self._field(frame, 2, "Instructor", self.course_vars["instructor"], [])
        ttk.Button(frame, text="Add course", style="Accent.TButton", command=self.add_course).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 6))
        ttk.Label(frame, text="Instructors may also be assigned later using the Instructor form.", style="Card.TLabel", wraplength=310).grid(row=4, column=0, columnspan=2, sticky="w", pady=(7, 0))

    @staticmethod
    def _choice_id(value: str) -> str:
        return value.split(" — ", 1)[0] if value else ""

    def refresh_all(self) -> None:
        course_values = [f"{course.course_id} — {course.course_name}" for course in self.db.courses()]
        instructor_values = [f"{item.instructor_id} — {item.name}" for item in self.db.instructors()]
        self.student_course.configure(values=[""] + course_values)
        self.instructor_course.configure(values=[""] + course_values)
        self.course_instructor.configure(values=[""] + instructor_values)
        self.refresh_table()

    def refresh_table(self) -> None:
        self.table.delete(*self.table.get_children())
        for row in self.db.all_rows(self.search_var.get()):
            self.table.insert("", "end", values=row, tags=(row[0],))
        count = len(self.table.get_children())
        self.status_var.set(f"Showing {count} record{'s' if count != 1 else ''} — SQLite connected")

    def _handle(self, action) -> None:
        try:
            action()
        except (ValidationError, sqlite3.IntegrityError, ValueError, OSError) as exc:
            messagebox.showerror("Unable to complete action", str(exc), parent=self.root)
            self.status_var.set(f"Error: {exc}")

    def add_student(self) -> None:
        def action() -> None:
            values = self.student_vars
            student = Student(values["name"].get(), values["age"].get(), values["email"].get(), values["id"].get())
            self.db.add_student(student)
            course_id = self._choice_id(values["course"].get())
            if course_id:
                self.db.register_student(student.student_id, course_id)
            for value in values.values(): value.set("")
            self.refresh_all()
            self.status_var.set(f"Student {student.student_id} added")
        self._handle(action)

    def add_instructor(self) -> None:
        def action() -> None:
            values = self.instructor_vars
            instructor = Instructor(values["name"].get(), values["age"].get(), values["email"].get(), values["id"].get())
            self.db.add_instructor(instructor)
            course_id = self._choice_id(values["course"].get())
            if course_id:
                self.db.assign_instructor(instructor.instructor_id, course_id)
            for value in values.values(): value.set("")
            self.refresh_all()
            self.status_var.set(f"Instructor {instructor.instructor_id} added")
        self._handle(action)

    def add_course(self) -> None:
        def action() -> None:
            values = self.course_vars
            course = Course(values["id"].get(), values["name"].get(), self._choice_id(values["instructor"].get()) or None)
            self.db.add_course(course)
            for value in values.values(): value.set("")
            self.refresh_all()
            self.status_var.set(f"Course {course.course_id} added")
        self._handle(action)

    def _selection(self) -> tuple[str, str] | None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Select a record", "Select a row in the table first.", parent=self.root)
            return None
        values = self.table.item(selected[0], "values")
        return str(values[0]), str(values[1])

    def edit_selected(self) -> None:
        selected = self._selection()
        if not selected:
            return
        record_type, record_id = selected
        def action() -> None:
            if record_type == "Student":
                old = next(item for item in self.db.students() if item.student_id == record_id)
                name = simpledialog.askstring("Edit student", "Full name:", initialvalue=old.name, parent=self.root)
                if name is None: return
                age = simpledialog.askinteger("Edit student", "Age:", initialvalue=old.age, minvalue=0, maxvalue=130, parent=self.root)
                if age is None: return
                email = simpledialog.askstring("Edit student", "Email:", initialvalue=old.email, parent=self.root)
                if email is None: return
                self.db.update_student(record_id, Student(name, age, email, record_id))
            elif record_type == "Instructor":
                old = next(item for item in self.db.instructors() if item.instructor_id == record_id)
                name = simpledialog.askstring("Edit instructor", "Full name:", initialvalue=old.name, parent=self.root)
                if name is None: return
                age = simpledialog.askinteger("Edit instructor", "Age:", initialvalue=old.age, minvalue=0, maxvalue=130, parent=self.root)
                if age is None: return
                email = simpledialog.askstring("Edit instructor", "Email:", initialvalue=old.email, parent=self.root)
                if email is None: return
                self.db.update_instructor(record_id, Instructor(name, age, email, record_id))
            else:
                old = next(item for item in self.db.courses() if item.course_id == record_id)
                name = simpledialog.askstring("Edit course", "Course name:", initialvalue=old.course_name, parent=self.root)
                if name is None: return
                self.db.update_course(record_id, Course(record_id, name, old.instructor))
            self.refresh_all()
            self.status_var.set(f"{record_type} {record_id} updated")
        self._handle(action)

    def delete_selected(self) -> None:
        selected = self._selection()
        if not selected:
            return
        record_type, record_id = selected
        if not messagebox.askyesno("Confirm deletion", f"Delete {record_type.lower()} {record_id}?", parent=self.root):
            return
        self._handle(lambda: (self.db.delete_record(record_type, record_id), self.refresh_all()))

    def save_json(self) -> None:
        path = filedialog.asksaveasfilename(parent=self.root, title="Save data", initialdir=BASE_DIR, initialfile="data.json", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self._handle(lambda: (self.db.save_json(path), self.status_var.set(f"Saved JSON: {Path(path).name}")))

    def load_json(self) -> None:
        path = filedialog.askopenfilename(parent=self.root, title="Load data", initialdir=BASE_DIR, filetypes=[("JSON", "*.json")])
        if path:
            self._handle(lambda: (self.db.load_json(path), self.refresh_all(), self.status_var.set(f"Loaded JSON: {Path(path).name}")))

    def backup_database(self) -> None:
        default = f"school_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        path = filedialog.asksaveasfilename(parent=self.root, title="Back up database", initialdir=BASE_DIR / "backups", initialfile=default, defaultextension=".db", filetypes=[("SQLite database", "*.db")])
        if path:
            self._handle(lambda: (self.db.backup(path), self.status_var.set(f"Backup created: {Path(path).name}")))

    def restore_database(self) -> None:
        path = filedialog.askopenfilename(parent=self.root, title="Restore database", initialdir=BASE_DIR / "backups", filetypes=[("SQLite database", "*.db")])
        if path and messagebox.askyesno("Restore database", "Replace current data with this backup?", parent=self.root):
            self._handle(lambda: (self.db.restore(path), self.refresh_all(), self.status_var.set(f"Restored: {Path(path).name}")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Tkinter School Management System")
    parser.add_argument("--screenshot", type=Path, help="Capture the populated window and close")
    args = parser.parse_args()
    root = tk.Tk()
    SchoolManagementTk(root)
    if args.screenshot:
        def capture() -> None:
            try:
                from PIL import ImageGrab
                root.update()
                x, y = root.winfo_rootx(), root.winfo_rooty()
                image = ImageGrab.grab((x, y, x + root.winfo_width(), y + root.winfo_height()))
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                image.save(args.screenshot)
            finally:
                root.destroy()
        root.after(1000, capture)
    root.mainloop()


if __name__ == "__main__":
    main()
