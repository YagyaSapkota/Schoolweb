# This file makes the models directory a Python package

# Import db first
from app.models.models import db

# Import all models
from app.models.models import User, Admin, Teacher, Student, Parent, Class, Attendance, Exam, ExamResult, FeePayment, Subject
from app.models.message import Message

# Export everything
__all__ = ['db', 'User', 'Admin', 'Teacher', 'Student', 'Parent', 'Class', 'Attendance', 'Exam', 'ExamResult', 'FeePayment', 'Subject', 'Message']