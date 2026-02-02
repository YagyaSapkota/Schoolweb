from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from app.models.models import User, Admin, Teacher, Student, Parent, db
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
user_bp = Blueprint('user', __name__)

# User profile view
@user_bp.route('/profile')
@login_required
def profile():
    return render_template(f'{current_user.role}/profile.html', user=current_user)

# User profile update
@user_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        
        # Update basic info
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user.full_name = f"{first_name} {last_name}"
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename:
                # Save file logic would go here
                filename = f"user_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                file_path = f"app/static/images/profiles/{filename}"
                file.save(file_path)
                user.profile_pic = f"/static/images/profiles/{filename}"
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))

# Change password
@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('user.change_password'))
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('user.change_password'))
        
        # Update password
        user = User.query.get(current_user.id)
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('change_password.html')

# Admin functions for user management
@user_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.asc()).all()
    return render_template('admin/users.html', users=users)

# Create new user (admin only)
@user_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('user.create_user'))
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            full_name=f"{first_name} {last_name}",
            email=email,
            password=hashed_password,
            role=role,
            created_at=datetime.now()
        )
        
        db.session.add(new_user)
        db.session.flush()
        
        # Create role-specific profile
        if role == 'admin':
            admin_id = f"ADM{new_user.id:03d}"
            profile = Admin(
                user_id=new_user.id,
                admin_id=admin_id,
                department=request.form.get('designation', 'Administration')
            )
            db.session.add(profile)
        elif role == 'teacher':
            teacher_id = f"TCH{new_user.id:03d}"
            profile = Teacher(
                user_id=new_user.id,
                teacher_id=teacher_id,
                subject=request.form.get('department', ''),
                qualification=request.form.get('qualification', '')
            )
            db.session.add(profile)
        elif role == 'student':
            student_id = f"STD{new_user.id:03d}"
            profile = Student(
                user_id=new_user.id,
                student_id=student_id,
                roll_number=request.form.get('roll_number', f"ROLL{new_user.id:03d}"),
                class_id=request.form.get('class_id') or None,
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            )
            db.session.add(profile)
        elif role == 'parent':
            parent_id = f"PRT{new_user.id:03d}"
            profile = Parent(
                user_id=new_user.id,
                parent_id=parent_id,
                phone=request.form.get('phone', ''),
                occupation=request.form.get('occupation', '')
            )
            db.session.add(profile)
        
        db.session.commit()
        flash(f'New {role} created successfully!', 'success')
        return redirect(url_for('user.admin_users'))
    
    # Get classes for student assignment
    from app.models.models import Class
    classes = Class.query.all()
    return render_template('admin/create_user.html', classes=classes)

# Edit user (admin only)
@user_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user.full_name = f"{first_name} {last_name}"
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.status = request.form.get('status')
        
        # Update password if provided
        if request.form.get('password'):
            user.password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('user.admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

# Delete user (admin only)
@user_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('user.admin_users'))
    
    # Reassign resources to current admin to prevent IntegrityError
    try:
        from app.models.models import Resource
        user_resources = Resource.query.filter_by(uploaded_by=user.id).all()
        for resource in user_resources:
            resource.uploaded_by = current_user.id
        # We don't commit here, we'll commit with the delete
    except Exception as e:
        print(f"Error reassigning resources: {e}")

    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('user.admin_users'))