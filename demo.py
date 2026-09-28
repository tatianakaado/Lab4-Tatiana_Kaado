"""Part 1 demonstration: OOP, polymorphism, abstraction and serialization."""

from pathlib import Path

from school_mgmt import Course, DatabaseManager, Instructor, Person, Student


BASE_DIR = Path(__file__).resolve().parent


def introduce_everyone(people: list[Person]) -> None:
    """Polymorphism: one call works for every Person subclass."""
    for person in people:
        print(person.introduce())


def main() -> None:
    database = DatabaseManager(BASE_DIR / "school.db")
    database.seed_demo()

    course = Course("EECE435L", "Software Tools Laboratory")
    student = Student("Tatiana Kaado", 21, "tgk12@mail.aub.edu", "202400900")
    instructor = Instructor("Dr. Lina Haddad", 41, "lina.haddad@aub.edu.lb", "I001")

    course.add_student(student)
    course.assign_instructor(instructor)
    introduce_everyone([student, instructor])
    print(f"{course.course_name}: {len(course.enrolled_students)} enrolled student(s)")

    output = database.save_json(BASE_DIR / "data.json")
    print(f"Saved database records to {output.name}")


if __name__ == "__main__":
    main()
