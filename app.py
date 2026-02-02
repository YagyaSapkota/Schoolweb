from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
import os
from datetime import datetime, timedelta

# Import database models
from app.models.models import db, User, Admin, Teacher, Student, Parent, Class
from app.models.message import Message

# Initialize Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-super-secret-key-change-in-production-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'app/static/uploads')

# Session configuration for persistent login
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'instance', 'sessions')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30 days persistent login
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'school_management:'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.remember_cookie_duration = timedelta(days=30)  # 30 days remember me

# Import controllers
from app.controllers.user_controller import user_bp
from app.controllers.student_controller import student_bp
from app.controllers.class_controller import class_bp
from app.controllers.attendance_controller import attendance_bp
from app.controllers.exam_controller import exam_bp
from app.controllers.message_controller import message_bp
from app.controllers.assignment_controller import assignment_bp
from app.controllers.announcement_controller import announcement_bp
from app.controllers.common_controller import common_bp
from app.controllers.teacher_controller import teacher_bp
from app.controllers.parent_controller import parent_bp

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(class_bp, url_prefix='/class')
app.register_blueprint(attendance_bp, url_prefix='/attendance')
app.register_blueprint(exam_bp, url_prefix='/exam')
app.register_blueprint(message_bp, url_prefix='/message')
app.register_blueprint(assignment_bp, url_prefix='/assignment')
app.register_blueprint(announcement_bp, url_prefix='/announcement')
app.register_blueprint(common_bp, url_prefix='/common')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(parent_bp, url_prefix='/parent')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Allow login page access even if already authenticated
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Check if password matches
            password_match = bcrypt.check_password_hash(user.password, form.password.data)
            if password_match:
                # Enhanced persistent login
                remember_me = form.remember.data
                login_user(user, remember=remember_me)
                
                # Set session data for persistent login
                session.permanent = True
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['user_role'] = user.role
                session['login_time'] = datetime.now().isoformat()
                
                db.session.commit()
                
                # Check if this is the user's first login (created within last 5 minutes)
                from datetime import timedelta
                is_new_user = (datetime.now() - user.created_at) < timedelta(minutes=5)
                
                if is_new_user:
                    flash(f'Welcome, {user.full_name}! Your account is ready.', 'success')
                else:
                    flash(f'Welcome back, {user.full_name}!', 'success')
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
                elif user.role == 'student':
                    return redirect(url_for('student_dashboard'))
                elif user.role == 'parent':
                    return redirect(url_for('parent_dashboard'))
                else:
                    # Fallback to main dashboard, ignore any "next" param to avoid unwanted redirects
                    return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Incorrect password.', 'danger')
        else:
            flash('Login unsuccessful. Email not found.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Allow register page access even if already authenticated
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please use a different email or log in.', 'danger')
            return render_template('register.html', form=form)

        # Hash password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(
            full_name=f"{form.first_name.data} {form.last_name.data}",
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            created_at=datetime.now()
        )
        db.session.add(user)
        db.session.flush()  # Get user ID without committing

        # Create role-specific profile
        if form.role.data == 'admin':
            admin = Admin(user_id=user.id, admin_id=f"ADM{user.id}")
            db.session.add(admin)
        elif form.role.data == 'teacher':
            teacher = Teacher(user_id=user.id, teacher_id=f"TCH{user.id}")
            db.session.add(teacher)
        elif form.role.data == 'student':
            student = Student(user_id=user.id, student_id=f"STD{user.id}")
            db.session.add(student)
        elif form.role.data == 'parent':
            parent = Parent(user_id=user.id, parent_id=f"PRT{user.id}")
            db.session.add(parent)
        
        db.session.commit()
        flash(f'Account created successfully! Please log in to get started.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
def dashboard():
    role = request.args.get('role', current_user.role if current_user.is_authenticated else 'user')
    return render_template('dashboard.html', role=role)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get counts for dashboard stats
    students_count = Student.query.count()
    teachers_count = Teacher.query.count()
    parents_count = Parent.query.count()
    classes_count = Class.query.count()

    # Recent Activity (New Users and Announcements)
    from app.models.models import Announcement, User, Exam
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_items = []
    
    for user in recent_users:
        recent_items.append({
            'type': 'user',
            'icon': 'user-plus',
            'color': 'success',
            'title': 'New User Registered',
            'description': f"{user.full_name} ({user.role}) joined EduSync",
            'time': user.created_at
        })
        
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    for ann in recent_announcements:
        recent_items.append({
            'type': 'announcement',
            'icon': 'bullhorn',
            'color': 'primary',
            'title': 'Announcement Posted',
            'description': ann.title,
            'time': ann.created_at
        })

    # Sort combined activity by time desc and take top 5
    recent_items.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_items[:5]

    # Upcoming Events (Future Exams)
    upcoming_events = []
    upcoming_exams = Exam.query.filter(Exam.exam_date >= datetime.now()).order_by(Exam.exam_date).limit(3).all()
    for ex in upcoming_exams:
        upcoming_events.append({
            'day': ex.exam_date.day,
            'month': ex.exam_date.strftime('%b'),
            'title': ex.title,
            'description': f"{ex.subject.name if ex.subject else 'Exam'} - Room {ex.room or 'TBD'}",
            'time': ex.start_time.strftime('%I:%M %p') if ex.start_time else 'TBD'
        })
    
    return render_template('admin/dashboard.html', 
                          students_count=students_count,
                          teachers_count=teachers_count,
                          parents_count=parents_count,
                          classes_count=classes_count,
                          recent_activity=recent_activity,
                          upcoming_events=upcoming_events)

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get teacher profile
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Fetch latest announcement
    try:
        from app.models.models import Announcement
        latest_announcement = Announcement.query.order_by(Announcement.created_at.desc()).first()
    except Exception:
        latest_announcement = None
    
    # Calculate dashboard stats
    from app.models.models import Class, Assignment, Exam, Subject, Student
    
    # My Classes count
    my_classes_count = Class.query.filter_by(teacher_id=teacher.id).count()
    
    # Assignments count (assignments linked to teacher's classes)
    assignments_count = Assignment.query.join(Class).filter(Class.teacher_id == teacher.id).count()
    
    # Exams count (exams linked to teacher's classes - using Subject just in case, but Exam usually links to Class)
    # Checking Exam model again - it has class_id.
    exams_count = Exam.query.join(Class).filter(Class.teacher_id == teacher.id).count()

    # Students count (unique students in teacher's classes)
    # We join Student with Class and filter by teacher_id
    students_count = Student.query.join(Class).filter(Class.teacher_id == teacher.id).count()
    
    return render_template('teacher/dashboard.html', 
                         teacher=teacher, 
                         latest_announcement=latest_announcement,
                         my_classes_count=my_classes_count,
                         assignments_count=assignments_count,
                         exams_count=exams_count,
                         students_count=students_count)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    from app.models.models import Exam, Attendance, Student, ExamResult, Assignment, Subject, Class, db
    from datetime import datetime, timedelta
    
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get student profile
    student = Student.query.filter_by(user_id=current_user.id).first()

    # Compute attendance percentage for current month
    attendance_percentage = 0
    if student:
        today = datetime.now().date()
    # Compute attendance percentage from start of month
    attendance_percentage = 0
    attendance_map = {} # Map day -> status
    if student:
        start_date = today.replace(day=1)
        # Handle month end safely
        if start_date.month == 12:
            next_month_start = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month_start = start_date.replace(month=start_date.month + 1, day=1)
        end_date = next_month_start - timedelta(days=1)

        records = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()

        if records:
            present_count = sum(1 for r in records if r.status == 'present')
            attendance_percentage = (present_count / len(records)) * 100
            for r in records:
                attendance_map[r.date.day] = r.status

    # Get average grade from exam results
    # Helper functions for grade calculation
    def calculate_grade_letter(p):
        if p >= 90: return 'A+'
        if p >= 85: return 'A'
        if p >= 80: return 'A-'
        if p >= 75: return 'B+'
        if p >= 70: return 'B'
        if p >= 65: return 'C+'
        if p >= 60: return 'C'
        if p >= 50: return 'D'
        return 'F'

    def get_badge_class(p):
        if p >= 80: return 'excellent'
        if p >= 70: return 'good'
        if p >= 60: return 'average'
        return 'poor'
    
    average_grade = "N/A"
    recent_grades = []
    if student:
        results = ExamResult.query.filter_by(student_id=student.id).all()
        if results:
            total_marks = sum(r.marks for r in results)  # Assuming marks are percentages or normalized

            # Re-query with join for recent grades and average calculation
            detailed_results = db.session.query(ExamResult, Exam, Subject).join(Exam, ExamResult.exam_id == Exam.id).join(Subject, Exam.subject_id == Subject.id).filter(ExamResult.student_id == student.id).order_by(ExamResult.date.desc()).all()
            
            if detailed_results:
                total_percentage = 0
                count = 0
                for res, exam, sub in detailed_results:
                    # Calculate percentage for this exam
                    if exam.total_marks > 0:
                        percentage = (res.marks / exam.total_marks) * 100
                        total_percentage += percentage
                        count += 1
                        
                        # Add to recent grades list (limit to 5 later)
                        recent_grades.append({
                            'subject': sub.name,
                            'title': exam.title,
                            'type': exam.exam_type,
                            'grade': calculate_grade_letter(percentage), # Helper function needed or inline
                            'percentage': round(percentage, 1),
                            'badge_class': get_badge_class(percentage)
                        })
                
                if count > 0:
                    avg = total_percentage / count
                    average_grade = f"{avg:.1f}%"

    # recent_grades is already populated and sorted desc by date
    recent_grades = recent_grades[:5]

    # Get pending assignments for the student's class
    pending_assignments = []
    student_class = None
    
    # We define today_start for exam filtering (include exams from today even if time passed)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if student and student.class_id:
        # Fetch Class object for display name
        student_class = Class.query.get(student.class_id)
        
        assignments_query = Assignment.query.filter(
            Assignment.class_id == student.class_id,
            Assignment.due_date >= datetime.now().date()
        ).order_by(Assignment.due_date).all()
        
        for asm in assignments_query:
            # Join with Subject to get name
            # Actually Assignment model has relationship `subject`
            days_left = (asm.due_date - datetime.now().date()).days
            pending_assignments.append({
                'title': asm.title,
                'description': asm.description,
                'subject': asm.subject.name if asm.subject else 'General',
                'due_date': asm.due_date,
                'days_left': days_left,
                'badge_class': 'danger' if days_left < 2 else 'warning' if days_left < 5 else 'success'
            })

    # Get Upcoming Exams
    upcoming_exams = []
    if student and student.class_id:
        exams_query = Exam.query.filter(
            Exam.class_id == student.class_id,
            Exam.exam_date >= today_start
        ).order_by(Exam.exam_date).limit(5).all()
        
        for ex in exams_query:
            upcoming_exams.append(ex)

    # Upcoming exams and assignments for the widget
    upcoming_events = []
    # Add exams
    for ex in upcoming_exams:
        upcoming_events.append({
            'title': f"{ex.subject.name} - {ex.title}" if ex.subject else ex.title,
            'description': f"Room: {ex.room}" if ex.room else "Exam",
            'date': ex.exam_date, # datetime
            'time': ex.start_time.strftime('%I:%M %p') if ex.start_time else 'TBD',
            'type': 'exam'
        })
    
    # Add assignments (limit to next few)
    for asm in pending_assignments:
        upcoming_events.append({
            'title': f"{asm['subject']} Assignment",
            'description': asm['title'],
            'date': datetime.combine(asm['due_date'], datetime.min.time()), # convert date to datetime for sorting
            'time': '11:59 PM', # Default for assignments
            'type': 'assignment'
        })
    
    # Sort by date and limit
    upcoming_events.sort(key=lambda x: x['date'])
    upcoming_events = upcoming_events[:5]

    return render_template('student/dashboard.html', 
                         student=student,
                         student_class=student_class,
                         attendance_percentage=attendance_percentage,
                         attendance_map=attendance_map,
                         average_grade=average_grade,
                         recent_grades=recent_grades,
                         pending_assignments=pending_assignments,
                         upcoming_exams=upcoming_exams,
                         upcoming_events=upcoming_events)


@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        flash('Access denied. Parent privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get parent profile and children
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    # Initialize stats
    children_count = 0
    attendance_avg = None
    fees_due = None
    unread_messages_count = 0
    
    if parent:
        # Get children count
        children = Student.query.filter_by(parent_id=parent.id).all()
        children_count = len(children)
        
        # Calculate average attendance across all children
        if children:
            from app.models.models import Attendance
            from datetime import datetime, timedelta
            
            total_attendance = 0
            children_with_attendance = 0
            
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
                
                if records:
                    present_count = sum(1 for r in records if r.status == 'present')
                    child_attendance = (present_count / len(records)) * 100
                    total_attendance += child_attendance
                    children_with_attendance += 1
            
            if children_with_attendance > 0:
                attendance_avg = round(total_attendance / children_with_attendance, 1)
        
        # Calculate total fees due
        from app.models.models import FeePayment
        total_fees = 0
        for child in children:
            # Sum unpaid or pending fees
            unpaid_fees = FeePayment.query.filter(
                FeePayment.student_id == child.id,
                FeePayment.status.in_(['pending', 'failed'])
            ).all()
            total_fees += sum(fee.amount for fee in unpaid_fees)
        
        if total_fees > 0:
            fees_due = total_fees
    
    # Get unread messages count
    unread_messages_count = Message.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()

    # Fetch recent announcements targeted to parents or all
    try:
        from app.models.models import Announcement
        announcements = Announcement.query.filter(
            (Announcement.audience_role == 'all') | (Announcement.audience_role == 'parent')
        ).order_by(Announcement.created_at.desc()).limit(5).all()
    except Exception:
        announcements = []
    
    return render_template('parent/dashboard.html', 
                         parent=parent, 
                         announcements=announcements,
                         children_count=children_count,
                         attendance_avg=attendance_avg,
                         fees_due=fees_due,
                         unread_messages_count=unread_messages_count)

@app.route('/logout')
@login_required
def logout():
    # Clear session and log out
    session.clear()
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# Create database tables and a default admin user if none exists
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create default admin if no users exist
        if User.query.count() == 0:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                full_name='Admin User',
                email='admin@school.com',
                password=hashed_password,
                role='admin',
                created_at=datetime.now()
            )
            db.session.add(admin)
            db.session.flush()
            
            admin_profile = Admin(user_id=admin.id, admin_id='ADM001', department='Administration')
            db.session.add(admin_profile)
            db.session.commit()

# Create tables on startup
create_tables()

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    try:
        if current_user.is_authenticated:
            room = f'user_{current_user.id}'
            join_room(room)
            emit('joined', {'room': room})
    except Exception as e:
        print('Socket connect error:', e)

@socketio.on('disconnect')
def handle_disconnect():
    try:
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
    except Exception as e:
        print('Socket disconnect error:', e)

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room})

@socketio.on('send_message')
def handle_send_message(data):
    try:
        if not current_user.is_authenticated:
            return
        recipient_id = int(data.get('recipient_id'))
        content = (data.get('content') or '').strip()
        if not recipient_id or not content:
            return
        # Persist message
        msg = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            timestamp=datetime.now(),
            is_read=False
        )
        db.session.add(msg)
        db.session.commit()

        payload = {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'recipient_id': msg.recipient_id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%I:%M %p')
        }
        # Send to both sender and recipient rooms
        emit('new_message', payload, room=f'user_{current_user.id}')
        emit('new_message', payload, room=f'user_{recipient_id}')
    except Exception as e:
        print('Error sending message:', e)

# WebRTC signaling events
@socketio.on('call_offer')
def handle_call_offer(data):
    to_id = int(data.get('to'))
    emit('call_offer', {
        'from': current_user.id,
        'sdp': data.get('sdp'),
        'media': data.get('media')
    }, to=f'user_{to_id}')

@socketio.on('call_answer')
def handle_call_answer(data):
    to_id = int(data.get('to'))
    emit('call_answer', {
        'from': current_user.id,
        'sdp': data.get('sdp')
    }, to=f'user_{to_id}')

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    to_id = int(data.get('to'))
    emit('ice_candidate', {
        'from': current_user.id,
        'candidate': data.get('candidate')
    }, to=f'user_{to_id}')

@socketio.on('end_call')
def handle_end_call(data):
    to_id = int(data.get('to'))
    emit('end_call', {'from': current_user.id}, to=f'user_{to_id}')


if __name__ == '__main__':
    socketio.run(app, debug=True)