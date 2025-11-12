# init_db.py - Fixed database initialization with first name usernames
from app import app, db
from models import User, Teacher, Student, Subject, Grade
from datetime import datetime, timedelta
import random

def init_sample_data():
    with app.app_context():
        try:
            # Clear existing data
            db.drop_all()
            db.create_all()
            
            print("Creating sample data...")
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@tutoring.com',
                role='admin'
            )
            admin_user.set_password('password321')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created")
            
            # Create teachers with first name usernames
            teachers_data = [
                {'name': 'Mr. Kamau', 'subjects': 'Mathematics,Physics', 'username': 'kamau'},
                {'name': 'Mrs. Moraa', 'subjects': 'English,Literature', 'username': 'moraa'},
                {'name': 'Mr. Njoroge', 'subjects': 'Mathematics,Chemistry', 'username': 'njoroge'},
                {'name': 'Mrs. Atieno', 'subjects': 'English,History', 'username': 'atieno'}
            ]
            
            teachers = {}
            for teacher_data in teachers_data:
                # Check if username already exists
                if User.query.filter_by(username=teacher_data['username']).first():
                    print(f"✓ Teacher {teacher_data['username']} already exists")
                    continue
                    
                teacher_user = User(
                    username=teacher_data['username'],
                    email=f"{teacher_data['username']}@tutoring.com",
                    role='teacher'
                )
                teacher_user.set_password('password321')
                db.session.add(teacher_user)
                db.session.commit()
                
                teacher = Teacher(
                    user_id=teacher_user.id,
                    full_name=teacher_data['name'],
                    subjects=teacher_data['subjects']
                )
                db.session.add(teacher)
                db.session.commit()
                
                teachers[teacher_data['name']] = teacher
                print(f"✓ Teacher {teacher_data['username']} created")
            
            # Create students with first name usernames
            students_data = [
                {'name': 'Samuel Mwangi', 'student_id': 'ST001', 'grade_level': 'Form 4', 'username': 'samuel'},
                {'name': 'Ruth Naliaka', 'student_id': 'ST002', 'grade_level': 'Form 4', 'username': 'ruth'},
                {'name': 'Dennis Kariuki', 'student_id': 'ST003', 'grade_level': 'Form 4', 'username': 'dennis'},
                {'name': 'Mercy Chebet', 'student_id': 'ST004', 'grade_level': 'Form 4', 'username': 'mercy'},
                {'name': 'Kevin Kiptoo', 'student_id': 'ST005', 'grade_level': 'Form 4', 'username': 'kevin'},
                {'name': 'Vivian Obiero', 'student_id': 'ST006', 'grade_level': 'Form 4', 'username': 'vivian'}
            ]
            
            students = {}
            for student_data in students_data:
                # Check if username already exists
                if User.query.filter_by(username=student_data['username']).first():
                    print(f"✓ Student {student_data['username']} already exists")
                    continue
                    
                student_user = User(
                    username=student_data['username'],
                    email=f"{student_data['username']}@tutoring.com",
                    role='student'
                )
                student_user.set_password('password321')
                db.session.add(student_user)
                db.session.commit()
                
                student = Student(
                    user_id=student_user.id,
                    student_id=student_data['student_id'],
                    full_name=student_data['name'],
                    grade_level=student_data['grade_level']
                )
                db.session.add(student)
                db.session.commit()
                
                students[student_data['student_id']] = student
                print(f"✓ Student {student_data['username']} created")
            
            # Create subjects
            subjects_data = {
                'Mathematics': 'Algebra, Geometry, Trigonometry, Statistics',
                'English': 'Grammar, Composition, Comprehension, Literature',
                'Physics': 'Mechanics, Electricity, Waves, Thermodynamics',
                'Chemistry': 'Organic, Inorganic, Physical Chemistry',
                'History': 'World History, African History, Modern History'
            }
            
            subjects = {}
            for subject_name, description in subjects_data.items():
                subject = Subject.query.filter_by(name=subject_name).first()
                if not subject:
                    subject = Subject(
                        name=subject_name,
                        description=description
                    )
                    db.session.add(subject)
                    db.session.commit()
                subjects[subject_name] = subject
                print(f"✓ Subject {subject_name} created")
            
            # Create sample grades (only if we have teachers and students)
            if teachers and students:
                topics = ['Algebra', 'Geometry', 'Trigonometry', 'Statistics', 'Grammar', 'Composition', 'Mechanics', 'Electricity']
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                
                grade_count = 0
                for student in students.values():
                    for i in range(15):  # 15 grades per student
                        subject_name = random.choice(['Mathematics', 'English', 'Physics'])
                        teacher_name = random.choice(list(teachers.keys()))
                        
                        grade = Grade(
                            student_id=student.id,
                            teacher_id=teachers[teacher_name].id,
                            subject_id=subjects[subject_name].id,
                            score=random.randint(60, 95),
                            topic=random.choice(topics),
                            exam_date=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                            day_of_week=random.choice(days),
                            teacher_name=teacher_name
                        )
                        db.session.add(grade)
                        grade_count += 1
                
                db.session.commit()
                print(f"✓ {grade_count} sample grades created")
            
            print("\n" + "="*50)
            print("✅ DATABASE INITIALIZED SUCCESSFULLY!")
            print("="*50)
            print("\n📋 LOGIN CREDENTIALS:")
            print("👑 ADMIN: admin / password321")
            print("👨‍🏫 TEACHERS:")
            print("   - kamau / password321")
            print("   - moraa / password321") 
            print("   - njoroge / password321")
            print("   - atieno / password321")
            print("👨‍🎓 STUDENTS:")
            print("   - samuel / password321")
            print("   - ruth / password321")
            print("   - dennis / password321")
            print("   - mercy / password321")
            print("   - kevin / password321")
            print("   - vivian / password321")
            print("\n🚀 Start the application with: python app.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_sample_data()
