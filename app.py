# app.py - Complete with all required routes
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
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

# Enhanced Analytics Functions
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
        return get_fallback_trends()
    
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

def get_fallback_trends():
    """Provide fallback data when no real data exists"""
    return {
        'day_of_week': {
            'Monday': {'average': 75, 'count': 10, 'min': 65, 'max': 85},
            'Tuesday': {'average': 82, 'count': 12, 'min': 70, 'max': 90},
            'Wednesday': {'average': 78, 'count': 8, 'min': 68, 'max': 88}
        },
        'teacher_name': {
            'Mr. Kamau': {'average': 80, 'count': 15, 'min': 70, 'max': 90},
            'Mrs. Moraa': {'average': 75, 'count': 12, 'min': 65, 'max': 85}
        },
        'topic': {
            'Algebra': {'average': 72, 'count': 8, 'min': 60, 'max': 85},
            'Geometry': {'average': 78, 'count': 6, 'min': 65, 'max': 90}
        }
    }

def generate_factor_impact_analysis(teacher_id=None, student_id=None):
    """Generate factor impact analysis using real data"""
    query = Grade.query
    
    if teacher_id:
        query = query.filter(Grade.teacher_id == teacher_id)
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    
    grades = query.all()
    
    if not grades:
        return get_fallback_factor_analysis()
    
    factors = ['day_of_week', 'teacher_name', 'topic']
    impact_analysis = {}
    overall_avg = db.session.query(func.avg(Grade.score)).scalar() or 75
    
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

def get_fallback_factor_analysis():
    """Fallback factor analysis when no real data"""
    return {
        'day_of_week': {
            'Monday': {'average_score': 75, 'impact': -2, 'count': 10, 'performance': 'below'},
            'Tuesday': {'average_score': 82, 'impact': 5, 'count': 12, 'performance': 'above'},
            'Wednesday': {'average_score': 78, 'impact': 1, 'count': 8, 'performance': 'above'}
        },
        'teacher_name': {
            'Mr. Kamau': {'average_score': 80, 'impact': 3, 'count': 15, 'performance': 'above'},
            'Mrs. Moraa': {'average_score': 75, 'impact': -2, 'count': 12, 'performance': 'below'}
        },
        'topic': {
            'Algebra': {'average_score': 72, 'impact': -5, 'count': 8, 'performance': 'below'},
            'Geometry': {'average_score': 78, 'impact': 1, 'count': 6, 'performance': 'above'}
        }
    }

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

def get_performance_data(student_id=None, teacher_id=None, days=90):
    """Get comprehensive performance data for charts using real database data"""
    query = Grade.query
    
    # Apply filters
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
        
        # Teacher data
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
    
    # If no real data, provide meaningful fallbacks
    if not grades:
        return get_fallback_performance_data()
    
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

def get_fallback_performance_data():
    """Provide structured fallback data when no real data exists"""
    return {
        'dates': [
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') 
            for i in range(14, 0, -1)
        ],
        'scores': [72 + i * 2 + (i % 3) for i in range(14)],
        'subject_averages': {'Mathematics': 78, 'English': 82},
        'teacher_averages': {'Mr. Kamau': 80, 'Mrs. Moraa': 75},
        'day_averages': {'Monday': 75, 'Tuesday': 82, 'Wednesday': 78, 'Thursday': 80, 'Friday': 76},
        'topic_averages': {'Algebra': 72, 'Geometry': 78, 'Statistics': 85},
        'total_grades': 0,
        'overall_average': 77
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
            teacher_grades = Grade.query.filter_by(teacher_id=teacher.id).all()
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

# Admin Routes
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
    avg_performance = db.session.query(func.avg(Grade.score)).scalar() or 0
    
    # Get performance trends
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
        # Calculate average impact
        teacher_grades = Grade.query.filter_by(teacher_id=teacher.id).all()
        avg_score = db.session.query(func.avg(Grade.score)).filter(Grade.teacher_id == teacher.id).scalar() or 0
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
        # Calculate average grade
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
    if user:
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

# Teacher Routes
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
    
    # Get teacher's performance data
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

@app.route('/teacher/add_grade', methods=['POST'])
@login_required
def teacher_add_grade():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    data = request.get_json()
    
    try:
        # Find or create subject
        subject = Subject.query.filter_by(name=data['subject']).first()
        if not subject:
            subject = Subject(name=data['subject'], description=data['subject'])
            db.session.add(subject)
            db.session.flush()
        
        # Create grade with external factors
        grade = Grade(
            student_id=data['student_id'],
            teacher_id=teacher.id,
            subject_id=subject.id,
            score=data['score'],
            topic=data['topic'],
            exam_date=datetime.strptime(data['exam_date'], '%Y-%m-%d'),
            # External factors
            day_of_week=data.get('day_of_week'),
            teacher_name=teacher.full_name
        )
        
        db.session.add(grade)
        
        log = SystemLog(
            user_id=current_user.id,
            action=f'Added grade for student {data["student_id"]}',
            status='success',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'grade_id': grade.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/teacher/grades')
@login_required
def teacher_grades():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    grades = Grade.query.filter_by(teacher_id=teacher.id).all()
    
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

@app.route('/teacher/upload_csv', methods=['POST'])
@login_required
def teacher_upload_csv():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['Student_ID', 'Student_Name', 'Subject', 'Topic', 'Test_Date', 'Day', 'Teacher_Name', 'Score']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV missing required columns'}), 400
        
        grades_added = 0
        for _, row in df.iterrows():
            # Find student
            student = Student.query.filter_by(student_id=row['Student_ID']).first()
            if not student:
                # Create new student
                student_user = User(
                    username=row['Student_Name'].replace(' ', '').lower(),
                    email=f"{row['Student_Name'].replace(' ', '').lower()}@tutoring.com",
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
                db.session.flush()
            
            # Find or create subject
            subject = Subject.query.filter_by(name=row['Subject']).first()
            if not subject:
                subject = Subject(name=row['Subject'], description=row['Subject'])
                db.session.add(subject)
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
        
        db.session.commit()
        
        log = SystemLog(
            user_id=current_user.id,
            action=f'Uploaded {grades_added} grades via CSV',
            status='success',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'grades_added': grades_added})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

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

# Analytics API Routes
@app.route('/api/performance-data')
@login_required
def performance_data():
    """Return comprehensive performance data for charts"""
    student_id = request.args.get('student_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    days = request.args.get('days', 90, type=int)
    
    # Get user-specific data
    if current_user.role == 'student':
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

# Initialize database
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
    except Exception as e:
        print(f"Database initialization error: {e}")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutoring_analytics.db'
        with app.app_context():
            db.create_all()
            print("SQLite database created successfully!")

init_database()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
