# Lab 4 — Git and GitHub

**Tatiana Kaado · EECE 435L · School Management System**

This project combines the Tkinter interface from Lab 2 with the documented
PyQt5 interface and corrected shared backend from Lab 3. Both interfaces manage
students, instructors, courses, and enrollments using the same SQLite database.

## Setup

Use Python 3.11 or newer with Tkinter installed and a desktop session.
From this project folder on macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, use `py -m venv .venv`, then `.venv\Scripts\activate` in
Command Prompt, followed by the same pip command.

## Run either interface

```bash
python tk_app.py
```

Or:

```bash
python pyqt_app.py
```

Each script creates `school.db` in the project folder on first launch and seeds
an empty database with demonstration records. To switch interfaces, close the
current application and launch the other script. Your saved changes remain in
the same database. The two GUI frameworks run in separate processes with their
own event loops; they share `school_mgmt` models, validation, and persistence.
Tables do not automatically refresh when another running process changes data.

1. Use the Student, Instructor, and Course tabs to add records.
2. Select an optional course when adding a student or instructor; choose an
   optional instructor when adding a course.
3. Search by name, ID, email, or course. Select a row to edit or delete it.
4. Save/Load JSON transfers records; loading JSON replaces the current contents.
5. Backup/Restore DB saves or restores a SQLite copy.
6. PyQt additionally supports CSV export.

`data.json` contains the supplied demonstration dataset. Databases, exports,
backups, environments, and generated HTML are excluded from Git. The optional
`python demo.py` command demonstrates the OOP models and exports the current
database to `data.json`.

## Project files

| Path | Purpose |
| --- | --- |
| `tk_app.py` | Tkinter interface from Lab 2 |
| `pyqt_app.py` | Documented PyQt5 interface from Lab 3 |
| `school_mgmt/` | Shared models and SQLite/JSON/CSV persistence from Lab 3 |
| `database_schema.sql` | Database schema |
| `data.json` | Demonstration records |
| `tests/` | Model, persistence, GUI, and integration tests |
| `docs/` | Sphinx documentation sources adapted from Lab 3 |
| `evidence/` | Actual Lab 4 verification output |
| `GITHUB_SETUP.md` | GitHub setup and submission steps |

## Test and build documentation

With the virtual environment activated:

```bash
python -m unittest discover -s tests -v
python -m sphinx -b html -W --keep-going docs docs/_build/html
```

If macOS reports `unsupported locale setting`, run the build as
`LC_ALL=en_US.UTF-8 python -m sphinx -b html -W --keep-going docs docs/_build/html`.
Open `docs/_build/html/index.html` after the build. Tkinter integration tests
require a working desktop display; the PyQt tests use Qt's offscreen platform.
All automated GUI tests use temporary databases, leaving project data untouched.

The integration tests create a record through Tkinter, read and edit it through
PyQt, and check the result back in Tkinter. They also exercise JSON exchange
between the interfaces using the shared backend.

## Git and submission

Follow [GITHUB_SETUP.md](GITHUB_SETUP.md) to commit, publish, and submit the
repository link. For solo work, the Lab 4 handout does not require feature
branches, pull requests, or a contribution breakdown. Team work requires the
collaboration steps described in the handout.

The local repository uses `main`, with a verified integration commit and a
`v1.0` tag. Its configured remote is
`https://github.com/tatianakaado/Lab4-Tatiana_Kaado.git`.
The remote URL is a target only: GitHub repository creation and pushing are
still pending account connection. The link becomes usable after publishing.
