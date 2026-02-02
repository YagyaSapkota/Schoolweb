from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models.models import Student, User, Class, Attendance, ExamResult, FeePayment, db
from datetime import datetime

student_bp = Blueprint('student', __name__)

# Student list view (for admin and teachers)
@student_bp.route('/students')
@login_required
def student_list():
    if current_user.role not in ['admin', 'teacher']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    students = Student.query.join(User).all()
    return render_template('student/list.html', students=students)

# Student detail view
@student_bp.route('/students/<int:student_id>')
@login_required
def student_detail(student_id):
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=student_id).first_or_404()
    user = User.query.get(student_id)
    
    # Get related data
    attendance = Attendance.query.filter_by(student_id=student_id).all()
    exam_results = ExamResult.query.filter_by(student_id=student_id).all()
    fee_payments = FeePayment.query.filter_by(student_id=student_id).all()
    
    return render_template('student/detail.html', 
                          student=student, 
                          user=user, 
                          attendance=attendance,
                          exam_results=exam_results,
                          fee_payments=fee_payments)

# Add new student (admin only)
@student_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    classes = Class.query.all()
    
    if request.method == 'POST':
        # First create user account
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('student.add_student'))
        
        # Create user
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            role='student',
            date_joined=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Create student profile
        admission_number = request.form.get('admission_number')
        roll_number = request.form.get('roll_number')
        class_id = request.form.get('class_id')
        date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
        
        new_student = Student(
            user_id=new_user.id,
            admission_number=admission_number,
            roll_number=roll_number,
            class_id=class_id,
            date_of_birth=date_of_birth,
            blood_group=request.form.get('blood_group'),
            address=request.form.get('address')
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('student.student_list'))
    
    return render_template('student/add.html', classes=classes)

# Edit student (admin only)
@student_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=student_id).first_or_404()
    user = User.query.get(student_id)
    classes = Class.query.all()
    
    if request.method == 'POST':
        # Update user info
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        
        # Update student info
        student.admission_number = request.form.get('admission_number')
        student.roll_number = request.form.get('roll_number')
        student.class_id = request.form.get('class_id')
        student.blood_group = request.form.get('blood_group')
        student.address = request.form.get('address')
        
        if request.form.get('date_of_birth'):
            student.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('student.student_list'))
    
    return render_template('student/edit.html', student=student, user=user, classes=classes)

# Delete student (admin only)
@student_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=student_id).first_or_404()
    user = User.query.get(student_id)
    
    # Delete student profile first (due to foreign key constraints)
    db.session.delete(student)
    # Then delete user account
    db.session.delete(user)
    db.session.commit()
    
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('student.student_list'))

# Student dashboard (for students)
@student_bp.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get student's class
    student_class = Class.query.get(student.class_id)
    
    # Get attendance statistics
    total_days = Attendance.query.filter_by(student_id=current_user.id).count()
    present_days = Attendance.query.filter_by(student_id=current_user.id, status='present').count()
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get recent exam results
    recent_results = ExamResult.query.filter_by(student_id=current_user.id).order_by(ExamResult.date.desc()).limit(5).all()
    
    # Get fee payment status
    pending_fees = FeePayment.query.filter_by(student_id=current_user.id, status='pending').all()
    
    return render_template('student/dashboard.html', 
                          student=student,
                          student_class=student_class,
                          attendance_percentage=attendance_percentage,
                          recent_results=recent_results,
                          pending_fees=pending_fees)

@student_bp.route('/my-courses')
@login_required
def my_courses():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    from app.models.models import Subject
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    courses = []
    
    if student and student.class_id:
        courses = Subject.query.filter_by(class_id=student.class_id).all()
        
    return render_template('student/my_courses.html', courses=courses)

@student_bp.route('/grades')
@login_required
def grades():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    from app.models.models import Subject, Exam, ExamResult, Attendance
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    grades_data = []
    summary = {
        'gpa': 0.0,
        'average_grade': 'N/A',
        'credits_earned': 0, # Placeholder as we don't have credits in model
        'attendance': 0
    }
    
    if student and student.class_id:
        # 1. Attendance
        total_days = Attendance.query.filter_by(student_id=student.user_id).count()
        present_days = Attendance.query.filter_by(student_id=student.user_id, status='present').count()
        if total_days > 0:
            summary['attendance'] = round((present_days / total_days) * 100)
            
        # 2. Subjects and Grades
        subjects = Subject.query.filter_by(class_id=student.class_id).all()
        total_percentage_sum = 0
        subject_count = 0
        
        for subject in subjects:
            # Get teacher name
            teacher_name = subject.teacher.user.full_name if subject.teacher else 'N/A'
            
            # Get exams for this subject
            exams = Exam.query.filter_by(subject_id=subject.id).all()
            
            term1_score = '-'
            term2_score = '-'
            term3_score = '-'
            final_term_score = '-'
            
            total_score = 0
            exam_count = 0
            
            for exam in exams:
                result = ExamResult.query.filter_by(exam_id=exam.id, student_id=student.id).first()
                if result:
                    score = result.marks # Assuming marks are absolute or normalized to 100
                    # Check max marks if available
                    if exam.total_marks > 0:
                        normalized_score = (score / exam.total_marks) * 100
                    else:
                        normalized_score = score
                    
                    rounded_score = round(normalized_score)
                        
                    if 'Term 1' in exam.exam_type:
                        term1_score = rounded_score
                    elif 'Term 2' in exam.exam_type:
                        term2_score = rounded_score
                    elif 'Term 3' in exam.exam_type:
                        term3_score = rounded_score
                    elif 'Final Term' in exam.exam_type:
                        final_term_score = rounded_score
                    
                    # Include other types (Quiz, etc) in calculation but maybe not column display if purely term based
                    # Or keep logic simple: include all graded exams in average
                    total_score += normalized_score
                    exam_count += 1
            
            subject_average = 0
            if exam_count > 0:
                subject_average = round(total_score / exam_count)
                total_percentage_sum += subject_average
                subject_count += 1
                
            # Determine Letter Grade
            grade_letter = 'F'
            badge_class = 'danger'
            if subject_average >= 90: grade_letter, badge_class = 'A+', 'success'
            elif subject_average >= 85: grade_letter, badge_class = 'A', 'success'
            elif subject_average >= 80: grade_letter, badge_class = 'A-', 'success'
            elif subject_average >= 75: grade_letter, badge_class = 'B+', 'primary'
            elif subject_average >= 70: grade_letter, badge_class = 'B', 'primary'
            elif subject_average >= 65: grade_letter, badge_class = 'C+', 'info'
            elif subject_average >= 60: grade_letter, badge_class = 'C', 'info'
            elif subject_average >= 50: grade_letter, badge_class = 'D', 'warning'
            
            grades_data.append({
                'subject': subject.name,
                'teacher': teacher_name,
                'term1': term1_score,
                'term2': term2_score,
                'term3': term3_score,
                'final_term': final_term_score,
                'total': subject_average if exam_count > 0 else '-',
                'grade': grade_letter if exam_count > 0 else '-',
                'badge_class': badge_class
            })
            
        # 3. Overall Stats
        if subject_count > 0:
            overall_avg = total_percentage_sum / subject_count
            
            # Simple 4.0 GPA scale approximation
            if overall_avg >= 90: summary['gpa'] = 4.0
            elif overall_avg >= 85: summary['gpa'] = 3.7
            elif overall_avg >= 80: summary['gpa'] = 3.3
            elif overall_avg >= 75: summary['gpa'] = 3.0
            elif overall_avg >= 70: summary['gpa'] = 2.7
            elif overall_avg >= 65: summary['gpa'] = 2.3
            elif overall_avg >= 60: summary['gpa'] = 2.0
            elif overall_avg >= 50: summary['gpa'] = 1.0
            else: summary['gpa'] = 0.0
            
            if overall_avg >= 90: summary['average_grade'] = 'A'
            elif overall_avg >= 80: summary['average_grade'] = 'B'
            elif overall_avg >= 70: summary['average_grade'] = 'C'
            elif overall_avg >= 60: summary['average_grade'] = 'D'
            else: summary['average_grade'] = 'F'
            
            summary['credits_earned'] = subject_count * 3 # Assuming 3 credits per subject
            
    return render_template('student/grades.html', grades=grades_data, summary=summary)

@student_bp.route('/schedule')
@login_required
def schedule():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('student/schedule.html')

@student_bp.route('/browse-classes')
@login_required
def browse_classes():
    from app.models.models import Class
    
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get all available classes
    all_classes = Class.query.all()
    
    # Get classes student is already enrolled in
    enrolled_classes = []
    if student and student.class_id:
        enrolled_classes = [Class.query.get(student.class_id)]
    
    return render_template('student/browse_classes.html', 
                         classes=all_classes,
                         enrolled_classes=enrolled_classes)

@student_bp.route('/join-class/<int:class_id>', methods=['POST'])
@login_required
def join_class(class_id):
    from app.models.models import db
    
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Update student's class_id
    student.class_id = class_id
    db.session.commit()
    
    flash('Successfully joined the class!', 'success')
    return redirect(url_for('student.my_courses'))

@student_bp.route('/download-report')
@login_required
def download_report():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    from flask import Response
    from app.models.models import Subject, Exam, ExamResult, Attendance, Student, Class
    
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    student_class = Class.query.get(student.class_id)
    
    # Generate Report Content
    report_lines = []
    report_lines.append("="*50)
    report_lines.append(f"ACADEMIC REPORT CARD - EduSync")
    report_lines.append("="*50)
    report_lines.append(f"Student Name: {current_user.full_name}")
    report_lines.append(f"Student ID: {current_user.username}") # or similar
    report_lines.append(f"Class: {student_class.name if student_class else 'Not Assigned'}")
    report_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    report_lines.append("-" * 50)
    
    # Attendance
    total_days = Attendance.query.filter_by(student_id=current_user.id).count()
    present_days = Attendance.query.filter_by(student_id=current_user.id, status='present').count()
    attendance_pct = (present_days / total_days * 100) if total_days > 0 else 0
    report_lines.append(f"Attendance: {attendance_pct:.1f}% ({present_days}/{total_days} days)")
    report_lines.append("-" * 50)
    report_lines.append("GRADES SUMMARY")
    report_lines.append("-" * 50)
    
    if student.class_id:
        subjects = Subject.query.filter_by(class_id=student.class_id).all()
        for subject in subjects:
            exams = Exam.query.filter_by(subject_id=subject.id).all()
            total_score = 0
            count = 0
            details = []
            
            for exam in exams:
                res = ExamResult.query.filter_by(exam_id=exam.id, student_id=student.id).first()
                if res:
                    score = res.marks
                    total = exam.total_marks
                    pct = (score/total*100) if total > 0 else 0
                    total_score += pct
                    count += 1
                    details.append(f"  - {exam.title}: {score}/{total} ({pct:.1f}%)")
            
            avg = total_score / count if count > 0 else 0
            grade = 'F'
            if avg >= 90: grade = 'A'
            elif avg >= 80: grade = 'B'
            elif avg >= 70: grade = 'C'
            elif avg >= 60: grade = 'D'
            
            report_lines.append(f"Subject: {subject.name}")
            report_lines.append(f"Average: {avg:.1f}% (Grade: {grade})")
            if details:
                report_lines.extend(details)
            report_lines.append("")
            
    else:
        report_lines.append("No class assigned.")
        
    report_lines.append("=" * 50)
    report_lines.append("End of Report")
    
    content = "\n".join(report_lines)
    
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=academic_report.txt"}
    )