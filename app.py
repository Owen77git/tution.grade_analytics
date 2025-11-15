# app.py - Complete Flask application with all routes
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Teacher, Student, Subject, Grade, SystemLog, Recommendation
from config import config
import json
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np
import io
import os
from collections import defaultdict
import secrets
import glob

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # NEW FUNCTION: Completely replace all data from CSV - FIXED TO NOT CREATE USERS AUTOMATICALLY
    def replace_all_data_with_csv(csv_file_path):
        """Completely replace ALL system data with data from CSV file - FIXED: Only creates from CSV"""
        try:
            print("🔄 Starting complete data replacement from CSV...")
            
            # Count existing data before deletion
            total_grades_before = Grade.query.count()
            total_students_before = Student.query.count()
            total_subjects_before = Subject.query.count()
            total_teachers_before = Teacher.query.count()
            
            print(f"📊 Before replacement - Grades: {total_grades_before}, Students: {total_students_before}, Subjects: {total_subjects_before}, Teachers: {total_teachers_before}")
            
            # DELETE ALL DATA (in correct order to avoid foreign key constraints)
            print("🗑️  Deleting all existing data...")
            
            # Delete grades first
            deleted_grades = Grade.query.delete()
            print(f"🗑️  Deleted {deleted_grades} grades")
            
            # Delete ALL students (including those linked to users except admin)
            students_to_delete = Student.query.filter(Student.user_id != 1).delete()
            print(f"🗑️  Deleted {students_to_delete} students")
            
            # Delete subjects
            subjects_to_delete = Subject.query.delete()
            print(f"🗑️  Deleted {subjects_to_delete} subjects")
            
            # Delete ALL teachers (including those linked to users except admin)
            teachers_to_delete = Teacher.query.filter(Teacher.user_id != 1).delete()
            print(f"🗑️  Deleted {teachers_to_delete} teachers")
            
            # Delete user accounts that are not admin
            users_to_delete = User.query.filter(User.id != 1, User.role.in_(['teacher', 'student'])).delete()
            print(f"🗑️  Deleted {users_to_delete} user accounts")
            
            db.session.commit()
            
            # Now process the new CSV file
            print(f"📖 Processing new CSV file: {csv_file_path}")
            
            df = pd.read_csv(csv_file_path)
            
            # Validate required columns
            required_columns = ['Student_ID', 'Student_Name', 'Subject', 'Topic', 'Test_Date', 'Day', 'Teacher_Name', 'Score']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV missing required columns. Required: {required_columns}")
            
            grades_added = 0
            students_created = 0
            subjects_created = 0
            teachers_created = 0
            
            # Track unique entities to avoid duplicates
            processed_students = {}
            processed_subjects = {}
            processed_teachers = {}
            
            for _, row in df.iterrows():
                # Process teacher - ONLY CREATE FROM CSV
                teacher_name = row['Teacher_Name']
                if teacher_name not in processed_teachers:
                    teacher = Teacher.query.filter_by(full_name=teacher_name).first()
                    if not teacher:
                        # Create new teacher user
                        teacher_username = teacher_name.replace(' ', '').replace('.', '').replace(',', '').lower()
                        # Ensure username is unique
                        base_username = teacher_username
                        counter = 1
                        while User.query.filter_by(username=teacher_username).first():
                            teacher_username = f"{base_username}{counter}"
                            counter += 1
                        
                        teacher_user = User(
                            username=teacher_username,
                            email=f"{teacher_username}@tutoring.com",
                            role='teacher'
                        )
                        teacher_user.set_password('password321')
                        db.session.add(teacher_user)
                        db.session.flush()
                        
                        teacher = Teacher(
                            user_id=teacher_user.id,
                            full_name=teacher_name,
                            subjects=row['Subject']
                        )
                        db.session.add(teacher)
                        teachers_created += 1
                        db.session.flush()
                    
                    processed_teachers[teacher_name] = teacher
                
                # Process student - ONLY CREATE FROM CSV
                student_id = row['Student_ID']
                if student_id not in processed_students:
                    student = Student.query.filter_by(student_id=student_id).first()
                    if not student:
                        # Create new student user
                        username = row['Student_Name'].replace(' ', '').replace('.', '').replace(',', '').lower()
                        # Ensure username is unique
                        base_username = username
                        counter = 1
                        while User.query.filter_by(username=username).first():
                            username = f"{base_username}{counter}"
                            counter += 1
                        
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
                            student_id=student_id,
                            full_name=row['Student_Name'],
                            grade_level='Form 4'
                        )
                        db.session.add(student)
                        students_created += 1
                        db.session.flush()
                    
                    processed_students[student_id] = student
                
                # Process subject - ONLY CREATE FROM CSV
                subject_name = row['Subject']
                if subject_name not in processed_subjects:
                    subject = Subject.query.filter_by(name=subject_name).first()
                    if not subject:
                        subject = Subject(name=subject_name, description=subject_name)
                        db.session.add(subject)
                        subjects_created += 1
                        db.session.flush()
                    
                    processed_subjects[subject_name] = subject
                
                # Create grade
                grade = Grade(
                    student_id=processed_students[student_id].id,
                    teacher_id=processed_teachers[teacher_name].id,
                    subject_id=processed_subjects[subject_name].id,
                    score=float(row['Score']),
                    topic=row['Topic'],
                    exam_date=datetime.strptime(row['Test_Date'], '%Y-%m-%d'),
                    day_of_week=row['Day'],
                    teacher_name=teacher_name
                )
                db.session.add(grade)
                grades_added += 1
            
            db.session.commit()
            
            total_grades_after = Grade.query.count()
            total_students_after = Student.query.count()
            total_subjects_after = Subject.query.count()
            total_teachers_after = Teacher.query.count()
            
            print(f"📊 After replacement - Grades: {total_grades_after}, Students: {total_students_after}, Subjects: {total_subjects_after}, Teachers: {total_teachers_after}")
            print(f"✅ Added - Grades: {grades_added}, Students: {students_created}, Subjects: {subjects_created}, Teachers: {teachers_created}")
            print("✅ Data replacement completed successfully!")
            
            return {
                'success': True,
                'grades_added': grades_added,
                'students_created': students_created,
                'subjects_created': subjects_created,
                'teachers_created': teachers_created,
                'total_grades': total_grades_after,
                'total_students': total_students_after,
                'total_subjects': total_subjects_after,
                'total_teachers': total_teachers_after
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during data replacement: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # UPDATED FUNCTION: Refresh all data from teacher CSVs - FIXED TO NOT CREATE SAMPLE DATA
    def refresh_all_teacher_data():
        """Clear all grade data and re-import from all teacher CSV files - FIXED: No sample data"""
        try:
            print("🔄 Starting complete data refresh...")
            
            # Count existing data before deletion
            total_grades_before = Grade.query.count()
            total_students_before = Student.query.count()
            total_subjects_before = Subject.query.count()
            
            print(f"📊 Before refresh - Grades: {total_grades_before}, Students: {total_students_before}, Subjects: {total_subjects_before}")
            
            # Delete ALL grades from the database
            deleted_grades = Grade.query.delete()
            print(f"🗑️  Deleted {deleted_grades} grades from database")
            
            # Delete students (except admin)
            students_to_delete = Student.query.filter(Student.user_id != 1).delete()
            print(f"🗑️  Deleted {students_to_delete} students")
            
            # Delete subjects not linked to any grades (they'll be recreated)
            subjects_to_delete = Subject.query.filter(~Subject.id.in_(db.session.query(Grade.subject_id))).delete()
            print(f"🗑️  Deleted {subjects_to_delete} orphaned subjects")
            
            # Delete teachers (except admin)
            teachers_to_delete = Teacher.query.filter(Teacher.user_id != 1).delete()
            print(f"🗑️  Deleted {teachers_to_delete} teachers")
            
            # Delete user accounts that are not admin
            users_to_delete = User.query.filter(User.id != 1, User.role.in_(['teacher', 'student'])).delete()
            print(f"🗑️  Deleted {users_to_delete} user accounts")
            
            db.session.commit()
            
            # Now process CSV files from uploads directory
            csv_files = glob.glob('uploads/*.csv') + glob.glob('static/*.csv')
            
            total_grades_added = 0
            total_students_created = 0
            total_subjects_created = 0
            
            print(f"📂 Processing {len(csv_files)} CSV files...")
            
            for csv_file in csv_files:
                try:
                    print(f"   📖 Processing CSV file: {csv_file}")
                    # For refresh, we need to process each CSV and create teachers/students
                    df = pd.read_csv(csv_file)
                    
                    # Validate required columns
                    required_columns = ['Student_ID', 'Student_Name', 'Subject', 'Topic', 'Test_Date', 'Day', 'Teacher_Name', 'Score']
                    if not all(col in df.columns for col in required_columns):
                        print(f"   ⚠️  CSV missing required columns: {csv_file}")
                        continue
                    
                    grades_added = 0
                    students_created = 0
                    subjects_created = 0
                    
                    # Process each row
                    for _, row in df.iterrows():
                        # Find or create teacher
                        teacher = Teacher.query.filter_by(full_name=row['Teacher_Name']).first()
                        if not teacher:
                            # Create teacher user
                            teacher_username = row['Teacher_Name'].replace(' ', '').replace('.', '').replace(',', '').lower()
                            base_username = teacher_username
                            counter = 1
                            while User.query.filter_by(username=teacher_username).first():
                                teacher_username = f"{base_username}{counter}"
                                counter += 1
                            
                            teacher_user = User(
                                username=teacher_username,
                                email=f"{teacher_username}@tutoring.com",
                                role='teacher'
                            )
                            teacher_user.set_password('password321')
                            db.session.add(teacher_user)
                            db.session.flush()
                            
                            teacher = Teacher(
                                user_id=teacher_user.id,
                                full_name=row['Teacher_Name'],
                                subjects=row['Subject']
                            )
                            db.session.add(teacher)
                            db.session.flush()
                        
                        # Find or create student
                        student = Student.query.filter_by(student_id=row['Student_ID']).first()
                        if not student:
                            # Create student user
                            username = row['Student_Name'].replace(' ', '').replace('.', '').replace(',', '').lower()
                            base_username = username
                            counter = 1
                            while User.query.filter_by(username=username).first():
                                username = f"{base_username}{counter}"
                                counter += 1
                            
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
                    
                    total_grades_added += grades_added
                    total_students_created += students_created
                    total_subjects_created += subjects_created
                    print(f"   ✅ Added {grades_added} grades from {csv_file}")
                    
                except Exception as e:
                    print(f"   ❌ Error processing {csv_file}: {e}")
                    continue
            
            # NO SAMPLE DATA CREATION - Only use actual CSV files
            
            db.session.commit()
            
            total_grades_after = Grade.query.count()
            
            print(f"📊 After refresh - Grades: {total_grades_after}, New students: {total_students_created}, New subjects: {total_subjects_created}")
            print("✅ Data refresh completed successfully!")
            
            return {
                'success': True,
                'grades_added': total_grades_added,
                'students_created': total_students_created,
                'subjects_created': total_subjects_created,
                'total_grades': total_grades_after
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during data refresh: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # UPDATED FUNCTION: Return zero data when no real data exists
    def get_zero_performance_data():
        """Return performance data with zeros when no real data exists"""
        return {
            'dates': ['2024-01-01', '2024-01-08', '2024-01-15', '2024-01-22'],
            'scores': [0, 0, 0, 0],
            'subject_averages': {'No Data': 0},
            'teacher_averages': {'No Data': 0},
            'day_averages': {'No Data': 0},
            'topic_averages': {'No Data': 0},
            'total_grades': 0,
            'overall_average': 0
        }

    def get_empty_performance_data():
        """Return empty performance data when no real data exists"""
        return get_zero_performance_data()

    def get_fallback_trends():
        """Provide empty fallback data when no real data exists"""
        return {
            'day_of_week': {},
            'teacher_name': {},
            'topic': {}
        }

    def get_fallback_factor_analysis():
        """Empty factor analysis when no real data"""
        return {
            'day_of_week': {},
            'teacher_name': {},
            'topic': {}
        }

    # Enhanced Analytics Functions - FIXED TO READ ALL TEACHER DATA
    def calculate_performance_trends(student_id=None, teacher_id=None, days=30):
        """Calculate performance trends based on external factors with real data"""
        query = Grade.query
        
        if student_id:
            query = query.filter(Grade.student_id == student_id)
        if teacher_id:
            query = query.filter(Grade.teacher_id == teacher_id)
        
        # Get recent grades
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Grade.exam_date >= cutoff_date)
        
        grades = query.order_by(Grade.exam_date).all()
        
        if not grades:
            return get_fallback_trends()  # Now returns empty trends
        
        trends = {}
        factors = ['day_of_week', 'teacher_name', 'topic']
        
        for factor in factors:
            factor_values = {}
            for grade in grades:
                factor_value = getattr(grade, factor)
                if factor_value:
                    if factor_value not in factor_values:
                        factor_values[factor_value] = []
                    factor_values[factor_value].append(grade.score)
            
            factor_avgs = {}
            for value, scores in factor_values.items():
                if len(scores) > 0:
                    factor_avgs[value] = {
                        'average': round(sum(scores) / len(scores), 2),
                        'count': len(scores),
                        'min': min(scores),
                        'max': max(scores)
                    }
            
            trends[factor] = factor_avgs
        
        return trends

    def generate_factor_impact_analysis(teacher_id=None, student_id=None):
        """Generate factor impact analysis using real data"""
        query = Grade.query
        
        if teacher_id:
            query = query.filter(Grade.teacher_id == teacher_id)
        if student_id:
            query = query.filter(Grade.student_id == student_id)
        
        grades = query.all()
        
        if not grades:
            return get_fallback_factor_analysis()  # Now returns empty analysis
        
        factors = ['day_of_week', 'teacher_name', 'topic']
        impact_analysis = {}
        overall_avg = db.session.query(func.avg(Grade.score)).scalar() or 0
        
        for factor in factors:
            factor_impact = {}
            # Get unique values for this factor from actual grades
            values_query = db.session.query(getattr(Grade, factor)).distinct().all()
            factor_values = [v[0] for v in values_query if v[0] is not None]
            
            for value in factor_values:
                value_grades = [g for g in grades if getattr(g, factor) == value]
                if value_grades:
                    avg_score = sum(g.score for g in value_grades) / len(value_grades)
                    count = len(value_grades)
                    
                    impact = avg_score - overall_avg
                    factor_impact[value] = {
                        'average_score': round(avg_score, 2),
                        'impact': round(impact, 2),
                        'count': count,
                        'performance': 'above' if impact > 0 else 'below'
                    }
            
            impact_analysis[factor] = factor_impact
        
        return impact_analysis

    def generate_intelligent_recommendations(student_id=None, teacher_id=None):
        """Generate intelligent recommendations based on actual performance data"""
        trends = calculate_performance_trends(student_id, teacher_id)
        recommendations = []
        
        if current_user.is_authenticated:
            if current_user.role == 'student' and student_id:
                # Student-specific recommendations based on actual data
                student_grades = Grade.query.filter_by(student_id=student_id).all()
                
                if student_grades:
                    # Day optimization based on actual performance
                    day_trends = trends.get('day_of_week', {})
                    if day_trends:
                        best_day = max(day_trends.items(), key=lambda x: x[1]['average'])
                        recommendations.append({
                            'type': 'day_optimization',
                            'text': f'Your performance is {best_day[1]["average"]}% on {best_day[0]} - highest among all days',
                            'impact_score': 8.0,
                            'action': f'Schedule important study sessions on {best_day[0]}',
                            'confidence': 'high'
                        })
                    
                    # Teacher optimization
                    teacher_trends = trends.get('teacher_name', {})
                    if teacher_trends:
                        best_teacher = max(teacher_trends.items(), key=lambda x: x[1]['average'])
                        recommendations.append({
                            'type': 'teacher_optimization',
                            'text': f'You achieve {best_teacher[1]["average"]}% with {best_teacher[0]}',
                            'impact_score': 12.0,
                            'action': f'Focus on sessions with {best_teacher[0]} for difficult topics',
                            'confidence': 'medium'
                        })
                    
                    # Topic analysis
                    topic_trends = trends.get('topic', {})
                    if topic_trends:
                        strong_topic = max(topic_trends.items(), key=lambda x: x[1]['average'])
                        weak_topic = min(topic_trends.items(), key=lambda x: x[1]['average'])
                        
                        recommendations.append({
                            'type': 'strength_utilization',
                            'text': f'Excellent performance in {strong_topic[0]} ({strong_topic[1]["average"]}%)',
                            'impact_score': 10.0,
                            'action': f'Use your strength in {strong_topic[0]} to build confidence',
                            'confidence': 'high'
                        })
                        
                        recommendations.append({
                            'type': 'improvement_area',
                            'text': f'Need improvement in {weak_topic[0]} ({weak_topic[1]["average"]}%)',
                            'impact_score': 15.0,
                            'action': f'Allocate extra study time for {weak_topic[0]}',
                            'confidence': 'high'
                        })
            
            elif current_user.role == 'teacher' and teacher_id:
                # Teacher-specific recommendations
                teacher_grades = Grade.query.filter_by(teacher_id=teacher_id).all()
                
                if teacher_grades:
                    # Topic difficulty analysis
                    topic_trends = trends.get('topic', {})
                    if topic_trends:
                        challenging_topic = min(topic_trends.items(), key=lambda x: x[1]['average'])
                        recommendations.append({
                            'type': 'teaching_focus',
                            'text': f'Students struggle with {challenging_topic[0]} (average: {challenging_topic[1]["average"]}%)',
                            'impact_score': 15.0,
                            'action': f'Provide additional resources and practice for {challenging_topic[0]}',
                            'confidence': 'high'
                        })
                    
                    # Day performance analysis
                    day_trends = trends.get('day_of_week', {})
                    if day_trends:
                        best_day = max(day_trends.items(), key=lambda x: x[1]['average'])
                        recommendations.append({
                            'type': 'scheduling_optimization',
                            'text': f'Best student performance on {best_day[0]} ({best_day[1]["average"]}%)',
                            'impact_score': 8.0,
                            'action': f'Schedule important topics and assessments on {best_day[0]}',
                            'confidence': 'medium'
                        })
        
        # Add general recommendations if we don't have enough specific ones
        if len(recommendations) < 3:
            general_recommendations = [
                {
                    'type': 'consistent_practice',
                    'text': 'Regular practice improves retention by 25% based on class data',
                    'impact_score': 15.0,
                    'action': 'Implement weekly review sessions for all topics',
                    'confidence': 'high'
                },
                {
                    'type': 'assessment_strategy',
                    'text': 'Frequent low-stakes assessments improve learning outcomes',
                    'impact_score': 12.0,
                    'action': 'Schedule weekly practice tests for ongoing evaluation',
                    'confidence': 'medium'
                }
            ]
            recommendations.extend(general_recommendations)
        
        return recommendations[:5]  # Return top 5 recommendations

    # UPDATED FUNCTION: Get performance data - FIXED TO RETURN 0 WHEN NO DATA
    def get_performance_data(student_id=None, teacher_id=None, days=90):
        """Get comprehensive performance data for charts using real database data - FIXED TO RETURN 0 WHEN NO DATA"""
        query = Grade.query
        
        # Apply filters - ADMIN SHOULD SEE ALL DATA
        if current_user.is_authenticated and current_user.role == 'admin':
            # Admin sees all data regardless of filters
            pass
        else:
            if student_id:
                query = query.filter(Grade.student_id == student_id)
            if teacher_id:
                query = query.filter(Grade.teacher_id == teacher_id)
        
        # Get recent data
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        grades = query.filter(Grade.exam_date >= cutoff_date).order_by(Grade.exam_date).all()
        
        # If no grades found, try without date filter
        if not grades:
            grades = query.order_by(Grade.exam_date).all()
        
        # If STILL no grades, return data with zeros (not empty arrays)
        if not grades:
            return get_zero_performance_data()
        
        dates = []
        scores = []
        subjects = defaultdict(list)
        teachers = defaultdict(list)
        days_data = defaultdict(list)
        topics = defaultdict(list)
        
        for grade in grades:
            dates.append(grade.exam_date.strftime('%Y-%m-%d'))
            scores.append(grade.score)
            
            # Subject data
            subjects[grade.subject.name].append(grade.score)
            
            # Teacher data - FIXED: Use teacher_name from CSV
            teachers[grade.teacher_name].append(grade.score)
            
            # Day data
            if grade.day_of_week:
                days_data[grade.day_of_week].append(grade.score)
            
            # Topic data
            topics[grade.topic].append(grade.score)
        
        # Calculate averages
        def calculate_average(data_dict):
            result = {}
            for key, scores_list in data_dict.items():
                if scores_list:
                    result[key] = round(sum(scores_list) / len(scores_list), 1)
            return result
        
        return {
            'dates': dates[-20:],  # Last 20 data points
            'scores': scores[-20:],
            'subject_averages': calculate_average(subjects),
            'teacher_averages': calculate_average(teachers),
            'day_averages': calculate_average(days_data),
            'topic_averages': calculate_average(topics),
            'total_grades': len(grades),
            'overall_average': round(sum(scores) / len(scores), 1) if scores else 0
        }

    # Excel Export Function
    def generate_excel_report(report_type, filters=None):
        """Generate Excel reports based on type and filters"""
        output = io.BytesIO()
        
        if report_type == 'performance_summary':
            # Performance summary report
            grades = Grade.query.all()
            
            data = []
            for grade in grades:
                data.append({
                    'Student ID': grade.student.student_id,
                    'Student Name': grade.student.full_name,
                    'Subject': grade.subject.name,
                    'Topic': grade.topic,
                    'Score': grade.score,
                    'Teacher': grade.teacher_name,
                    'Day of Week': grade.day_of_week,
                    'Exam Date': grade.exam_date.strftime('%Y-%m-%d')
                })
            
            df = pd.DataFrame(data)
        
        elif report_type == 'teacher_analysis':
            # Teacher analysis report
            teachers = Teacher.query.all()
            data = []
            
            for teacher in teachers:
                teacher_grades = Grade.query.filter_by(teacher_name=teacher.full_name).all()
                if teacher_grades:
                    avg_score = sum(g.score for g in teacher_grades) / len(teacher_grades)
                    data.append({
                        'Teacher Name': teacher.full_name,
                        'Subjects': teacher.subjects,
                        'Total Students': len(set(g.student_id for g in teacher_grades)),
                        'Total Tests': len(teacher_grades),
                        'Average Score': round(avg_score, 1),
                        'Performance Impact': round(avg_score - 75, 1)  # Baseline 75
                    })
            
            df = pd.DataFrame(data)
        
        elif report_type == 'student_progress':
            # Student progress report
            students = Student.query.all()
            data = []
            
            for student in students:
                student_grades = Grade.query.filter_by(student_id=student.id).all()
                if student_grades:
                    avg_score = sum(g.score for g in student_grades) / len(student_grades)
                    recent_grades = sorted(student_grades, key=lambda x: x.exam_date, reverse=True)[:5]
                    recent_avg = sum(g.score for g in recent_grades) / len(recent_grades) if recent_grades else 0
                    
                    data.append({
                        'Student ID': student.student_id,
                        'Student Name': student.full_name,
                        'Grade Level': student.grade_level,
                        'Total Tests': len(student_grades),
                        'Overall Average': round(avg_score, 1),
                        'Recent Average (Last 5)': round(recent_avg, 1),
                        'Trend': 'Improving' if recent_avg > avg_score else 'Stable' if recent_avg == avg_score else 'Needs Attention'
                    })
            
            df = pd.DataFrame(data)
        
        else:
            # Default comprehensive report
            grades = Grade.query.all()
            data = []
            for grade in grades:
                data.append({
                    'Student ID': grade.student.student_id,
                    'Student Name': grade.student.full_name,
                    'Subject': grade.subject.name,
                    'Topic': grade.topic,
                    'Score': grade.score,
                    'Grade': get_grade_letter(grade.score),
                    'Teacher': grade.teacher_name,
                    'Day': grade.day_of_week,
                    'Date': grade.exam_date.strftime('%Y-%m-%d')
                })
            
            df = pd.DataFrame(data)
        
        # Create Excel file
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Records', 'Date Generated', 'Report Type'],
                'Value': [len(df), datetime.utcnow().strftime('%Y-%m-%d %H:%M'), report_type]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        return output

    def get_grade_letter(score):
        """Convert score to letter grade"""
        if score >= 90: return 'A'
        if score >= 80: return 'B'
        if score >= 70: return 'C'
        if score >= 60: return 'D'
        return 'F'

    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif current_user.role == 'student':
                return redirect(url_for('student_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username, is_active=True).first()
            
            if user and user.check_password(password):
                login_user(user)
                
                log = SystemLog(
                    user_id=user.id,
                    action='login',
                    status='success',
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                log = SystemLog(
                    action='login',
                    status='failed',
                    details=f'Failed login attempt for username: {username}',
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # NEW ROUTE: Admin data refresh
    @app.route('/admin/refresh-data', methods=['POST'])
    @login_required
    def admin_refresh_data():
        """Admin endpoint to refresh all data from teacher CSVs"""
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        try:
            result = refresh_all_teacher_data()
            
            if result['success']:
                log = SystemLog(
                    user_id=current_user.id,
                    action='Refreshed all system data from teacher CSVs',
                    status='success',
                    details=f"Added {result['grades_added']} grades, {result['students_created']} students, {result['subjects_created']} subjects",
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f"Data refresh completed! Added {result['grades_added']} grades.",
                    'stats': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Error refreshing data: {str(e)}'
            })

    # Admin Routes - FIXED TO SHOW ALL DATA
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        
        total_students = Student.query.count()
        total_teachers = Teacher.query.count()
        total_subjects = Subject.query.count()
        recent_activity = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
        
        # FIXED: Get ALL performance data, not filtered by teacher
        avg_performance = db.session.query(func.avg(Grade.score)).scalar() or 0
        
        # Get performance trends - FIXED: No filters for admin
        performance_data = get_performance_data()

        return render_template('admin.html',
                            total_students=total_students,
                            total_teachers=total_teachers,
                            total_subjects=total_subjects,
                            avg_performance=round(avg_performance, 1),
                            recent_activity=recent_activity,
                            performance_data=performance_data)

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        users = User.query.all()
        users_data = []
        
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.strftime('%Y-%m-%d'),
                'is_active': user.is_active
            }
            
            if user.role == 'teacher' and user.teacher_profile:
                user_data.update({
                    'full_name': user.teacher_profile.full_name,
                    'subjects': user.teacher_profile.subjects,
                    'status': user.teacher_profile.status
                })
            elif user.role == 'student' and user.student_profile:
                user_data.update({
                    'full_name': user.student_profile.full_name,
                    'student_id': user.student_profile.student_id,
                    'grade_level': user.student_profile.grade_level
                })
            
            users_data.append(user_data)
        
        return jsonify(users_data)

    @app.route('/admin/teachers')
    @login_required
    def admin_teachers():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        teachers = Teacher.query.all()
        teachers_data = []
        
        for teacher in teachers:
            # Calculate average impact - FIXED: Use teacher_name from grades
            teacher_grades = Grade.query.filter_by(teacher_name=teacher.full_name).all()
            avg_score = db.session.query(func.avg(Grade.score)).filter(Grade.teacher_name == teacher.full_name).scalar() or 0
            overall_avg = db.session.query(func.avg(Grade.score)).scalar() or 0
            impact = avg_score - overall_avg
            
            teachers_data.append({
                'id': teacher.user.id,
                'full_name': teacher.full_name,
                'username': teacher.user.username,
                'email': teacher.user.email,
                'subjects': teacher.subjects,
                'status': teacher.status,
                'impact': round(impact, 1),
                'student_count': len(set([grade.student_id for grade in teacher_grades]))
            })
        
        return jsonify(teachers_data)

    @app.route('/admin/students')
    @login_required
    def admin_students():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        students = Student.query.all()
        students_data = []
        
        for student in students:
        
            # Calculate average grade - FIXED: Use all grades for student
            avg_grade = db.session.query(func.avg(Grade.score)).filter(Grade.student_id == student.id).scalar() or 0
            
            students_data.append({
                'id': student.user.id,
                'full_name': student.full_name,
                'username': student.user.username,
                'email': student.user.email,
                'student_id': student.student_id,
                'grade_level': student.grade_level,
                'avg_grade': round(avg_grade, 1)
            })
        
        return jsonify(students_data)

    @app.route('/admin/add_user', methods=['POST'])
    @login_required
    def admin_add_user():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        try:
            # Check if username already exists
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 400
            
            # Create user
            new_user = User(
                username=data['username'],
                email=data['email'],
                role=data['role']
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.flush()  # Get the ID without committing
            
            # Create profile based on role
            if data['role'] == 'teacher':
                teacher = Teacher(
                    user_id=new_user.id,
                    full_name=data['full_name'],
                    subjects=data.get('subjects', '')
                )
                db.session.add(teacher)
            elif data['role'] == 'student':
                student = Student(
                    user_id=new_user.id,
                    full_name=data['full_name'],
                    student_id=data['student_id'],
                    grade_level=data.get('grade_level', '')
                )
                db.session.add(student)
            
            db.session.commit()
            
            log = SystemLog(
                user_id=current_user.id,
                action=f'Added {data["role"]} user: {data["username"]}',
                status='success',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': True, 'user_id': new_user.id})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
    @login_required
    def admin_delete_user(user_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if user and user.id != 1:  # Prevent deleting admin
            db.session.delete(user)
            db.session.commit()
            
            log = SystemLog(
                user_id=current_user.id,
                action=f'Deleted user: {user.username}',
                status='success',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': True})
        
        return jsonify({'error': 'User not found'}), 404

    # Teacher Routes - READ ONLY
    @app.route('/teacher')
    @login_required
    def teacher_dashboard():
        if current_user.role != 'teacher':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher profile not found.', 'error')
            return redirect(url_for('logout'))
        
        # Get teacher's performance data - ONLY for this teacher
        performance_data = get_performance_data(teacher_id=teacher.id)
        
        return render_template('teacher.html', teacher=teacher, performance_data=performance_data)

    @app.route('/teacher/students')
    @login_required
    def teacher_students():
        if current_user.role != 'teacher':
            return jsonify({'error': 'Access denied'}), 403
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        # Get unique students who have grades with this teacher
        student_ids = db.session.query(Grade.student_id).filter(Grade.teacher_id == teacher.id).distinct().all()
        students = Student.query.filter(Student.id.in_([s[0] for s in student_ids])).all()
        
        students_data = []
        for student in students:
            # Get student's average grade for this teacher's subjects
            avg_grade = db.session.query(func.avg(Grade.score)).filter(
                Grade.student_id == student.id,
                Grade.teacher_id == teacher.id
            ).scalar() or 0
            
            students_data.append({
                'id': student.id,
                'student_id': student.student_id,
                'full_name': student.full_name,
                'grade_level': student.grade_level,
                'avg_grade': round(avg_grade, 1)
            })
        
        return jsonify(students_data)

    @app.route('/teacher/grades')
    @login_required
    def teacher_grades():
        if current_user.role != 'teacher':
            return jsonify({'error': 'Access denied'}), 403
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        grades = Grade.query.filter_by(teacher_id=teacher.id).order_by(Grade.exam_date.desc()).all()
        
        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'student_name': grade.student.full_name,
                'student_id': grade.student.student_id,
                'subject': grade.subject.name,
                'score': grade.score,
                'topic': grade.topic,
                'exam_date': grade.exam_date.strftime('%Y-%m-%d'),
                'day_of_week': grade.day_of_week,
                'teacher_name': grade.teacher_name
            })
        
        return jsonify(grades_data)

    @app.route('/teacher/subjects')
    @login_required
    def teacher_subjects():
        if current_user.role != 'teacher':
            return jsonify({'error': 'Access denied'}), 403
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        # Get unique subjects taught by this teacher
        subject_ids = db.session.query(Grade.subject_id).filter(Grade.teacher_id == teacher.id).distinct().all()
        subjects = Subject.query.filter(Subject.id.in_([s[0] for s in subject_ids])).all()
        
        subjects_data = []
        for subject in subjects:
            # Get average score for this subject taught by this teacher
            avg_score = db.session.query(func.avg(Grade.score)).filter(
                Grade.subject_id == subject.id,
                Grade.teacher_id == teacher.id
            ).scalar() or 0
            
            subjects_data.append({
                'id': subject.id,
                'name': subject.name,
                'avg_score': round(avg_score, 1)
            })
        
        return jsonify(subjects_data)

    @app.route('/teacher/topics')
    @login_required
    def teacher_topics():
        if current_user.role != 'teacher':
            return jsonify({'error': 'Access denied'}), 403
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        # Get unique topics taught by this teacher
        topics = db.session.query(Grade.topic).filter(Grade.teacher_id == teacher.id).distinct().all()
        
        topics_data = []
        for topic in topics:
            if topic[0]:  # Ensure topic is not None
                # Get average score for this topic taught by this teacher
                avg_score = db.session.query(func.avg(Grade.score)).filter(
                    Grade.topic == topic[0],
                    Grade.teacher_id == teacher.id
                ).scalar() or 0
                
                # Count number of grades for this topic
                grade_count = db.session.query(func.count(Grade.id)).filter(
                    Grade.topic == topic[0],
                    Grade.teacher_id == teacher.id
                ).scalar() or 0
                
                topics_data.append({
                    'name': topic[0],
                    'avg_score': round(avg_score, 1),
                    'grade_count': grade_count
                })
        
        return jsonify(topics_data)

    # Student Routes
    @app.route('/student')
    @login_required
    def student_dashboard():
        if current_user.role != 'student':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Student profile not found.', 'error')
            return redirect(url_for('logout'))
        
        # Get student's performance data
        performance_data = get_performance_data(student_id=student.id)
        
        return render_template('student.html', student=student, performance_data=performance_data)

    @app.route('/student/grades')
    @login_required
    def student_grades():
        if current_user.role != 'student':
            return jsonify({'error': 'Access denied'}), 403
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        grades = Grade.query.filter_by(student_id=student.id).all()
        
        grades_data = []
        for grade in grades:
            grades_data.append({
                'subject': grade.subject.name,
                'score': grade.score,
                'topic': grade.topic,
                'exam_date': grade.exam_date.strftime('%Y-%m-%d'),
                'teacher': grade.teacher.full_name,
                'day_of_week': grade.day_of_week
            })
        
        return jsonify(grades_data)

    @app.route('/student/analytics')
    @login_required
    def student_analytics():
        if current_user.role != 'student':
            return jsonify({'error': 'Access denied'}), 403
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        recommendations = generate_intelligent_recommendations(student_id=student.id)
        
        return jsonify({
            'recommendations': recommendations,
            'performance_trends': calculate_performance_trends(student_id=student.id)
        })

    # UPDATED: Admin CSV Upload Route - COMPLETE DATA REPLACEMENT
    @app.route('/admin/upload-csv', methods=['POST'])
    @login_required
    def admin_upload_csv():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file'}), 400
        
        try:
            # Save the uploaded file temporarily
            temp_path = f"temp_{secrets.token_hex(8)}.csv"
            file.save(temp_path)
            
            # Process the CSV with complete data replacement
            result = replace_all_data_with_csv(temp_path)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            if result['success']:
                log = SystemLog(
                    user_id=current_user.id,
                    action=f'Admin completely replaced all system data with CSV upload',
                    status='success',
                    details=f"Added {result['grades_added']} grades, {result['students_created']} students, {result['subjects_created']} subjects, {result['teachers_created']} teachers",
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'grades_added': result['grades_added'],
                    'students_created': result['students_created'],
                    'subjects_created': result['subjects_created'],
                    'teachers_created': result['teachers_created'],
                    'message': f'Successfully replaced ALL system data with {result["grades_added"]} grades from CSV.'
                })
            else:
                return jsonify({'error': result['error']}), 400
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400

    # Admin Delete All Grades Route
    @app.route('/admin/delete-all-grades', methods=['DELETE'])
    @login_required
    def admin_delete_all_grades():
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        try:
            # Count grades before deletion
            grade_count = Grade.query.count()
            
            # Delete all grades from the system
            deleted_count = Grade.query.delete()
            
            # Also delete all students, teachers, and subjects (except admin)
            Student.query.filter(Student.user_id != 1).delete()
            Teacher.query.filter(Teacher.user_id != 1).delete()
            Subject.query.delete()
            
            # Delete user accounts that are not admin
            User.query.filter(User.id != 1, User.role.in_(['teacher', 'student'])).delete()
            
            log = SystemLog(
                user_id=current_user.id,
                action=f'Admin deleted all {deleted_count} grades and all user accounts from system',
                status='success',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'deleted_count': deleted_count,
                'message': f'Successfully deleted all {deleted_count} grades and all user accounts from the system.'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error deleting data: {str(e)}'}), 400

    # Analytics API Routes - FIXED FOR ADMIN
    @app.route('/api/performance-data')
    @login_required
    def performance_data():
        """Return comprehensive performance data for charts - FIXED FOR ADMIN"""
        student_id = request.args.get('student_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)
        days = request.args.get('days', 90, type=int)
        
        # Get user-specific data - ADMIN SHOULD SEE ALL DATA
        if current_user.role == 'admin':
            # Admin sees all data regardless of filters
            student_id = None
            teacher_id = None
        elif current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            student_id = student.id if student else None
        elif current_user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=current_user.id).first()
            teacher_id = teacher.id if teacher else None
        
        data = get_performance_data(student_id, teacher_id, days)
        return jsonify(data)

    @app.route('/api/factor-analysis')
    @login_required
    def factor_analysis():
        """Return factor impact analysis"""
        impact_analysis = generate_factor_impact_analysis()
        return jsonify(impact_analysis)

    @app.route('/api/performance-insights')
    @login_required
    def performance_insights():
        """Get performance insights and recommendations"""
        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            insights = generate_intelligent_recommendations(student_id=student.id if student else None)
        elif current_user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=current_user.id).first()
            insights = generate_intelligent_recommendations(teacher_id=teacher.id if teacher else None)
        else:
            # Admin gets system-wide recommendations
            insights = generate_intelligent_recommendations()
        
        return jsonify(insights)

    @app.route('/api/export-report')
    @login_required
    def export_report():
        """Export data as Excel report"""
        report_type = request.args.get('type', 'comprehensive')
        filename = f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx"
        
        excel_data = generate_excel_report(report_type)
        
        return send_file(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    @app.route('/api/system-logs')
    @login_required
    def get_system_logs():
        """Return system logs"""
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(50).all()
        logs_data = []
        
        for log in logs:
            user = User.query.get(log.user_id) if log.user_id else None
            logs_data.append({
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'user': user.username if user else 'System',
                'action': log.action,
                'status': log.status,
                'details': log.details,
                'ip_address': log.ip_address
            })
        
        return jsonify(logs_data)

    @app.route('/api/subjects')
    @login_required
    def get_subjects():
        """Return all subjects"""
        subjects = Subject.query.all()
        subjects_data = [{'id': s.id, 'name': s.name} for s in subjects]
        return jsonify(subjects_data)

    # Static file serving
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    # Sample CSV template download
    @app.route('/static/sample_grades.csv')
    def download_sample_csv():
        return send_from_directory('static', 'sample_grades.csv', as_attachment=True)

    # UPDATED: Initialize database - ONLY CREATE ADMIN
    def init_database():
        try:
            with app.app_context():
                db.create_all()
                
                # Create default admin user if not exists
                if not User.query.filter_by(username='admin').first():
                    admin_user = User(
                        username='admin',
                        email='admin@tutoring.com',
                        role='admin'
                    )
                    admin_user.set_password('password321')
                    db.session.add(admin_user)
                    db.session.commit()
                    
                    print("Database initialized successfully!")
                    print("Default admin account created:")
                    print("Username: admin")
                    print("Password: password321")
                    print("NO teachers or students created - system is empty until CSV upload")
        except Exception as e:
            print(f"Database initialization error: {e}")
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutoring_analytics.db'
            with app.app_context():
                db.create_all()
                print("SQLite database created successfully!")

    init_database()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
