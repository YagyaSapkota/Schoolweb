from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.models import db, Resource, Class, Student
from werkzeug.utils import secure_filename
import os
from datetime import datetime

common_bp = Blueprint('common', __name__)

@common_bp.route('/calendar')
@login_required
def calendar():
    return render_template('common/calendar.html')

@common_bp.route('/resources')
@login_required
def resources():
    role = current_user.role
    query = Resource.query
    
    if role == 'student':
        # Students see general resources + their class resources
        student = Student.query.filter_by(user_id=current_user.id).first()
        if student and student.class_id:
            query = query.filter((Resource.class_id == None) | (Resource.class_id == student.class_id))
        else:
            query = query.filter(Resource.class_id == None)
    elif role == 'parent':
         # Parents see general resources (could be expanded to children's class resources)
         query = query.filter(Resource.class_id == None)
    
    # Admins and Teachers see all resources by default (could be filtered)
    resources = query.order_by(Resource.uploaded_at.desc()).all()
    
    return render_template('common/resources.html', resources=resources)

ALLOWED_RESOURCE_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


@common_bp.route('/resources/upload', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied. Only admins and teachers can upload resources.', 'danger')
        return redirect(url_for('common.resources'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        class_id = request.form.get('class_id')
        
        if not title:
            flash('Title is required', 'danger')
            return redirect(url_for('common.upload_resource'))
            
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('common.upload_resource'))
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('common.upload_resource'))
            
        if file:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext not in ALLOWED_RESOURCE_EXTENSIONS:
                flash('Only PDF, PNG and JPEG files can be uploaded as resources.', 'danger')
                return redirect(url_for('common.upload_resource'))

            # Add timestamp to filename to prevent duplicates
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Use 'app/static' to match Flask configuration
            upload_folder = os.path.join(current_app.root_path, 'app', 'static', 'uploads', 'resources')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Relative path for database
            db_path = f"uploads/resources/{filename}"
            
            resource = Resource(
                title=title,
                description=description,
                file_path=db_path,
                class_id=int(class_id) if class_id else None,
                uploaded_by=current_user.id
            )
            
            db.session.add(resource)
            db.session.commit()
            
            flash('Resource uploaded successfully!', 'success')
            return redirect(url_for('common.resources'))
            
    classes = Class.query.all()
    return render_template('common/upload_resource.html', classes=classes)

@common_bp.route('/resources/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Allow deletion if user is admin OR if user is the uploader (teacher)
    if current_user.role != 'admin' and resource.uploaded_by != current_user.id:
        flash('Access denied. You can only delete your own resources.', 'danger')
        return redirect(url_for('common.resources'))
    
    # Delete file from filesystem
    try:
        # Check correct path (app/static)
        file_path_correct = os.path.join(current_app.root_path, 'app', 'static', resource.file_path)
        if os.path.exists(file_path_correct):
            os.remove(file_path_correct)
            
        # Check legacy/buggy path (static) and clean up if exists
        file_path_legacy = os.path.join(current_app.root_path, 'static', resource.file_path)
        if os.path.exists(file_path_legacy):
            os.remove(file_path_legacy)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    try:
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting resource: {str(e)}', 'danger')
        print(f"DB Error: {e}")
    
    return redirect(url_for('common.resources'))

@common_bp.route('/settings')
@login_required
def settings():
    return render_template('common/settings.html')

@common_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    
    # Update user's full name
    current_user.full_name = f"{first_name} {last_name}".strip()
    current_user.email = email
    
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('common.settings'))

@common_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    from flask_bcrypt import Bcrypt
    
    bcrypt = Bcrypt()
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Verify current password
    if not bcrypt.check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('common.settings'))
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('common.settings'))
    
    # Update password
    current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('common.settings'))
