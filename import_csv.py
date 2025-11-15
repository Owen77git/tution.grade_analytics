# import_csv.py - Import CSV data into the database
import pandas as pd
from app import app, db
from models import User, Teacher, Student, Subject, Grade
from datetime import datetime
import os

def import_csv_data(csv_file_path='sample_grades.csv'):
    with app.app_context():
        try:
            # Check if CSV file exists
            if not os.path.exists(csv_file_path):
                print(f"❌ CSV file not found: {csv_file_path}")
                return False
            
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            print(f"Reading CSV file: {csv_file_path}")
            print(f" Found {len(df)} records")
            
            grades_added = 0
            students_created = 0
            subjects_created = 0
            teachers_checked = 0
            
            # First, ensure we have all teachers from the CSV
            unique_teachers = df['Teacher_Name'].unique()
            print(f"Found {len(unique_teachers)} unique teachers in CSV")
            
            for teacher_name in unique_teachers:
                teacher = Teacher.query.filter_by(full_name=teacher_name).first()
                if not teacher:
                    print(f"  Teacher '{teacher_name}' not found in database. Please ensure teachers exist before importing.")
            
            # Process each row in CSV
            for index, row in df.iterrows():
                # Find or create student
                student = Student.query.filter_by(student_id=row['Student_ID']).first()
                if not student:
                    # Create new student user
                    username = row['Student_Name'].replace(' ', '').lower()
                    # Check if username already exists
                    if User.query.filter_by(username=username).first():
                        username = f"{username}{row['Student_ID'].lower()}"
                    
                    student_user = User(
                        username=username,
                        email=f"{username}@tutoring.com",
                        role='student'
                    )
                    student_user.set_password('password321')
                    db.session.add(student_user)
                    db.session.flush()
                    
                    student = Student(
                        user_id=student_user.id,
                        student_id=row['Student_ID'],
                        full_name=row['Student_Name'],
                        grade_level='Form 4'
                    )
                    db.session.add(student)
                    students_created += 1
                    db.session.flush()
                
                # Find or create subject
                subject = Subject.query.filter_by(name=row['Subject']).first()
                if not subject:
                    subject = Subject(name=row['Subject'], description=row['Subject'])
                    db.session.add(subject)
                    subjects_created += 1
                    db.session.flush()
                
                # Find teacher - use the teacher name from CSV
                teacher = Teacher.query.filter_by(full_name=row['Teacher_Name']).first()
                if not teacher:
                    # If teacher not found, use the first available teacher
                    teacher = Teacher.query.first()
                    if teacher:
                        print(f"  Teacher '{row['Teacher_Name']}' not found. Using '{teacher.full_name}' instead.")
                    else:
                        print(f" No teachers found in database. Please run init_db.py first.")
                        return False
                
                # Check if this grade already exists (avoid duplicates)
                existing_grade = Grade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    topic=row['Topic'],
                    exam_date=datetime.strptime(row['Test_Date'], '%Y-%m-%d')
                ).first()
                
                if not existing_grade:
                    # Create grade
                    grade = Grade(
                        student_id=student.id,
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        score=float(row['Score']),
                        topic=row['Topic'],
                        exam_date=datetime.strptime(row['Test_Date'], '%Y-%m-%d'),
                        day_of_week=row['Day'],
                        teacher_name=row['Teacher_Name']
                    )
                    db.session.add(grade)
                    grades_added += 1
                else:
                    print(f"  Grade already exists for {row['Student_Name']} - {row['Subject']} - {row['Topic']} - {row['Test_Date']}")
            
            db.session.commit()
            print(f"\n✅ CSV Import Complete!")
            print(f" Students created: {students_created}")
            print(f" Subjects created: {subjects_created}")
            print(f"Grades added: {grades_added}")
            print(f" Total students in system: {Student.query.count()}")
            print(f"Total grades in system: {Grade.query.count()}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error importing CSV: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_database_status():
    """Check current database status"""
    with app.app_context():
        print("\n CURRENT DATABASE STATUS:")
        print(f"👥Users: {User.query.count()}")
        print(f" Students: {Student.query.count()}")
        print(f" Teachers: {Teacher.query.count()}")
        print(f" Subjects: {Subject.query.count()}")
        print(f" Grades: {Grade.query.count()}")

if __name__ == '__main__':
    print("🚀 Starting CSV Import...")
    check_database_status()
    
    # Import the CSV data
    success = import_csv_data('sample_grades.csv')
    
    if success:
        print("\n🎉 Import completed successfully!")
        check_database_status()
    else:
        print("\n💥 Import failed!")
