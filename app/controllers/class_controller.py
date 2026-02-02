from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models.models import Class, Subject, Teacher, Student, db

class_bp = Blueprint('class', __name__)

# Class list view
@class_bp.route('/classes')
@login_required
def class_list():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    classes = Class.query.all()
    return render_template('class/list.html', classes=classes)

# Class detail view
@class_bp.route('/classes/<int:class_id>')
@login_required
def class_detail(class_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    subjects = Subject.query.filter_by(class_id=class_id).all()
    
    return render_template('class/detail.html', 
                          class_obj=class_obj, 
                          students=students,
                          subjects=subjects)

# Add new class (admin and teacher)
@class_bp.route('/classes/add', methods=['GET', 'POST'])
@login_required
def add_class():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        section = request.form.get('section')
        class_teacher_id = request.form.get('class_teacher_id')
        
        new_class = Class(
            name=name,
            section=section,
            teacher_id=class_teacher_id
        )
        
        db.session.add(new_class)
        db.session.commit()
        
        flash('Class added successfully!', 'success')
        return redirect(url_for('class.class_list'))
    
    return render_template('class/add.html', teachers=teachers)

# Edit class (admin only)
@class_bp.route('/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
def edit_class(class_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        class_obj.name = request.form.get('name')
        class_obj.section = request.form.get('section')
        class_obj.teacher_id = request.form.get('class_teacher_id')
        
        db.session.commit()
        flash('Class updated successfully!', 'success')
        return redirect(url_for('class.class_list'))
    
    return render_template('class/edit.html', class_obj=class_obj, teachers=teachers)

# Delete class (admin only)
@class_bp.route('/classes/delete/<int:class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if class has students
    students = Student.query.filter_by(class_id=class_id).all()
    if students:
        flash('Cannot delete class with students. Please reassign students first.', 'danger')
        return redirect(url_for('class.class_list'))
    
    db.session.delete(class_obj)
    db.session.commit()
    
    flash('Class deleted successfully!', 'success')
    return redirect(url_for('class.class_list'))

# Add subject to class
@class_bp.route('/classes/<int:class_id>/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject(class_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get_or_404(class_id)
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        teacher_id = request.form.get('teacher_id')
        
        new_subject = Subject(
            name=name,
            code=code,
            class_id=class_id,
            teacher_id=teacher_id
        )
        
        db.session.add(new_subject)
        db.session.commit()
        
        flash('Subject added successfully!', 'success')
        return redirect(url_for('class.class_detail', class_id=class_id))
    
    return render_template('class/add_subject.html', class_obj=class_obj, teachers=teachers)

# Student join class
@class_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_class():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if student already has a class
    existing_student = Student.query.filter_by(user_id=current_user.id).first()
    if existing_student:
        flash('You are already enrolled in a class', 'info')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        
        if not class_id:
            flash('Please select a class', 'danger')
            return redirect(url_for('class.join_class'))
        
        # Create student record
        new_student = Student(
            user_id=current_user.id,
            class_id=class_id,
            roll_number=request.form.get('roll_number', ''),
            admission_date=request.form.get('admission_date')
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Successfully joined the class!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get available classes
    classes = Class.query.all()
    return render_template('class/join.html', classes=classes)

# Subject list view
@class_bp.route('/subjects')
@login_required
def subject_list():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = Subject.query.all()
    return render_template('class/subjects.html', subjects=subjects)

# Delete subject (admin only)
@class_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if subject has exams (integrity check)
    if subject.exams:
        flash('Cannot delete subject with scheduled exams. Please remove exams first.', 'danger')
        return redirect(url_for('class.subject_list'))

    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('class.subject_list'))