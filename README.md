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

## How Tkinter and PyQt work together

Both interfaces import the same `Student`, `Instructor`, `Course`, and
`DatabaseManager` classes from `school_mgmt`. Both default to the exact same
`school.db` path beside the scripts, regardless of the terminal's current
directory. A successful add, edit, or delete saves to SQLite immediately.
Opening the other interface reads those saved records and relationships.
There is no need to export JSON when switching interfaces in this project.

```text
tk_app.py   (Tkinter) ─┐
                      ├─ school_mgmt models + DatabaseManager ─ school.db
pyqt_app.py (PyQt5) ───┘
```

The integration is through shared application logic and persistent data.
The interfaces are separate windows launched independently; live automatic
synchronization between two open windows is not implemented.

To demonstrate the integration manually:

1. Run `python tk_app.py` and add a student with a unique ID and valid email.
   Optionally select a course to enroll the student.
2. Close Tkinter, then run `python pyqt_app.py` from this same project.
3. Search for the student's email. The student and course enrollment appear.
4. Select the student, choose **Edit selected**, and change the name.
5. Close PyQt and reopen `python tk_app.py`. Search for the same email;
   the updated name is displayed. Delete this test record when finished.

## Using the application

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

Latest verification: **32 tests passed, with no failures or skips**.
The integration checks use real Tkinter and PyQt widgets with temporary
databases; modal dialogs are supplied with automated test inputs.

| Integration check | Verified result |
| --- | --- |
| Add a student and enrollment in Tkinter, then read in PyQt | Same student and enrollment persist |
| Edit that student through PyQt, then refresh Tkinter | Updated name and age are visible; enrollment is retained |
| Export JSON through Tkinter and import into a separate PyQt database | All records and relationships match |

Full output: [evidence/tests.txt](evidence/tests.txt).
Test implementation: [tests/test_integration.py](tests/test_integration.py).

## Git and submission

Follow [GITHUB_SETUP.md](GITHUB_SETUP.md) to commit, publish, and submit the
repository link. For solo work, the Lab 4 handout does not require feature
branches, pull requests, or a contribution breakdown. Team work requires the
collaboration steps described in the handout.

Repository: [tatianakaado/Lab4-Tatiana_Kaado](https://github.com/tatianakaado/Lab4-Tatiana_Kaado).
The `main` branch contains the project; `v1.0` identifies the initial verified
integration. Later documentation updates appear on `main`.

For a solo submission, upload this `README.md` and the repository link to
Moodle. If the repository is private, give the instructor/TAs access using
the GitHub accounts they provide. A GitHub Release is optional for solo work.
For a team submission, also complete the handout's branch, pull request,
review, release, and actual contribution-tracking requirements.
