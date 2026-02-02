from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.models import Parent, Student, Attendance, ExamResult, Exam, Subject, FeePayment, Class, db
from datetime import datetime, timedelta

parent_bp = Blueprint('parent', __name__)

@parent_bp.route('/my-children')
@login_required
def my_children():
    if current_user.role != 'parent':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get parent profile
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    if not parent:
        flash('Parent profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all children for this parent
    children = Student.query.filter_by(parent_id=parent.id).all()
    
    # Enrich children data with class info, attendance, and grades
    children_data = []
    for child in children:
        # Get class information
        child_class = Class.query.get(child.class_id) if child.class_id else None
        
        # Calculate attendance for current month
        today = datetime.now().date()
        start_date = today.replace(day=1)
        
        # Handle month end safely
        if start_date.month == 12:
            next_month_start = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month_start = start_date.replace(month=start_date.month + 1, day=1)
        end_date = next_month_start - timedelta(days=1)
        
        records = Attendance.query.filter(
            Attendance.student_id == child.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        attendance_percentage = None
        if records:
            present_count = sum(1 for r in records if r.status == 'present')
            attendance_percentage = round((present_count / len(records)) * 100, 1)
        
        # Calculate average grade
        average_grade = None
        detailed_results = db.session.query(ExamResult, Exam).join(
            Exam, ExamResult.exam_id == Exam.id
        ).filter(ExamResult.student_id == child.id).all()
        
        if detailed_results:
            total_percentage = 0
            count = 0
            for res, exam in detailed_results:
                if exam.total_marks > 0:
                    percentage = (res.marks / exam.total_marks) * 100
                    total_percentage += percentage
                    count += 1
            
            if count > 0:
                average_grade = round(total_percentage / count, 1)
        
        children_data.append({
            'student': child,
            'class': child_class,
            'attendance': attendance_percentage,
            'average_grade': average_grade
        })
    
    return render_template('parent/my_children.html', children=children_data)

@parent_bp.route('/performance')
@login_required
def performance():
    if current_user.role != 'parent':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get parent profile
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    if not parent:
        flash('Parent profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all children
    children = Student.query.filter_by(parent_id=parent.id).all()
    
    # Get performance data for each child
    children_performance = []
    for child in children:
        # Get all exam results with subject information
        results = db.session.query(ExamResult, Exam, Subject).join(
            Exam, ExamResult.exam_id == Exam.id
        ).join(
            Subject, Exam.subject_id == Subject.id
        ).filter(ExamResult.student_id == child.id).order_by(ExamResult.date.desc()).all()
        
        # Group by subject
        subject_grades = {}
        overall_total = 0
        overall_count = 0
        
        for res, exam, subject in results:
            if exam.total_marks > 0:
                percentage = (res.marks / exam.total_marks) * 100
                
                if subject.name not in subject_grades:
                    subject_grades[subject.name] = {
                        'grades': [],
                        'average': 0
                    }
                
                subject_grades[subject.name]['grades'].append({
                    'exam_title': exam.title,
                    'exam_type': exam.exam_type,
                    'marks': res.marks,
                    'total_marks': exam.total_marks,
                    'percentage': round(percentage, 1),
                    'date': res.date
                })
                
                overall_total += percentage
                overall_count += 1
        
        # Calculate subject averages
        for subject_name in subject_grades:
            grades = subject_grades[subject_name]['grades']
            if grades:
                avg = sum(g['percentage'] for g in grades) / len(grades)
                subject_grades[subject_name]['average'] = round(avg, 1)
        
        overall_average = round(overall_total / overall_count, 1) if overall_count > 0 else None
        
        children_performance.append({
            'student': child,
            'subject_grades': subject_grades,
            'overall_average': overall_average
        })
    
    return render_template('parent/performance.html', children_performance=children_performance)

@parent_bp.route('/attendance')
@login_required
def attendance():
    if current_user.role != 'parent':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get parent profile
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    if not parent:
        flash('Parent profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all children
    children = Student.query.filter_by(parent_id=parent.id).all()
    
    # Get attendance data for each child
    children_attendance = []
    for child in children:
        # Get attendance for current month
        today = datetime.now().date()
        start_date = today.replace(day=1)
        
        # Handle month end safely
        if start_date.month == 12:
            next_month_start = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month_start = start_date.replace(month=start_date.month + 1, day=1)
        end_date = next_month_start - timedelta(days=1)
        
        records = Attendance.query.filter(
            Attendance.student_id == child.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        # Create attendance map for calendar display
        attendance_map = {}
        present_count = 0
        absent_count = 0
        late_count = 0
        
        for record in records:
            attendance_map[record.date.day] = record.status
            if record.status == 'present':
                present_count += 1
            elif record.status == 'absent':
                absent_count += 1
            elif record.status == 'late':
                late_count += 1
        
        attendance_percentage = None
        if records:
            attendance_percentage = round((present_count / len(records)) * 100, 1)
        
        children_attendance.append({
            'student': child,
            'attendance_map': attendance_map,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'total_days': len(records),
            'attendance_percentage': attendance_percentage,
            'current_month': today.strftime('%B %Y')
        })
    
    return render_template('parent/attendance.html', children_attendance=children_attendance)

@parent_bp.route('/fee-payments')
@login_required
def fee_payments():
    if current_user.role != 'parent':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get parent profile
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    if not parent:
        flash('Parent profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all children
    children = Student.query.filter_by(parent_id=parent.id).all()
    
    # Get fee payment data for each child
    children_fees = []
    total_paid = 0
    total_pending = 0
    
    for child in children:
        payments = FeePayment.query.filter_by(student_id=child.id).order_by(FeePayment.payment_date.desc()).all()
        
        child_paid = sum(p.amount for p in payments if p.status == 'paid')
        child_pending = sum(p.amount for p in payments if p.status in ['pending', 'failed'])
        
        total_paid += child_paid
        total_pending += child_pending
        
        children_fees.append({
            'student': child,
            'payments': payments,
            'total_paid': child_paid,
            'total_pending': child_pending
        })
    
    return render_template('parent/fee_payments.html', 
                         children_fees=children_fees,
                         total_paid=total_paid,
                         total_pending=total_pending)
