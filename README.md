# EduSync - School Management System

A comprehensive Flask-based School Management System designed for modern educational institutions. EduSync provides role-based access for administrators, teachers, students, and parents with  academic tracking, and resource management capabilities.

## ✨ Key Features

### 🔐 Authentication & Authorization
- Secure user authentication with role-based access control (Admin, Teacher, Student, Parent)
- Persistent sessions with Flask-Login (30-day remember me)
- Password hashing with Flask-Bcrypt
- CSRF protection on all forms

### 📊 Academic Management
- **4-Term Grading System**: Track student performance across Term 1, Term 2, Term 3, and Final Term
- **Exam Scheduling**: Teachers can create and manage exams for their subjects
- **Grade Entry**: Teachers can enter and update grades for exams they've created
- **Assignment Management**: Create, distribute, and track student assignments
- **Attendance Tracking**: Daily attendance monitoring with reporting capabilities

### 👥 Role-Based Dashboards
- **Admin Dashboard**: User management, system-wide announcements, resource oversight
- **Teacher Dashboard**: Class management, exam creation, grade entry, resource uploads
- **Student Dashboard**: View grades, assignments, attendance, and announcements
- **Parent Dashboard**: Monitor child's academic progress, grades, and attendance

### 💬 Communication
- **Announcements**: System-wide and role-specific announcements
- **Notifications**: Enhanced flash alerts with modern UI

### 🎨 Modern UI/UX
- **Dark Theme**: Fully functional dark mode across all dashboards
- **Fixed Footer**: Always visible footer on all pages
- **Smooth Animations**: Modern micro-animations for better user experience

### 📁 Resource Management
- **File Uploads**: Support for PDF, PNG, and JPEG files only
- **Resource Library**: Organized storage and retrieval of learning materials
- **View Resources**: In-browser viewing of uploaded resources

## 🛠️ Tech Stack

**Backend:**
- Python 3.10+ with Flask framework
- Flask-SQLAlchemy (ORM)
- Flask-Login (Session management)
- Flask-Bcrypt (Password hashing)
- Flask-WTF (Form handling & CSRF protection)
- Flask-Mail (Email functionality)
- Flask-Session (Server-side sessions)

**Database:**
- SQLite (default for development)
- Easily configurable for PostgreSQL/MySQL in production

**Frontend:**
- Jinja2 templating engine
- Custom CSS with dark theme support
- Vanilla JavaScript for interactivity

See `requirements.txt` for complete dependency list.

## Prerequisites

- Python 3.10+ (3.8+ may work, but 3.10+ is recommended)
- Git (optional)

## Quickstart

1. Clone the repository:

```bash
git clone <repo-url> .
```

2. Create and activate a virtual environment:

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the application:

- Open `app.py` and change `app.config['SECRET_KEY']` to a secure value (use environment variable in production)
- The app uses `sqlite:///school_management.db` by default. Change `SQLALCHEMY_DATABASE_URI` for production databases

5. Start the application:

```bash
python app.py
```

The development server will start with Socket.IO support. By default, the project creates database tables and a default admin account (email: `admin@school.com`, password: `admin123`) when first run.

## 📁 Project Structure

```
EduSync/
├── app/                          # Main application package
│   ├── controllers/              # Flask blueprints for features
│   │   ├── user_controller.py    # Authentication & user management
│   │   ├── teacher_controller.py # Teacher dashboard & features
│   │   ├── student_controller.py # Student dashboard & grades
│   │   ├── parent_controller.py  # Parent dashboard & monitoring
│   │   ├── class_controller.py   # Class scheduling & management
│   │   ├── attendance_controller.py # Attendance tracking
│   │   ├── exam_controller.py    # Exam creation & management
│   │   ├── message_controller.py # Real-time messaging
│   │   ├── assignment_controller.py # Assignment handling
│   │   ├── announcement_controller.py # Announcements
│   │   └── common_controller.py  # Shared resources & utilities
│   ├── models/                   # Database models
│   │   ├── models.py             # Core models (User, Class, Exam, etc.)
│   │   └── message.py            # Message model for real-time chat
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── admin/              # Admin dashboard templates
│   │   ├── teacher/            # Teacher dashboard templates
│   │   ├── student/            # Student dashboard templates
│   │   ├── parent/             # Parent dashboard templates
│   │   ├── common/             # Shared templates
│   │   └── base.html           # Base template with navigation
│   └── static/                 # Static assets
│       ├── css/                # Stylesheets (including dark theme)
│       ├── js/                 # JavaScript files
│       ├── images/             # Image assets
│       └── uploads/           # User-uploaded files
├── instance/                    # Instance-specific files
│   ├── school_management.db    # SQLite database (created on first run)
│   └── sessions/               # Server-side session storage
├── app.py                       # Application entry point & Socket.IO setup
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔒 Environment & Production Notes

- **Security**: Never commit secrets to version control. Use environment variables for `SECRET_KEY` and database credentials
- **Database**: For production, migrate from SQLite to PostgreSQL or MySQL for better performance and concurrency
- **File Uploads**: Only PDF, PNG, and JPEG files are allowed. File type validation is enforced both client-side and server-side
- **HTTPS**: Always use HTTPS in production to protect user credentials and session data

## 🔑 Default Credentials

On first run, the system creates a default admin account:

- **Email**: `admin@school.com`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change the default admin password immediately after first login!

## 🔄 Database Reset

To reset the database and start fresh:

1. Stop the application
2. Delete `instance/school_management.db`
3. Restart the application - tables and default admin will be recreated

## 🐛 Troubleshooting

**Dependencies won't install:**
- Ensure Python 3.10+ is installed: `python --version`
- Update pip: `python -m pip install --upgrade pip`
- Try installing in a fresh virtual environment

**Socket.IO connection issues:**
- Check firewall settings to allow WebSocket connections
- Ensure eventlet is installed: `pip install eventlet`

**Database errors:**
- Delete `instance/school_management.db` and restart to recreate tables
- Check file permissions on the database file

**CSRF token errors:**
- Clear browser cache and cookies
- Ensure `SECRET_KEY` is properly configured
- Check that forms include `{{ form.csrf_token }}` or `{{ csrf_token() }}`

**Theme not loading:**
- Clear browser cache
- Check browser console for CSS loading errors
- Verify static files are being served correctly

## 📝 License

This project is currently unlicensed. Please add a `LICENSE` file to specify terms of use and distribution.

---

**EduSync** - Empowering education through technology 🎓
