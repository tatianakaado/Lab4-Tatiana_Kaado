Installation and user guide
===========================

Build and open the documentation
--------------------------------

Install the dependencies below, then run from the project root::

   python -m sphinx -b html -W --keep-going docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser. Generated HTML is excluded
from Git and can be rebuilt from the tracked documentation sources.

Install and run either application
------------------------------------

Use Python 3.11 or newer; this submission was verified with Python 3.13.
From the extracted project directory on macOS/Linux::

   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   python pyqt_app.py

Alternatively, run ``python tk_app.py``. Close one interface before switching
to the other; both use the same ``school.db`` beside the scripts. Tkinter must
be installed with Python. CSV export is available in PyQt only.

On Windows, create the environment with ``py -m venv .venv`` and activate
it using ``.venv\Scripts\activate`` in Command Prompt. The remaining
``python`` commands are the same. A desktop session is required for the GUI.

The application creates ``school.db`` beside ``pyqt_app.py`` and seeds a
completely empty database with sample data. The supplied ``data.json`` is
also available through **Load JSON**. These are demonstration records.

Using the dashboard
-------------------

1. Select **Student**, **Instructor**, or **Course** and complete its form.
   Names and IDs are required; people also need a valid email and age 0–130.
2. Choose an optional course when adding a student or instructor, or choose
   an instructor when creating a course. Add an instructor before assigning
   that instructor to a course. Add a course before enrolling students in it.
3. Use the search box to filter displayed names, IDs, emails, and relationships.
4. Select a row and press **Edit selected**, or double-click it. The dialog
   edits a person's name, age, and email, or a course's name. IDs stay fixed.
5. **Delete** asks for confirmation. Student/course removal also removes
   enrollments; instructor removal leaves its courses unassigned.
6. **Save JSON** exports all records. **Load JSON** replaces the current data;
   a malformed file or a failed database insertion preserves existing records.
7. **Export CSV** writes three separate entity files into the chosen directory.
8. **Backup DB** creates a SQLite copy. **Restore DB** asks for confirmation
   before replacing the current database with the selected backup.

Relationship details
--------------------

The instructor form assigns a course to the newly created instructor; there
is no separate button for reassigning an existing instructor. Programmatic
reassignment is available through ``DatabaseManager.assign_instructor``.
The SQLite foreign key determines the current assignment. Query the models
again after a database change; fetched objects are snapshots.

JSON format
-----------

All three lists are required. A payload containing three empty lists explicitly
clears the records. Identifiers referenced by relationships must exist. Duplicate
IDs/emails and contradictory instructor assignments are rejected. Student-side
and course-side enrollment declarations are combined without duplicates.

.. literalinclude:: ../data.json
   :language: json
   :lines: 1-22
   :caption: Beginning of the supplied Lab 2 JSON sample

Known inherited behavior
------------------------

Relationship display uses comma-separated SQL aggregation, so use IDs without
commas. CSV export of an empty entity table creates an empty file. Restore expects
a valid backup created by this application. New-student creation and its optional
enrollment use separate operations; a database error during that enrollment can
leave the newly created student present. These are separate from the corrected
transactional JSON import.
