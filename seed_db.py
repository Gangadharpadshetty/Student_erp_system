from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, DATABASE_URL
from app.models import Teacher, Student, Class, SystemLog
from app.utils.security import hash_password

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    print("Connecting to Render PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Classes first (Foreign Key requirement)
        # Creating 10 classes (1-10)
        for i in range(1, 11):
            if not db.query(Class).filter(Class.class_id == i).first():
                db.add(Class(class_id=i, class_number=i))
        db.commit()
        print("✅ Classes 1-10 created.")

        # 2. Create Admin (Special Case)
        # Since we don't have an Admin table, we'll ensure the logic in auth_controller works,
        # but for a real DB, we might add them to a user table.
        # For now, the auth_controller handles 'admin@erp.com' hardcoded.

        # 3. Seed Teachers
        teachers_data = [
            {"name": "Mr. Rajesh", "email": "math_teacher@erp.com", "password": "pass123", "phone": "1234567890", "exp": 10, "sub": "Mathematics"},
            {"name": "Ms. anu", "email": "sci_teacher@erp.com", "password": "pass123", "phone": "0987654321", "exp": 8, "sub": "Science"},
        ]

        for t in teachers_data:
            if not db.query(Teacher).filter(Teacher.email == t["email"]).first():
                db.add(Teacher(
                    name=t["name"], email=t["email"], password=hash_password(t["password"]),
                    phone_no=t["phone"], years_of_experience=t["exp"], subject_specialization=t["sub"]
                ))
        db.commit()
        print("✅ Teachers seeded.")

        # 4. Seed Students
        students_data = [
            {"name": "Amit Kumar", "email": "student1@erp.com", "password": "pass123", "roll": 1, "year": "2024", "class_id": 1},
            {"name": "Suman Rao", "email": "student2@erp.com", "password": "pass123", "roll": 2, "year": "2024", "class_id": 1},
            {"name": "Vijay Singh", "email": "student3@erp.com", "password": "pass123", "roll": 3, "year": "2024", "class_id": 1},
        ]

        for s in students_data:
            if not db.query(Student).filter(Student.email == s["email"]).first():
                db.add(Student(
                    name=s["name"], email=s["email"], password=hash_password(s["password"]),
                    roll_no=s["roll"], year=s["year"], class_id=s["class_id"]
                ))
        db.commit()
        print("✅ Students seeded.")

        # 5. Assign Teacher to Class 1
        teacher = db.query(Teacher).first()
        if teacher:
            classroom = db.query(Class).filter(Class.class_id == 1).first()
            if classroom:
                classroom.class_teacher_id = teacher.teacher_id
                db.commit()
                print(f"✅ Assigned {teacher.name} to Class 1.")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("\n🚀 Database initialized on Render PostgreSQL successfully!")
