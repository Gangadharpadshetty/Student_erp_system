from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone_no = Column(String)
    date_of_joining = Column(Date, default=datetime.date.today)
    years_of_experience = Column(Integer)
    subject_specialization = Column(String)

    # Relationship: A teacher can be a class teacher for one class
    class_managed = relationship("Class", back_populates="class_teacher", uselist=False)

class Class(Base):
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True, index=True)
    class_number = Column(Integer) # 1 to 10
    class_teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"))

    class_teacher = relationship("Teacher", back_populates="class_managed")
    students = relationship("Student", back_populates="classroom")

class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    roll_no = Column(Integer)
    date_joined = Column(Date, default=datetime.date.today)
    year = Column(String)
    class_id = Column(Integer, ForeignKey("classes.class_id"))

    classroom = relationship("Class", back_populates="students")
    reports = relationship("Report", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")
    tickets = relationship("Ticket", back_populates="student")

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True)
    year = Column(String)
    student_id = Column(Integer, ForeignKey("students.student_id"))
    class_id = Column(Integer, ForeignKey("classes.class_id"))

    eng_marks = Column(Integer)
    kannada_marks = Column(Integer)
    hindi_marks = Column(Integer)
    math_marks = Column(Integer)
    science_marks = Column(Integer)
    social_science_marks = Column(Integer)

    overall_percentage = Column(Float)
    result_status = Column(String) # PASS/FAIL

    student = relationship("Student", back_populates="reports")

class Academics(Base):
    __tablename__ = "academics"

    academic_id = Column(Integer, primary_key=True, index=True)
    year = Column(String)
    class_id = Column(Integer, ForeignKey("classes.class_id"))
    total_students = Column(Integer)
    fees_collected = Column(Float)
    teacher_salaries = Column(Float)
    students_passed = Column(Integer)
    distinctions = Column(Integer)

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id"))
    class_id = Column(Integer, ForeignKey("classes.class_id"))
    year = Column(String)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"))
    date = Column(Date, default=datetime.date.today)
    status = Column(String) # Present/Absent

    student = relationship("Student", back_populates="attendance")

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id"))
    issue_description = Column(Text)
    status = Column(String, default="Open") # Open/Resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    student = relationship("Student", back_populates="tickets")

class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
