"""Object-oriented domain models for the School Management System."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
from typing import Any


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")


class ValidationError(ValueError):
    """ValueError subclass for invalid school record fields.
    """


def validate_required(value: str, label: str) -> str:
    """Trim a value and reject an empty result.
    
    :param value: Value converted to text and stripped.
    :type value: str
    :param label: Field label used in the error message.
    :type label: str
    :raises ValidationError: The text is empty.
    :return: Nonempty trimmed text.
    :rtype: str
    """
    value = str(value).strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    return value


def validate_age(value: int | str) -> int:
    """Convert an age to an integer and check the inclusive range 0 to 130.
    
    :param value: Integer age or text accepted by int().
    :type value: int or str
    :raises ValidationError: Conversion fails or age is outside the accepted range.
    :return: Validated age.
    :rtype: int
    """
    try:
        age = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Age must be a whole number.") from exc
    if age < 0:
        raise ValidationError("Age cannot be negative.")
    if age > 130:
        raise ValidationError("Age must be 130 or less.")
    return age


def validate_email(value: str) -> str:
    """Strip surrounding whitespace and validate email syntax.
    
    :param value: Email address to check.
    :type value: str
    :raises ValidationError: The value does not match EMAIL_PATTERN.
    :return: Validated email address.
    :rtype: str
    """
    email = str(value).strip()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValidationError("Enter a valid email address (for example, name@example.com).")
    return email


@dataclass
class Person(ABC):
    """Abstract validated base class for people in the school.
    
    Subclasses implement :meth:`introduce` and :meth:`to_dict`.
    
    :ivar name: Trimmed full name.
    :ivar age: Validated integer age.
    :ivar _email: Encapsulated email accessed through the email property.
    
    :param name: Nonempty full name.
    :type name: str
    :param age: Age from 0 through 130.
    :type age: int
    :param _email: Initial email, validated through the email property.
    :type _email: str
    """

    name: str
    age: int
    _email: str

    def __post_init__(self) -> None:
        """Validate required fields and normalize this model after dataclass construction.
        
        :raises ValidationError: A required field, age, or email is invalid.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        self.name = validate_required(self.name, "Name")
        self.age = validate_age(self.age)
        self.email = self._email

    @property
    def email(self) -> str:
        """Read or validate and replace the encapsulated email.
        
        Assignment validates the new value and raises ValidationError if invalid.
        
        :return: The current validated email address.
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Validate and store a new email address.
        
        :param value: New email address.
        :type value: str
        :raises ValidationError: The address has invalid syntax.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        self._email = validate_email(value)

    @abstractmethod
    def introduce(self) -> str:
        """Return an introduction identifying this person and their role.
        
        :return: Human-readable introduction.
        :rtype: str
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize public fields and relationship IDs for JSON export.
        
        :return: JSON-compatible fields; relationship lists are copied.
        :rtype: dict[str, Any]
        """


@dataclass
class Student(Person):
    """Person with a unique student ID and a list of registered course IDs.
    
    :param name: Nonempty full name.
    :type name: str
    :param age: Age from 0 through 130.
    :type age: int
    :param _email: Initial email, validated through the email property.
    :type _email: str
    :param student_id: Nonempty student identifier.
    :type student_id: str
    :param registered_courses: Course IDs; defaults to a new empty list, with duplicates removed.
    :type registered_courses: list[str]
    """
    student_id: str
    registered_courses: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate required fields and normalize this model after dataclass construction.
        
        :raises ValidationError: A required field, age, or email is invalid.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        super().__post_init__()
        self.student_id = validate_required(self.student_id, "Student ID")
        self.registered_courses = list(dict.fromkeys(self.registered_courses))

    def introduce(self) -> str:
        """Return an introduction identifying this person and their role.
        
        :return: Human-readable introduction.
        :rtype: str
        """
        return f"I am {self.name}, student {self.student_id}."

    def register_course(self, course: Course | str) -> None:
        """Add a course ID once to this student.
        
        This method changes the student side only. Use Course.add_student with
        a Student object to update both in-memory sides, or DatabaseManager for storage.
        
        :param course: Course object or nonempty identifier.
        :type course: Course or str
        :raises ValidationError: A supplied string ID is empty.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        course_id = course.course_id if isinstance(course, Course) else validate_required(course, "Course ID")
        if course_id not in self.registered_courses:
            self.registered_courses.append(course_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize public fields and relationship IDs for JSON export.
        
        :return: JSON-compatible fields; relationship lists are copied.
        :rtype: dict[str, Any]
        """
        return {
            "student_id": self.student_id,
            "name": self.name,
            "age": self.age,
            "email": self.email,
            "registered_courses": list(self.registered_courses),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Student:
        """Construct a student from a JSON-compatible dictionary.
        
        :param data: Fields in the format produced by to_dict(); relationship lists are optional.
        :type data: dict[str, Any]
        :raises KeyError: A required key is missing.
        :raises ValidationError: A field is invalid.
        :return: New validated model.
        :rtype: Student
        """
        return cls(
            data["name"], data["age"], data["email"], data["student_id"],
            list(data.get("registered_courses", [])),
        )


@dataclass
class Instructor(Person):
    """Person with an instructor ID and assigned course IDs.
    
    :param name: Nonempty full name.
    :type name: str
    :param age: Age from 0 through 130.
    :type age: int
    :param _email: Initial email, validated through the email property.
    :type _email: str
    :param instructor_id: Nonempty instructor identifier.
    :type instructor_id: str
    :param assigned_courses: Assigned course IDs; defaults to a new empty list.
    :type assigned_courses: list[str]
    """
    instructor_id: str
    assigned_courses: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate required fields and normalize this model after dataclass construction.
        
        :raises ValidationError: A required field, age, or email is invalid.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        super().__post_init__()
        self.instructor_id = validate_required(self.instructor_id, "Instructor ID")
        self.assigned_courses = list(dict.fromkeys(self.assigned_courses))

    def introduce(self) -> str:
        """Return an introduction identifying this person and their role.
        
        :return: Human-readable introduction.
        :rtype: str
        """
        return f"I am {self.name}, instructor {self.instructor_id}."

    def assign_course(self, course: Course | str) -> None:
        """Assign a course object consistently, or append a course ID once.
        
        For an object, delegates to Course.assign_instructor so the old instructor
        link is removed. A string updates this object only; it cannot resolve others.
        
        :param course: Course object or nonempty identifier.
        :type course: Course or str
        :raises ValidationError: A supplied string ID is empty.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        if isinstance(course, Course):
            course.assign_instructor(self)
        else:
            course_id = validate_required(course, "Course ID")
            if course_id not in self.assigned_courses:
                self.assigned_courses.append(course_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize public fields and relationship IDs for JSON export.
        
        :return: JSON-compatible fields; relationship lists are copied.
        :rtype: dict[str, Any]
        """
        return {
            "instructor_id": self.instructor_id,
            "name": self.name,
            "age": self.age,
            "email": self.email,
            "assigned_courses": list(self.assigned_courses),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Instructor:
        """Construct a instructor from a JSON-compatible dictionary.
        
        :param data: Fields in the format produced by to_dict(); relationship lists are optional.
        :type data: dict[str, Any]
        :raises KeyError: A required key is missing.
        :raises ValidationError: A field is invalid.
        :return: New validated model.
        :rtype: Instructor
        """
        return cls(
            data["name"], data["age"], data["email"], data["instructor_id"],
            list(data.get("assigned_courses", [])),
        )


@dataclass
class Course:
    """Course with an optional instructor ID and enrolled student IDs.
    
    Relationships serialize as identifiers, not nested objects. When an
    Instructor object is assigned, a private reference lets reassignment remove
    the course from the previous object. Objects restored from dictionaries
    contain IDs only; use DatabaseManager for persistent relationship updates.
    
    :param course_id: Nonempty course identifier.
    :type course_id: str
    :param course_name: Nonempty course title.
    :type course_name: str
    :param instructor: Assigned instructor ID; defaults to None.
    :type instructor: str or None
    :param enrolled_students: Student IDs; defaults to a new empty list.
    :type enrolled_students: list[str]
    """
    course_id: str
    course_name: str
    instructor: str | None = None
    enrolled_students: list[str] = field(default_factory=list)

    _instructor_object: Instructor | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate required fields and normalize this model after dataclass construction.
        
        :raises ValidationError: A required field, age, or email is invalid.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        self.course_id = validate_required(self.course_id, "Course ID")
        self.course_name = validate_required(self.course_name, "Course name")
        self.instructor = self.instructor or None
        self.enrolled_students = list(dict.fromkeys(self.enrolled_students))

    def add_student(self, student: Student | str) -> None:
        """Enroll a student once and update the supplied Student object.
        
        :param student: Student object or nonempty student ID.
        :type student: Student or str
        :raises ValidationError: A supplied string ID is empty.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        student_id = student.student_id if isinstance(student, Student) else validate_required(student, "Student ID")
        if student_id not in self.enrolled_students:
            self.enrolled_students.append(student_id)
        if isinstance(student, Student):
            student.register_course(self)

    def assign_instructor(self, instructor: Instructor | str | None) -> None:
        """Replace or clear the instructor and remove a tracked obsolete link.
        
        When an object was previously assigned, remove this course from that
        object before linking another instructor. Repeating the assignment does
        not duplicate the course. ID-only values do not resolve external objects.
        
        :param instructor: New instructor object/ID, or None to unassign.
        :type instructor: Instructor or str or None
        :raises ValidationError: A supplied string ID is empty.
        :return: No return value; updates state or performs the described action.
        :rtype: None
        """
        instructor_id = (
            instructor.instructor_id if isinstance(instructor, Instructor)
            else None if instructor is None
            else validate_required(instructor, "Instructor ID")
        )
        previous = self._instructor_object
        if previous is not None and (
            previous.instructor_id != instructor_id
            or isinstance(instructor, Instructor) and previous is not instructor
        ):
            previous.assigned_courses[:] = [
                value for value in previous.assigned_courses if value != self.course_id
            ]
            self._instructor_object = None
        self.instructor = instructor_id
        if isinstance(instructor, Instructor):
            self._instructor_object = instructor
            if self.course_id not in instructor.assigned_courses:
                instructor.assigned_courses.append(self.course_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize public fields and relationship IDs for JSON export.
        
        :return: JSON-compatible fields; relationship lists are copied.
        :rtype: dict[str, Any]
        """
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor": self.instructor,
            "enrolled_students": list(self.enrolled_students),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Course:
        """Construct a course from a JSON-compatible dictionary.
        
        :param data: Fields in the format produced by to_dict(); relationship lists are optional.
        :type data: dict[str, Any]
        :raises KeyError: A required key is missing.
        :raises ValidationError: A field is invalid.
        :return: New validated model.
        :rtype: Course
        """
        return cls(
            data["course_id"], data["course_name"], data.get("instructor"),
            list(data.get("enrolled_students", [])),
        )
