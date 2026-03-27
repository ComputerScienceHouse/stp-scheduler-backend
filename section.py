from typing import TYPE_CHECKING
from time_block import TimeBlock
from constants import CLASS_LIMIT
import uuid
import pandas as pd
from constants import TIME_BLOCKS

if TYPE_CHECKING:
    from teacher import Teacher

class Section:
    """ 
    Creates a section of a class that students will take
    Name: Name of the Class, could be seperated into 'name, difficulty'
    Time: Time block of the class
    Days: Days of the week the class is held in the format: "MTWRF"
    Capacity: How many students can take the class
    """
    def __init__(self, subject: str, level: int, time: TimeBlock | None = None, days:str | None = None, teacher: 'Teacher' = None):
        self.__id = uuid.uuid4()
        self.__subject = subject
        self.__time = time
        self.__level = level
        self.__teacher = teacher
        self.__days = days
        self.__students = []

    # Checks if the classs is at capacity
    def is_full(self):
        if len(self.__students) == CLASS_LIMIT:
            return True
        else:
            return False
    
    # adds a student to the class
    # eventually this could keep track of which students if desired
    # raises index error if class is at capacity
    # TODO: correct Error type, with handling
    def add_student(self, student):
        if self.is_full():
            return IndexError("Class is at capacity.")
        else:
            self.__students.append(student)

    def get_students(self) -> list:
        return self.__students
    
    def remove_student(self, student):
        if student in self.__students:
            self.__students.remove(student)
        else:
            return IndexError("Student not found in class.")

    def set_teacher(self,teacher):
        if teacher.is_full():
            raise IndexError("Teacher's schedule is full.")
        elif teacher.subjects[self.__subject.lower()] == -1:
            raise ValueError(f"Teacher {teacher.name} is not qualified to teach {self.__subject}.")
        else:
            self.__teacher = teacher
            
    def remove_teacher(self):
        self.__teacher = None
    
    def set_time(self, time: TimeBlock):
        self.__time = time
    
    def get_days(self):
        return self.__days
    
    def set_days(self, days: str):
        self.__days = days
    
    def get_teacher(self):
        return self.__teacher

    def get_time(self):
        return self.__time
    
    def get_level(self):
        return self.__level
    
    def get_subject(self):
        return self.__subject
    
    def get_id(self):
        return self.__id
    
    def __str__(self):
        return f"Section({self.__subject}, {self.__time}, {self.__level}, {self.__teacher})"
    
    def __repr__(self):
        return self.__str__()
    
    def to_json(self) -> dict:
        return {
            "id": str(self.__id),
            "subject": self.__subject,
            "level": self.__level,
            "timeBlockId": TIME_BLOCKS.index(self.__time) if self.__time else None,
            "days": self.__days,
            "teacherId": str(self.__teacher.id) if self.__teacher else None,
            "studentIds": [str(student.id) for student in self.__students]
        }
        
def export_sections_to_csv(sections: list[Section], file_name: str) -> None:
    import pandas as pd
    data = []
    for section in sections:
        data.append({
            "Subject": section.get_subject(),
            "Level": section.get_level(),
            "Time": str(section.get_time()),
            "Days": section.get_days(),
            "Teacher": section.get_teacher().name if section.get_teacher() else "Unassigned",
            "Students": " | ".join([str(student) for student in section.get_students()])
        })
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)
    