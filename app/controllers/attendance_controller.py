from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models.models import Attendance, Student, Class, User, db
from datetime import datetime, timedelta
import calendar
from sqlalchemy.orm import joinedload

attendance_bp = Blueprint('attendance', __name__)

# View attendance records by class
@attendance_bp.route('/class/<int:class_id>')
@login_required
def class_attendance(class_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.options(joinedload(Student.user)).filter_by(class_id=class_id).all()
    
    # Get date parameters (default to today)
    date_str = request.args.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = datetime.now().date()
    
    # Get attendance records for the class on the specified date
    attendance_records = {}
    for student in students:
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            class_id=class_id,
            date=date
        ).first()
        
        attendance_records[student.id] = attendance.status if attendance else 'not_marked'
    
    return render_template('attendance/class_attendance.html',
                          class_obj=class_obj,
                          students=students,
                          date=date,
                          attendance_records=attendance_records)

# Mark attendance for a class
@attendance_bp.route('/mark/<int:class_id>', methods=['GET', 'POST'])
@login_required
def mark_attendance(class_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.options(joinedload(Student.user)).filter_by(class_id=class_id).all()
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Delete existing attendance records for this class and date
        for student in students:
            existing = Attendance.query.filter_by(
                student_id=student.id,
                class_id=class_id,
                date=date
            ).first()
            
            if existing:
                db.session.delete(existing)
        
        # Create new attendance records
        for student in students:
            status = request.form.get(f'status_{student.id}')
            
            attendance = Attendance(
                student_id=student.id,
                class_id=class_id,
                date=date,
                status=status,
                marked_by=current_user.id
            )
            
            db.session.add(attendance)
        
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('attendance.class_attendance', class_id=class_id, date=date_str))
    
    # Default to today's date
    date = datetime.now().date()
    
    # Check if attendance already marked
    attendance_records = {}
    for student in students:
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            class_id=class_id,
            date=date
        ).first()
        
        attendance_records[student.id] = attendance.status if attendance else 'not_marked'
    
    return render_template('attendance/mark_attendance.html',
                          class_obj=class_obj,
                          students=students,
                          date=date,
                          attendance_records=attendance_records)

# View student attendance
@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_attendance(student_id):
    # Check permissions
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        # Check if parent viewing their child's attendance
        if current_user.role == 'parent':
            # Logic to check if student is child of parent would go here
            pass
        else:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
    
    student = Student.query.options(joinedload(Student.user)).filter_by(user_id=student_id).first_or_404()
    user = student.user
    
    # Get month and year parameters
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get all days in the month
    num_days = calendar.monthrange(year, month)[1]
    days = [datetime(year, month, day).date() for day in range(1, num_days + 1)]
    
    # Get attendance records for the month
    attendance_records = {}
    for day in days:
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            date=day
        ).first()
        
        attendance_records[day] = attendance.status if attendance else 'not_marked'
    
    # Calculate statistics
    total_days = len([a for a in attendance_records.values() if a != 'not_marked'])
    present_days = len([a for a in attendance_records.values() if a == 'present'])
    absent_days = len([a for a in attendance_records.values() if a == 'absent'])
    late_days = len([a for a in attendance_records.values() if a == 'late'])
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return render_template('attendance/student_attendance.html',
                          student=student,
                          user=user,
                          month=month,
                          year=year,
                          days=days,
                          attendance_records=attendance_records,
                          attendance_percentage=attendance_percentage,
                          present_days=present_days,
                          absent_days=absent_days,
                          late_days=late_days)

# Attendance report
@attendance_bp.route('/report')
@login_required
def attendance_report():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    classes = Class.query.all()
    
    # Get parameters
    class_id = request.args.get('class_id', type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    if class_id:
        # Get all students in the class
        students = Student.query.options(joinedload(Student.user)).filter_by(class_id=class_id).all()
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month)[1]
        days = [datetime(year, month, day).date() for day in range(1, num_days + 1)]
        
        # Get attendance data for each student
        attendance_data = []
        for student in students:
            student_data = {
                'id': student.user_id,
                'name': student.user.full_name,
                'attendance': {}
            }
            
            for day in days:
                attendance = Attendance.query.filter_by(
                    student_id=student.id,
                    date=day
                ).first()
                
                student_data['attendance'][day] = attendance.status if attendance else 'not_marked'
            
            # Calculate statistics
            total_days = len([a for a in student_data['attendance'].values() if a != 'not_marked'])
            present_days = len([a for a in student_data['attendance'].values() if a == 'present'])
            
            student_data['percentage'] = (present_days / total_days * 100) if total_days > 0 else 0
            
            attendance_data.append(student_data)
        
        return render_template('attendance/report.html',
                              classes=classes,
                              selected_class=Class.query.get(class_id),
                              month=month,
                              year=year,
                              days=days,
                              attendance_data=attendance_data)
    
    return render_template('attendance/report.html',
                          classes=classes,
                          month=month,
                          year=year)