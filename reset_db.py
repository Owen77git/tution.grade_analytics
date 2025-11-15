# reset_db.py - Reset database and optionally import sample data
from app import app, db
from models import User, Teacher, Student, Subject, Grade, SystemLog, Recommendation
import os

def reset_database(import_sample_data=True, import_csv_data=False):
    with app.app_context():
        try:
            print("🔄 Resetting database...")
            
            # Clear all data (in correct order to avoid foreign key constraints)
            print("🗑️  Clearing SystemLogs...")
            SystemLog.query.delete()
            
            print("🗑️  Clearing Recommendations...")
            Recommendation.query.delete()
            
            print("🗑️  Clearing Grades...")
            Grade.query.delete()
            
            print("🗑️  Clearing Students...")
            Student.query.delete()
            
            print("🗑️
