from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.models.models import db, Teacher, Student, Class, Subject

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/my-students')
@login_required
def my_students():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all subjects taught by this teacher
    teacher_subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    
    # Get unique students enrolled in these subjects
    # For now, we'll get students from the classes the teacher teaches
    class_ids = [subject.class_id for subject in teacher_subjects if subject.class_id]
    students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    
    return render_template('teacher/my_students.html', students=students, teacher=teacher)

@teacher_bp.route('/my-subjects')
@login_required
def my_subjects():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    # Fetch subjects assigned to this teacher
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all() if teacher else []
    return render_template('teacher/my_subjects.html', subjects=subjects)

@teacher_bp.route('/add-subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        class_id = request.form.get('class_id') # This is just an integer 1-12 from the form
        description = request.form.get('description')
        
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
             flash('Teacher profile not found.', 'danger')
             return redirect(url_for('dashboard'))

        # Check if subject code already exists
        if Subject.query.filter_by(code=code).first():
            flash('Subject code already exists.', 'danger')
            return redirect(url_for('teacher.add_subject'))
            
        # In a real app, we would link to an actual Class model instance.
        # Since the user asked for "select 1 to 12 class", we might need to find or create the Class record.
        # For now, let's assume we just store the class_id if the model allows, or we find the class by name.
        # Let's try to find a class with that name (e.g., "Class 1") or create it if it doesn't exist.
        
        class_name = f"Class {class_id}"
        class_obj = Class.query.filter_by(name=class_name).first()
        if not class_obj:
            class_obj = Class(name=class_name, teacher_id=teacher.id) # Assign creating teacher as class teacher for now
            db.session.add(class_obj)
            db.session.flush()
            
        new_subject = Subject(
            name=name,
            code=code,
            description=description,
            class_id=class_obj.id,
            teacher_id=teacher.id
        )
        
        db.session.add(new_subject)
        db.session.commit()
        
        flash('Subject added successfully!', 'success')
        return redirect(url_for('teacher.my_subjects'))
        
    return render_template('teacher/add_subject.html')

@teacher_bp.route('/create-exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    from app.models.models import Exam
    from datetime import datetime
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get teacher's subjects for the dropdown
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        exam_type = request.form.get('exam_type')
        subject_id = request.form.get('subject_id')
        exam_date = request.form.get('exam_date')
        duration = request.form.get('duration_minutes')
        total_marks = request.form.get('total_marks')
        room = request.form.get('room')
        description = request.form.get('description')
        
        # Get class_id from the selected subject
        subject = Subject.query.get(subject_id)
        
        new_exam = Exam(
            title=title,
            exam_type=exam_type,
            subject_id=subject_id,
            class_id=subject.class_id if subject else None,
            exam_date=datetime.strptime(exam_date, '%Y-%m-%dT%H:%M'),
            duration_minutes=duration,
            total_marks=total_marks,
            room=room,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(new_exam)
        db.session.commit()
        
        flash('Exam scheduled successfully!', 'success')
        return redirect(url_for('teacher.my_exams'))
    
    return render_template('teacher/create_exam.html', subjects=subjects)

@teacher_bp.route('/my-exams')
@login_required
def my_exams():
    from app.models.models import Exam
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all exams for classes taught by this teacher
    teacher_subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    class_ids = [s.class_id for s in teacher_subjects if s.class_id]
    
    # Get exams for teacher's classes
    exams = Exam.query.filter(Exam.class_id.in_(class_ids)).order_by(Exam.exam_date).all() if class_ids else []
    
    return render_template('teacher/my_exams.html', exams=exams)

@teacher_bp.route('/edit-exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    from app.models.models import Exam
    from datetime import datetime
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if this exam belongs to a class taught by this teacher
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher or exam.created_by != current_user.id:
        flash('You do not have permission to edit this exam.', 'danger')
        return redirect(url_for('teacher.my_exams'))
        
    if request.method == 'POST':
        exam.title = request.form.get('title')
        exam.exam_type = request.form.get('exam_type')
        exam.subject_id = request.form.get('subject_id')
        exam_date_str = request.form.get('exam_date')
        exam.exam_date = datetime.strptime(exam_date_str, '%Y-%m-%dT%H:%M')
        exam.duration_minutes = request.form.get('duration_minutes')
        exam.total_marks = request.form.get('total_marks')
        exam.room = request.form.get('room')
        exam.description = request.form.get('description')
        
        # Update class_id based on subject
        subject = Subject.query.get(exam.subject_id)
        if subject:
            exam.class_id = subject.class_id
            
        db.session.commit()
        flash('Exam updated successfully!', 'success')
        return redirect(url_for('teacher.my_exams'))
        
    # Get subjects for dropdown
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    return render_template('teacher/edit_exam.html', exam=exam, subjects=subjects)

@teacher_bp.route('/delete-exam/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    from app.models.models import Exam
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    exam = Exam.query.get_or_404(exam_id)
    
    # Check permission
    if exam.created_by != current_user.id:
        flash('You do not have permission to delete this exam.', 'danger')
        return redirect(url_for('teacher.my_exams'))
        
    db.session.delete(exam)
    db.session.commit()
    
    flash('Exam deleted successfully!', 'success')
    return redirect(url_for('teacher.my_exams'))

@teacher_bp.route('/exam/\u003cint:exam_id\u003e/enter-grades', methods=['GET', 'POST'])
@login_required
def enter_grades(exam_id):
    from app.models.models import Exam, ExamResult
    from datetime import datetime
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if this exam belongs to a subject taught by this teacher
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if teacher has permission to grade this exam
    # Allow if: teacher teaches the subject OR teacher owns the class OR teacher created the exam
    has_permission = False
    
    if exam.subject and exam.subject.teacher_id == teacher.id:
        has_permission = True  # Teacher teaches this subject
    elif exam.class_id:
        exam_class = Class.query.get(exam.class_id)
        if exam_class and exam_class.teacher_id == teacher.id:
            has_permission = True  # Teacher owns this class
    elif exam.created_by == current_user.id:
        has_permission = True  # Teacher created this exam
    
    if not has_permission:
        flash('You do not have permission to enter grades for this exam.', 'danger')
        return redirect(url_for('teacher.my_exams'))
    
    # Get all students in this exam's class
    students = Student.query.filter_by(class_id=exam.class_id).all()
    
    if request.method == 'POST':
        # Process grade entries
        success_count = 0
        error_count = 0
        
        for student in students:
            marks_key = f'marks_{student.id}'
            remarks_key = f'remarks_{student.id}'
            
            marks_str = request.form.get(marks_key, '').strip()
            remarks = request.form.get(remarks_key, '').strip()
            
            # Skip if no marks entered
            if not marks_str:
                continue
            
            try:
                marks = float(marks_str)
                
                # Validate marks
                if marks < 0:
                    flash(f'Invalid marks for {student.user.full_name}: cannot be negative', 'warning')
                    error_count += 1
                    continue
                    
                if marks > exam.total_marks:
                    flash(f'Invalid marks for {student.user.full_name}: exceeds total marks ({exam.total_marks})', 'warning')
                    error_count += 1
                    continue
                
                # Check if result already exists
                existing_result = ExamResult.query.filter_by(
                    exam_id=exam.id,
                    student_id=student.id
                ).first()
                
                if existing_result:
                    # Update existing result
                    existing_result.marks = marks
                    existing_result.remarks = remarks if remarks else None
                    existing_result.date = datetime.now()
                else:
                    # Create new result
                    new_result = ExamResult(
                        exam_id=exam.id,
                        student_id=student.id,
                        marks=marks,
                        remarks=remarks if remarks else None,
                        date=datetime.now()
                    )
                    db.session.add(new_result)
                
                success_count += 1
                
            except ValueError:
                flash(f'Invalid marks format for {student.user.full_name}', 'warning')
                error_count += 1
                continue
        
        if success_count > 0:
            db.session.commit()
            flash(f'Successfully saved grades for {success_count} student(s)!', 'success')
        
        if error_count > 0:
            flash(f'{error_count} grade(s) had errors and were not saved.', 'warning')
        
        return redirect(url_for('teacher.my_exams'))
    
    # GET request - fetch existing results
    existing_results = {}
    for student in students:
        result = ExamResult.query.filter_by(exam_id=exam.id, student_id=student.id).first()
        if result:
            existing_results[student.id] = {
                'marks': result.marks,
                'remarks': result.remarks
            }
    
    return render_template('teacher/enter_grades.html', 
                         exam=exam, 
                         students=students,
                         existing_results=existing_results)

@teacher_bp.route('/create-class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        section = request.form.get('section', '').strip()
        description = request.form.get('description', '').strip()
        
        # Check if class already exists
        existing_class = Class.query.filter_by(name=class_name, section=section).first()
        if existing_class:
            flash('A class with this name and section already exists.', 'warning')
            return redirect(url_for('teacher.create_class'))
        
        new_class = Class(
            name=class_name,
            section=section if section else None,
            teacher_id=teacher.id
        )
        
        db.session.add(new_class)
        db.session.commit()
        
        flash(f'Class "{class_name} {section}" created successfully!', 'success')
        return redirect(url_for('teacher.my_classes'))
    
    return render_template('teacher/create_class.html')

@teacher_bp.route('/my-classes')
@login_required
def my_classes():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all classes created by this teacher
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('teacher/my_classes.html', classes=classes)

@teacher_bp.route('/upload-resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    from app.models.models import Resource
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app
    from app.controllers.common_controller import ALLOWED_RESOURCE_EXTENSIONS
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get teacher's classes
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        class_id = request.form.get('class_id')
        file = request.files.get('file')
        
        if not title or not class_id or not file:
            flash('All fields are required.', 'warning')
            return redirect(url_for('teacher.upload_resource'))
            
        if file.filename == '':
            flash('No selected file', 'warning')
            return redirect(url_for('teacher.upload_resource'))
            
        if file:
            try:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext not in ALLOWED_RESOURCE_EXTENSIONS:
                    flash('Only PDF, PNG and JPEG files can be uploaded as resources.', 'warning')
                    return redirect(url_for('teacher.upload_resource'))

                # Ensure upload directory exists
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'resources')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Store path with forward slashes for URL compatibility
                file_path = f"uploads/resources/{filename}"
                full_path = os.path.join(upload_folder, filename)
                file.save(full_path)
                
                new_resource = Resource(
                    title=title,
                    file_path=file_path,
                    class_id=class_id,
                    uploaded_by=current_user.id
                )
                
                db.session.add(new_resource)
                db.session.commit()
                
                flash('Resource uploaded successfully!', 'success')
                return redirect(url_for('teacher.my_resources'))
            except Exception as e:
                print(f"Upload error: {e}")
                flash(f'Error uploading resource: {str(e)}', 'danger')
                return redirect(url_for('teacher.upload_resource'))
            
    return render_template('teacher/upload_resource.html', classes=classes)

@teacher_bp.route('/my-resources')
@login_required
def my_resources():
    from app.models.models import Resource
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get resources uploaded by this teacher
    resources = Resource.query.filter_by(uploaded_by=current_user.id).order_by(Resource.uploaded_at.desc()).all()
    
    return render_template('teacher/my_resources.html', resources=resources)

@teacher_bp.route('/delete-resource/<int:resource_id>')
@login_required
def delete_resource(resource_id):
    from app.models.models import Resource
    import os
    
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    resource = Resource.query.get_or_404(resource_id)
    
    if resource.uploaded_by != current_user.id:
        flash('You do not have permission to delete this resource.', 'danger')
        return redirect(url_for('teacher.my_resources'))
        
    # Try to delete the file
    try:
        full_path = os.path.join(current_app.root_path, 'static', resource.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
        
    db.session.delete(resource)
    db.session.commit()
    
    flash('Resource deleted successfully.', 'success')
    return redirect(url_for('teacher.my_resources'))
