Tkinter interface
=================

Run ``python tk_app.py`` from the project folder with the virtual environment
activated. This interface is carried forward from Lab 2 and uses the shared
models and corrected persistence layer documented in the API reference.

The Student, Instructor, and Course forms add validated records. The table
supports search, editing, and deletion. Save/Load JSON and Backup/Restore DB
use the same formats as PyQt. CSV export is available in PyQt.

The default database is ``school.db`` next to both scripts. Close Tkinter and
launch ``python pyqt_app.py`` to continue using the saved records in PyQt.
