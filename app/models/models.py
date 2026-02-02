from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student, parent
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    admin = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")
    student = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    parent = db.relationship('Parent', backref='user', uselist=False, cascade="all, delete-orphan")
    
    # Message relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'

# Admin model
class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Admin {self.admin_id}>'

# Teacher model
class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.String(20), unique=True, nullable=False)
    subject = db.Column(db.String(50))
    qualification = db.Column(db.String(100))
    
    # Relationships
    classes = db.relationship('Class', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f'<Teacher {self.teacher_id}>'

# Student model
class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    roll_number = db.Column(db.String(20))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.String(200))
    
    # Relationships
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    exam_results = db.relationship('ExamResult', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.student_id}>'

# Parent model
class Parent(db.Model):
    __tablename__ = 'parents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    occupation = db.Column(db.String(50))
    
    # Relationships
    students = db.relationship('Student', backref='parent', lazy=True)
    
    def __repr__(self):
        return f'<Parent {self.parent_id}>'

# Class model
class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    
    # Relationships
    students = db.relationship('Student', backref='class', lazy=True)
    attendances = db.relationship('Attendance', backref='class', lazy=True)
    exams = db.relationship('Exam', backref='class', lazy=True)
    
    def __repr__(self):
        return f'<Class {self.name} {self.section}>'

# Attendance model
class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # present, absent, late
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Attendance {self.student_id} {self.date}>'

# Exam model
class Exam(db.Model):
    __tablename__ = 'exams'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # Unified from name/title
    exam_type = db.Column(db.String(50), nullable=False)  # midterm, final, quiz, etc.
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)  # Unified from date/exam_date
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer)
    total_marks = db.Column(db.Integer, nullable=False)
    passing_marks = db.Column(db.Integer)
    room = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    results = db.relationship('ExamResult', backref='exam', lazy=True)
    subject = db.relationship('Subject', backref='exams')
    # class relationship is handled by backref from Class model ('class')
    
    def __repr__(self):
        return f'<Exam {self.title}>'

# Exam Result model
class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<ExamResult {self.exam_id} {self.student_id}>'

# Fee Payment model
class FeePayment(db.Model):
    __tablename__ = 'fee_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='paid')  # paid, pending, failed
    
    # Relationship
    student = db.relationship('Student', backref='fee_payments')
    
    def __repr__(self):
        return f'<FeePayment {self.id} {self.student_id}>'

# Subject model
class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    
    # Relationships
    class_rel = db.relationship('Class', backref='subjects')
    teacher = db.relationship('Teacher', backref='subjects')
    
    def __repr__(self):
        return f'<Subject {self.name}>'

# Assignment model
class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    due_date = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    subject = db.relationship('Subject', backref='assignments', lazy=True)
    class_rel = db.relationship('Class', backref='assignments', lazy=True)

    def __repr__(self):
        return f'<Assignment {self.title}>'

# Announcement model
class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    audience_role = db.Column(db.String(20), default='all')  # all, admin, teacher, student, parent
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    class_rel = db.relationship('Class', backref='announcements', lazy=True)

    def __repr__(self):
        return f'<Announcement {self.title}>'



class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='enrollments')
    subject = db.relationship('Subject', backref='enrollments')
    
    def __repr__(self):
        return f'<StudentEnrollment student={self.student_id} subject={self.subject_id}>'

# Resource model
class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(300), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    class_rel = db.relationship('Class', backref='resources')
    uploader = db.relationship('User', backref='uploaded_resources')
    
    def __repr__(self):
        return f'<Resource {self.title}>'

# Timetable model
class Timetable(db.Model):
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False) # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(50))
    
    # Relationships
    class_rel = db.relationship('Class', backref='timetable_entries')
    subject = db.relationship('Subject', backref='timetable_entries')
    
    def __repr__(self):
        return f'<Timetable {self.class_id} {self.day_of_week} {self.start_time}>'