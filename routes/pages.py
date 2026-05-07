from flask import Blueprint, render_template

pages_bp = Blueprint('pages_bp', __name__)


# ---- HOME ----
@pages_bp.route('/')
def index():
    return render_template('index.html')


# ---- PATIENT ----
@pages_bp.route('/patient/dashboard')
def patient_dashboard():
    return render_template('patients.html')

@pages_bp.route('/patient/find-doctors')
def find_doctors():
    return render_template('find-doctors.html')

@pages_bp.route('/patient/appointments')
def my_appointments():
    return render_template('my-appointments.html')

@pages_bp.route('/patient/medical-history')
def medical_history():
    return render_template('medical-history.html')

@pages_bp.route('/patient/reports')
def reports():
    return render_template('reports.html')

@pages_bp.route('/patient/book-appointment')
def book_appointment():
    return render_template('book-appointment.html')


# ---- DOCTOR ----
@pages_bp.route('/doctor/dashboard')
def doctor_dashboard():
    return render_template('doctors.html')

@pages_bp.route('/doctor/schedule')
def schedule():
    return render_template('schedule.html')

@pages_bp.route('/doctor/patient-history')
def patient_history():
    return render_template('patient-history.html')

@pages_bp.route('/doctor/update-diagnosis')
def update_diagnosis():
    return render_template('update-diagnosis.html')


# ---- MANAGEMENT ----
@pages_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('management.html')

@pages_bp.route('/admin/manage-doctors')
def admin_manage_doctors():
    return render_template('manage-doctors.html')

@pages_bp.route('/admin/appointments')
def admin_appointments():
    return render_template('appointments-monitor.html')

@pages_bp.route('/admin/availability')
def admin_availability():
    return render_template('doctor-availability.html')

@pages_bp.route('/admin/daily-schedule')
def admin_daily_schedule():
    return render_template('daily-schedule.html')

@pages_bp.route('/admin/manage-hospital')
def admin_manage_hospital():
    return render_template('admission.html')

@pages_bp.route('/admin/settings')
def admin_settings():
    return render_template('system-settings.html')

@pages_bp.route('/symptom-checker')
def symptom_checker():
    return render_template('symptom-checker.html')