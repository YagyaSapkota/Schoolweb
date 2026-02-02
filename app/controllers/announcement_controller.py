from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app.models.models import db, Announcement, Class, Student

announcement_bp = Blueprint('announcement', __name__)

@announcement_bp.route('/announcement', methods=['GET'])
@login_required
def list():
    role = current_user.role
    # Determine class filter for students/parents
    class_ids = []
    if role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if student and student.class_id:
            class_ids = [student.class_id]
    # For simplicity, parents see role-targeted and all announcements
    query = Announcement.query
    if role in ['admin', 'teacher']:
        # Admins/teachers see all
        announcements = query.order_by(Announcement.created_at.desc()).all()
    else:
        announcements = query.filter(
            (Announcement.audience_role == 'all') | (Announcement.audience_role == role)
        ).order_by(Announcement.created_at.desc()).all()
        if class_ids:
            announcements = [a for a in announcements if (a.class_id in class_ids) or (a.class_id is None)]

    return render_template('announcement/list.html', announcements=announcements)

@announcement_bp.route('/announcement/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied. Only admins or teachers can create announcements.', 'danger')
        return redirect(url_for('dashboard'))

    classes = Class.query.all()
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        audience_role = (request.form.get('audience_role') or 'all').strip()
        class_id = request.form.get('class_id', type=int)

        if not title or not content:
            flash('Title and content are required', 'danger')
        else:
            ann = Announcement(
                title=title,
                content=content,
                audience_role=audience_role,
                class_id=class_id,
                created_by=current_user.id,
                created_at=datetime.now()
            )
            db.session.add(ann)
            db.session.commit()
            flash('Announcement published', 'success')
            return redirect(url_for('announcement.list'))

    return render_template('announcement/create.html', classes=classes)

@announcement_bp.route('/announcement/delete/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Announcement deleted successfully', 'success')
    return redirect(url_for('announcement.list'))