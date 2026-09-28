PRAGMA foreign_keys = ON;

CREATE TABLE students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0),
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE instructors (
    instructor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0),
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE courses (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    instructor_id TEXT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE enrollments (
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
