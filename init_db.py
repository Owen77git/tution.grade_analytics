# init_db.py - Fixed database initialization - ONLY CREATES ADMIN
from app import create_app
from models import db, User, Teacher, Student, Subject, Grade

def init_sample_data():
    app = create_app()
    with app.app_context():
        try:
            # Clear existing data
            print("🔄 Initializing database...")
            db.drop_all()
            db.create_all()
            
            print("Creating admin user only...")
            
            # Create admin user ONLY
            admin_user = User(
                username='admin',
                email='admin@tutoring.com',
                role='admin'
            )
            admin_user.set_password('password321')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created")
            
            # NO TEACHERS OR STUDENTS CREATED - SYSTEM STARTS EMPTY
            
            # Count to verify empty state
            total_teachers = Teacher.query.count()
            total_students = Student.query.count()
            total_subjects = Subject.query.count()
            total_grades = Grade.query.count()
            
            print("\n" + "="*50)
            print("✅ DATABASE INITIALIZED SUCCESSFULLY!")
            print("="*50)
            print("\n📋 LOGIN CREDENTIALS:")
            print("👑 ADMIN: admin / password321")
            print("\n📝 SYSTEM STATUS:")
            print(f"   - Teachers: {total_teachers}")
            print(f"   - Students: {total_students}") 
            print(f"   - Subjects: {total_subjects}")
            print(f"   - Grades: {total_grades}")
            print("\n🚀 Upload a CSV file to populate the system with data")
            print("   Start the application with: python app.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_sample_data()
