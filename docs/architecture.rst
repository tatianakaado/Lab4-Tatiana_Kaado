Architecture and Lab 2 corrections
==================================

Layers and relationships
------------------------

``tk_app`` contains ``SchoolManagementTk``. Both GUI modules call the same
``school_mgmt`` package and default to the same project-relative database.
Each interface runs its own event loop in a separate process. Closing one
and opening the other reloads the persisted records.


``pyqt_app`` contains ``SchoolManagementQt`` and ``EditDialog``. Signals from
buttons and search fields call methods that validate models, invoke
``DatabaseManager``, and refresh the widgets.

``school_mgmt.models`` contains the abstract ``Person`` base class, derived
``Student`` and ``Instructor`` classes, ``Course``, and reusable validators.
Dataclasses hold entity fields; the email property validates writes.

``school_mgmt.storage`` owns the four SQLite tables: ``students``,
``instructors``, ``courses``, and ``enrollments``. A course has zero or one
instructor, an instructor has many courses, and students and courses have a
many-to-many relationship through enrollments.

.. code-block:: text

   Tkinter / PyQt widgets -> validated models -> DatabaseManager -> SQLite
                                             |
                                  JSON / CSV / backup files

Correction 1: outdated instructor link
--------------------------------------

Previously, assigning a second Instructor object to a Course changed the
course's instructor ID but left that course in the first object's
``assigned_courses`` list. The course now remembers its assigned instructor
object, removes the previous link on reassignment/unassignment, and adds the
new link once. Calling ``Instructor.assign_course(course)`` uses the same
operation. ID-only assignment does not resolve unrelated Python objects;
SQLite assignments remain authoritative for stored records.

.. code-block:: python

   from school_mgmt import Course, Instructor
   first = Instructor("First", 40, "first@example.com", "I1")
   second = Instructor("Second", 41, "second@example.com", "I2")
   course = Course("C1", "Software Tools")
   course.assign_instructor(first)
   course.assign_instructor(second)
   assert first.assigned_courses == []
   assert second.assigned_courses == ["C1"]
   assert course.instructor == "I2"

Correction 2: failed JSON import erased records
-----------------------------------------------

Previously, deleting the original rows committed before replacement records
were inserted. A later constraint error could leave partial or empty data.
``load_json`` now validates the input shape and constructs models first,
then performs every deletion and insertion within **one SQLite transaction**.
If a duplicate identifier/email or dangling relationship raises an error,
the context manager rolls back all changes, including deletions.

Successful imports reconcile both sides of enrollments and reject conflicting
instructor assignments. JSON syntax errors, missing fields, and invalid shapes
fail before database changes. Only an explicitly valid empty payload clears data.

The empty-database check was also corrected to inspect all three entity tables,
so opening a database containing only instructors/courses does not reseed it.
