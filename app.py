from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from pydantic import BaseModel, RootModel
from typing import Optional

from bucket import create_buckets
from student import Student, load_student_csv
from section import Section, export_sections_to_csv
from teacher import Teacher, load_teachers_csv, generate_teacher_dataframe
from constants import TIME_BLOCKS, LUNCH_TIME, CORE_CLASSES
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------
# In-memory application state
# -------------------------------------------------

students: dict[str, Student] = {}
teachers: dict[str, Teacher] = {}
sections: dict[str, Section] = {}

# -------------------------------------------------
# Scheduling logic (unchanged)
# -------------------------------------------------

def build_conflict_graph(
    sections_list: list[Section],
    students_list: list[Student],
    teachers_list: list[Teacher]
) -> dict[Section, set[Section]]:
    conflicts = {s: set() for s in sections_list}

    # Student conflicts
    for student in students_list:
        sched = student.get_schedule()
        for i in range(len(sched)):
            for j in range(i + 1, len(sched)):
                s1, s2 = sched[i], sched[j]
                conflicts[s1].add(s2)
                conflicts[s2].add(s1)

    # Teacher conflicts
    for teacher in teachers_list:
        sched = teacher.schedule
        for i in range(len(sched)):
            for j in range(i + 1, len(sched)):
                s1, s2 = sched[i], sched[j]
                conflicts[s1].add(s2)
                conflicts[s2].add(s1)

    return conflicts


def assign_time_blocks(
    sections_list: list[Section],
    students_list: list[Student],
    teachers_list: list[Teacher]
) -> None:
    conflicts = build_conflict_graph(sections_list, students_list, teachers_list)

    ordered = sorted(
        sections_list,
        key=lambda s: len(conflicts[s]),
        reverse=True
    )

    for section in ordered:
        if section.get_subject().lower() not in CORE_CLASSES:
            continue
        used_blocks = {
            neighbor.get_time()
            for neighbor in conflicts[section]
            if neighbor.get_time() is not None
        }

        for block in TIME_BLOCKS:
            if block not in used_blocks:
                section.set_time(block)
                break
        else:
            raise RuntimeError(f"Could not assign time block to {section}")


def check_for_conflicts(
    students_list: list[Student],
    teachers_list: list[Teacher]
) -> list[str]:
    issues = []

    for student in students_list:
        seen = {}
        for sec in student.get_schedule():
            t = sec.get_time()
            if t in seen:
                issues.append(f"Student conflict: {student}")
            seen[t] = sec

    for teacher in teachers_list:
        seen = {}
        for sec in teacher.schedule:
            t = sec.get_time()
            if t in seen:
                issues.append(f"Teacher conflict: {teacher}")
            seen[t] = sec

    return issues


# -------------------------------------------------
# Scheduler entrypoint
# -------------------------------------------------

def run_scheduler() -> list[str]:
    global sections
    sections.clear()

    students_list = list(students.values())
    teachers_list = list(teachers.values())

    # Reset schedules (important if re-running)
    for s in students_list:
        s.schedule.clear()
    for t in teachers_list:
        t.schedule.clear()

    buckets, _ = create_buckets()

    # Create sections + assign students
    for bucket in buckets:
        bucket.assign_students(students_list)
        needed = bucket.get_sections_needed()

        for i in range(needed):
            section = Section(bucket.subject, bucket.level)

            per_section = len(bucket.get_students()) // needed
            start = i * per_section
            end = start + per_section if i < needed - 1 else len(bucket.get_students())

            for student in bucket.get_students()[start:end]:
                section.add_student(student)
                student.add_section(section)

            sections[str(section.get_id())] = section

    # Assign teachers
    df = generate_teacher_dataframe(teachers_list)

    for section in sections.values():
        subject = section.get_subject().capitalize()

        preferred = df[df[subject] == 1]
        fallback = df[df[subject] == 0]
        pool = preferred if not preferred.empty else fallback

        if pool.empty:
            continue

        pool = pool.copy()
        pool["assigned"] = pool["Name"].apply(
            lambda n: len(next(t for t in teachers_list if t.name == n).schedule)
        )
        pool = pool.sort_values("assigned")

        for _, row in pool.iterrows():
            teacher = next(t for t in teachers_list if t.name == row["Name"])
            try:
                teacher.add_section(section)
                section.set_teacher(teacher)
                break
            except Exception:
                continue

    assign_time_blocks(list(sections.values()), students_list, teachers_list)
    return check_for_conflicts(students_list, teachers_list)


# -------------------------------------------------
# FastAPI lifespan handler
# -------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    students.clear()
    teachers.clear()
    sections.clear()

    for s in load_student_csv("data/students.csv"):
        students[str(s.id)] = s

    for t in load_teachers_csv("teachers.csv"):
        teachers[str(t.id)] = t

    print(f"[Startup] Loaded {len(students)} students")
    print(f"[Startup] Loaded {len(teachers)} teachers")

    # Run the scheduler ONCE
    schedule_result = run_scheduler()

    print(f"[Startup] Scheduler completed with {len(schedule_result)} conflicts")
    
    # Store results on app state
    app.state.conflicts = schedule_result

    yield

    # Optional shutdown hook
    # export_sections_to_csv(list(sections.values()), "final_sections.csv")


# -------------------------------------------------
# FastAPI app
# -------------------------------------------------

app = FastAPI(
    title="Class Scheduler API",
    lifespan=lifespan
)

# TODO: This is to access the front end with. This should be looked at to change for security reasons -----
origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----


# -------------------------------------------------
# API endpoints
# -------------------------------------------------

@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/students")
def get_students():
    return [s.to_json() for s in students.values()]


@app.get("/teachers")
def get_teachers():
    return [t.to_json() for t in teachers.values()]


@app.get("/sections")
def get_sections():
    return [s.to_json() for s in sections.values()]


@app.get("/buckets")
def get_buckets():
    buckets, _ = create_buckets()
    for b in buckets:
        b.assign_students(list(students.values()))

    return [
        {
            "name": str(b),
            "subject": b.subject,
            "level": b.level,
            "size": b.get_size(),
            "sectionsNeeded": b.get_sections_needed(),
            "studentIds": [str(s.id) for s in b.get_students()]
        }
        for b in buckets
    ]


@app.post("/schedule")
def schedule():
    conflicts = app.state.conflicts
    return {
        "sections": [s.to_json() for s in sections.values()],
        "conflicts": conflicts
    }


@app.post("/export")
def export():
    # TODO: connect this app to S3 so the csv is downloadable
    export_sections_to_csv(list(sections.values()), "final_sections.csv")
    return {"status": "exported"}

class TeacherModel(BaseModel):
    name: str
    subject_weights: dict[str, int]
    sections: int
    is_mentor: bool

class StudentModel(BaseModel):
    name: str
    subject_abilities: dict[str, int]
    section_ids: Optional[list[str]] = None

class CSV(RootModel[list[dict]]):
    pass

@app.post("/create/teacher")
def add_teacher(teacher: TeacherModel):
    print("Received:", teacher)
    t = Teacher(teacher.subject_weights, teacher.sections, teacher.name, teacher.is_mentor)
    teachers[str(t.id)] = t
    return {"message": "Teacher added", "teacher": teacher}

@app.post("/create/student")
def add_student(student: StudentModel):
    print("Received:", student)
    s = Student(student.name, **student.subject_abilities)
    if student.section_ids is not None:
        for section_id in student.section_ids:
            s.add_section(sections[section_id])     
    return {"message": "Student added", "student": student}

@app.post("/update/csv")
def update_csv(csv: CSV):
    print("Received:", csv)
    return {"message": "CSV uploaded", "csv": csv}  
