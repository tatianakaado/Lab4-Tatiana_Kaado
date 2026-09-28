Verification
============

Run tests from the project root with the virtual environment activated::

   python -m unittest discover -s tests -v
   python -m sphinx -b html -W --keep-going docs docs/_build/html

The inherited model and persistence tests cover validation, relationships,
CRUD, JSON round trips, backup/restore, instructor reassignment, and rollback
of invalid imports. PyQt widget tests cover search, student creation, JSON
error handling, and edit-dialog fields.

Lab 4 adds tests using actual Tkinter and PyQt widgets against temporary
SQLite files. They create a student in Tkinter, read and edit it in PyQt,
and read it back in Tkinter. A second test exports JSON through Tkinter and
imports it through PyQt into a different database, checking all records and
relationships. Native dialogs are patched to supply deterministic user input.

Tkinter requires a desktop display; its integration tests report a skip when
one is unavailable. The PyQt tests run with the offscreen platform. Inspect
the reported skip count before claiming both interfaces were tested.

Actual verification output is stored in ``evidence/tests.txt`` and
``evidence/docs-build.txt``. The README and ``GITHUB_SETUP.md`` describe the
remaining GitHub publishing and submission steps.
