from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app.models.models import db, Assignment, Class, Subject, Student

assignment_bp = Blueprint('assignment', __name__)

@assignment_bp.route('/assignment/manage', methods=['GET', 'POST'])
@login_required
def manage():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied. Only teachers or admins can manage assignments.', 'danger')
        return redirect(url_for('dashboard'))

    classes = Class.query.all()
    subjects = Subject.query.all()

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        class_id = request.form.get('class_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

        if not title:
            flash('Title is required', 'danger')
        else:
            a = Assignment(
                title=title,
                description=description,
                class_id=class_id,
                subject_id=subject_id,
                due_date=due_date,
                created_by=current_user.id,
                created_at=datetime.now()
            )
            db.session.add(a)
            db.session.commit()
            flash('Assignment created successfully', 'success')
            return redirect(url_for('assignment.manage'))

    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    return render_template('assignment/manage.html', assignments=assignments, classes=classes, subjects=subjects)

@assignment_bp.route('/assignment/my')
@login_required
def my_assignments():
    if current_user.role != 'student':
        flash('Access denied. Only students can view their assignments.', 'danger')
        return redirect(url_for('dashboard'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    class_id = student.class_id if student else None
    assignments = Assignment.query.filter_by(class_id=class_id).order_by(Assignment.due_date).all() if class_id else []
    return render_template('assignment/my.html', assignments=assignments)