from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models.models import Exam, ExamResult, Student, Class, Subject, db
from datetime import datetime

exam_bp = Blueprint('exam', __name__)

# List all exams
@exam_bp.route('/exams')
@login_required
def exam_list():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    exams = Exam.query.all()
    return render_template('exam/list.html', exams=exams)

# Create new exam
@exam_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
def create_exam():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    classes = Class.query.all()
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        title = request.form.get('name')
        exam_type = request.form.get('exam_type')
        class_id = request.form.get('class_id')
        subject_id = request.form.get('subject_id')
        exam_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        total_marks = request.form.get('total_marks')
        passing_marks = request.form.get('passing_marks')
        
        new_exam = Exam(
            title=title,
            exam_type=exam_type,
            class_id=class_id,
            subject_id=subject_id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            total_marks=total_marks,
            passing_marks=passing_marks,
            created_by=current_user.id
        )
        
        db.session.add(new_exam)
        db.session.commit()
        
        flash('Exam created successfully!', 'success')
        return redirect(url_for('exam.exam_list'))
    
    return render_template('exam/create.html', classes=classes, subjects=subjects)

# View exam details
@exam_bp.route('/exams/<int:exam_id>')
@login_required
def exam_detail(exam_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    results = ExamResult.query.filter_by(exam_id=exam_id).all()
    
    # Calculate statistics
    total_students = len(results)
    passed_students = len([r for r in results if r.marks >= exam.passing_marks])
    failed_students = total_students - passed_students
    
    if total_students > 0:
        pass_percentage = (passed_students / total_students) * 100
        avg_marks = sum([r.marks for r in results]) / total_students
    else:
        pass_percentage = 0
        avg_marks = 0
    
    return render_template('exam/detail.html', 
                          exam=exam, 
                          results=results,
                          total_students=total_students,
                          passed_students=passed_students,
                          failed_students=failed_students,
                          pass_percentage=pass_percentage,
                          avg_marks=avg_marks)

# Enter exam results
@exam_bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@login_required
def enter_results(exam_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    students = Student.query.filter_by(class_id=exam.class_id).all()
    
    if request.method == 'POST':
        # Delete existing results
        ExamResult.query.filter_by(exam_id=exam_id).delete()
        
        # Add new results
        for student in students:
            marks = request.form.get(f'marks_{student.user_id}')
            remarks = request.form.get(f'remarks_{student.user_id}')
            
            result = ExamResult(
                exam_id=exam_id,
                student_id=student.user_id,
                marks=marks,
                remarks=remarks,
                date=datetime.now()
            )
            
            db.session.add(result)
        
        db.session.commit()
        flash('Exam results saved successfully!', 'success')
        return redirect(url_for('exam.exam_detail', exam_id=exam_id))
    
    # Get existing results
    results = {}
    for student in students:
        result = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student.user_id
        ).first()
        
        if result:
            results[student.user_id] = {
                'marks': result.marks,
                'remarks': result.remarks
            }
    
    return render_template('exam/enter_results.html', 
                          exam=exam, 
                          students=students,
                          results=results)

# Student exam results
@exam_bp.route('/student/results/<int:student_id>')
@login_required
def student_results(student_id):
    # Check permissions
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        # Check if parent viewing their child's results
        if current_user.role == 'parent':
            # Logic to check if student is child of parent would go here
            pass
        else:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=student_id).first_or_404()
    results = ExamResult.query.filter_by(student_id=student_id).all()
    
    # Group results by exam type
    grouped_results = {}
    for result in results:
        exam_type = result.exam.exam_type
        if exam_type not in grouped_results:
            grouped_results[exam_type] = []
        
        grouped_results[exam_type].append(result)
    
    return render_template('exam/student_results.html',
                          student=student,
                          grouped_results=grouped_results)