from flask import Blueprint, render_template

pages_bp = Blueprint('pages_bp', __name__)


@pages_bp.route('/appointments-monitor')
def appointments_monitor():
    return render_template('appointments-monitor.html')

@pages_bp.route('/book-appointment')
def book_appointments():
    return render_template('book-appointment.html')

@pages_bp.route('/daily-schedule')
def daily_schedule():
    return render_template('daily-schedule.html')

@pages_bp.route('/doctor-availability')
def doctor_availability():
    return render_template('doctor-availability.html')

@pages_bp.route('/doctors')
def doctors_page():
    return render_template('doctors.html')

@pages_bp.route('/find-doctors')
def find_doctors_page():
    return render_template('find-doctors.html')

@pages_bp.route('/')
def index():
    return render_template('index.html')

@pages_bp.route('/manage-doctors')
def manage_doctors():
    return render_template('manage-doctors.html')

@pages_bp.route('/management')
def management():
    return render_template('management.html')

@pages_bp.route('/medical-history')
def medical_history():
    return render_template('medical-history.html')

@pages_bp.route('/my-appointments')
def my_appointments():
    return render_template('my-appointments.html')

@pages_bp.route('/patients')
def patients_page():
    return render_template('patients.html')

@pages_bp.route('/patient-history')
def patient_history_page():
    return render_template('patient-history.html')

@pages_bp.route('/reports')
def reports_page():
    return render_template('reports.html')

@pages_bp.route('/schedule')
def schedule_page():
    return render_template('schedule.html')

@pages_bp.route('/update-diagnosis')
def update_diagnosis_page():
    return render_template('update-diagnosis.html')

@pages_bp.route('/system-settings')
def system_settings():
    return render_template('system-settings.html')