import uuid
import pandas as pd
from section import Section

class Teacher:
    def __init__(self, subjects_rankings: dict, sections: int, name: str, is_mentor=False):
        self.id = uuid.uuid4()
        self.name = name
        self.subjects = subjects_rankings
        self.sections = int(sections)
        self.is_mentor = is_mentor
        self.schedule: list[Section] = []
    
    def is_full(self):
        """
        Checks if the teacher's schedule is full.
        """
        return len(self.schedule) == self.sections
    
    def get_schedule(self) -> list[Section]:
        return self.schedule

    def add_section(self, section: Section):
        """
        Adds a section to the teacher's schedule.
        """
        if self.is_full():
            raise IndexError("Teacher's schedule is full.")
        elif self.subjects[section.get_subject().lower()] == -1:
            raise ValueError(f"Teacher {self.name} is not qualified to teach {section.get_subject()}.")
        else:
            self.schedule.append(section)
            
    def remove_section(self, section: Section):
        if section in self.schedule:
            section.remove_teacher()
            self.schedule.remove(section)
    
    def set_name(self, name):
        self.name = name
    
    def set_subjects(self, subject_rankings):
        self.subjects = subject_rankings
        
    def set_sections(self, sections):
        self.sections = sections
        
    def set_mentor(self, is_mentor):
        self.is_mentor = is_mentor
    
    def __str__(self):
        return f"{self.name}: {self.sections} sections{' (Mentor)' if self.is_mentor else ''}"
    
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash((self.name, self.sections, self.is_mentor))
    
    def __eq__(self, other):
        if isinstance(other, Teacher):
            return self.name == other.name and self.sections == other.sections and self.is_mentor == other.is_mentor
        return False
    
    def to_json(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "subjects": self.subjects,
            "sectionIds": [str(section.get_id()) for section in self.schedule],
            "is_mentor": self.is_mentor
        }
    
def load_teachers_csv(file_name) -> list[Teacher]:
    """
    Teacher format:
    Teacher,Class,Weight
    Ex:
    Nathan,ASL,-1
    Nathan,Math,1
    Nathan,English,0
    Jeanne,ASL,-1
    Jeanne,Engli8sh,1
    Jeanne,Math,0
    """
    teachers = []
    df = pd.read_csv(file_name)
    # Teacher, Class, Weight
    grouped = df.groupby('Teacher')
    for name, group in grouped:
        subjects_rankings = {}
        for _, row in group.iterrows():
            subjects_rankings[row['Class'].lower()] = int(row['Weight'])
        sections = 6 # default to 6 sections per teacher
        is_mentor = False # default to false while we don't have that data
        teacher = Teacher(subjects_rankings, sections, name, is_mentor)
        teachers.append(teacher)
    return teachers

def generate_teacher_dataframe(teachers: list[Teacher]) -> pd.DataFrame:
    """ 
    Generates a pandas DataFrame from a list of Teacher objects.
    Columns: Name, Subject1, Subject2, Subject3, ...
    Rows: Each teacher and their subject rankings
    """
    data = []
    for teacher in teachers:
        row = {'Name': teacher.name}
        for subject, ranking in teacher.subjects.items():
            row[subject.capitalize()] = ranking
        data.append(row)
    df = pd.DataFrame(data)
    return df

def delete_teacher(teacher: Teacher):
    for section in teacher.get_schedule():
        teacher.remove_section(section)
    del teacher # might not be necessary

if __name__ == "__main__":
    teachers = load_teachers_csv("teachers.csv")
    print(teachers)
    for teacher in teachers:
        print(teacher.subjects)
    df = generate_teacher_dataframe(teachers)
    print(df)