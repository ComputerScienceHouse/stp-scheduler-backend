from section import Section
import uuid

class Student:
    def __init__(self, name, english, math, asl):
        self.id = uuid.uuid4()
        self.name = name
        self.subject_rankings = {"math": math, "english": english, "asl": asl}
        self.schedule = []

    def is_full(self) -> bool:
        """
        Checks if the student's schedule is full.
        """
        return len(self.schedule) >= 6
    
    def get_subject_rankings(self) -> dict:
        """Returns the student's subject rankings"""
        return self.subject_rankings

    def get_english_level(self) -> int:
        """Returns the student's English level"""
        return 0 if self.subject_rankings["english"] <= 3 else 2 if self.subject_rankings["english"] > 6 else 1
    
    def get_math_level(self) -> int:
        """Returns the student's Math level"""
        return 0 if self.subject_rankings["math"] <= 3 else 2 if self.subject_rankings["math"] > 6 else 1
    
    def get_asl_level(self) -> int:
        """Returns the student's ASL level"""
        return 0 if self.subject_rankings["asl"] <= 3 else 2 if self.subject_rankings["asl"] > 6 else 1
    
    def add_section(self, course: Section):
        """Adds a class to the student's schedule"""
        # Check if the course is already in the schedule
        if course not in self.schedule:
            self.schedule.append(course)
    
    def remove_section(self, course: Section):
        """Removes a class from the student's schedule"""
        # Check if the course is in the schedule
        if course in self.schedule:
            self.schedule.remove(course)
            # course.remove_student(self)
    
    def get_schedule(self) -> list[Section]:
        """Returns a list of sections that the student is enrolled in"""
        return self.schedule
    
    def __str__(self):
        return f"{self.name}"
    
    def __hash__(self):
        return hash((self.name, self.english, self.math, self.asl))
    
    def __eq__(self, other):
        if isinstance(other, Student):
            return self.name == other.name and self.english == other.english and self.math == other.math and self.asl == other.asl
        return False
    
    def __repr__(self):
        return self.__str__()
    
    def to_json(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "subject_rankings": self.subject_rankings,
            "sectionIds": [str(section.get_id()) for section in self.schedule]
        }
    
def load_student_csv(file_name) -> list[Student]:
    """
    CSV Format: 
    Name, English, Math, ASL
    """
    with open(file_name, 'r') as file:
        data = file.readlines()
    data = [line.strip().split(',') for line in data]
    students = []
    
    for i, line in enumerate(data):
        if i == 0:
            continue
        if line[0] == '':
            line[0] = 'Unknown'
        if line[1] == '':
            line[1] = 0
        if line[2] == '':
            line[2] = 0
        if line[3] == '':
            line[3] = 0
        
        name = line[0]
        english = int(line[1])
        math = int(line[2])
        asl = int(line[3])
        students.append(Student(name, english, math, asl))
    
    return students

def delete_student(student: Student):
    for section in student.get_schedule():
        section.remove_student(student)
    del student # might not be necessary

if __name__ == "__main__":
    students = load_student_csv("data/students.csv")
    for student in students:
        print(student)