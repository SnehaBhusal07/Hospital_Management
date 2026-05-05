from flask import Blueprint, request, jsonify, session, current_app
from models import Doctor, Appointment, Patient
from extensions import db
from werkzeug.security import generate_password_hash
from functools import wraps

management_bp = Blueprint('management_bp', __name__)


# checks if admin is logged in
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'message': 'Admin login required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# admin login
@management_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    if (data['username'] == current_app.config['ADMIN_USERNAME'] and
            data['password'] == current_app.config['ADMIN_PASSWORD']):
        session['is_admin'] = True
        return jsonify({'message': 'Admin login successful!'}), 200

    return jsonify({'message': 'Invalid admin credentials'}), 401


# admin logout
@management_bp.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    session.pop('is_admin', None)
    return jsonify({'message': 'Admin logged out successfully!'}), 200


# add doctor
@management_bp.route('/admin/add-doctor', methods=['POST'])
@admin_required
def add_doctor():
    data = request.get_json()

    required = ['name', 'specialization', 'department', 'email', 'password',
                'working_days', 'start_time', 'end_time']
    for field in required:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    existing = Doctor.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'message': 'Doctor with this email already exists'}), 400

    new_doctor = Doctor(
        name=data['name'],
        specialization=data['specialization'],
        department=data['department'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        working_days=data['working_days'],    # e.g. "Mon,Tue,Wed,Thu,Fri"
        start_time=data['start_time'],        # e.g. "09:00"
        end_time=data['end_time']             # e.g. "17:00"
    )
    db.session.add(new_doctor)
    db.session.commit()

    return jsonify({'message': 'Doctor added successfully!'}), 201


# remove doctor
@management_bp.route('/admin/remove-doctor/<int:doctor_id>', methods=['DELETE'])
@admin_required
def remove_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    # remove doctor's appointments first
    Appointment.query.filter_by(doctor_id=doctor_id).delete()
    db.session.delete(doctor)
    db.session.commit()

    return jsonify({'message': 'Doctor removed successfully!'}), 200


# view all doctors
@management_bp.route('/admin/doctors', methods=['GET'])
@admin_required
def view_doctors():
    doctors = Doctor.query.all()

    result = []
    for doc in doctors:
        result.append({
            'id': doc.id,
            'name': doc.name,
            'specialization': doc.specialization,
            'department': doc.department,
            'email': doc.email,
            'working_days': doc.working_days,
            'start_time': doc.start_time,
            'end_time': doc.end_time
        })

    return jsonify({'doctors': result}), 200


# update doctor schedule
@management_bp.route('/admin/update-doctor/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    data = request.get_json()


    if data.get('working_days'):
        doctor.working_days = data['working_days']
    if data.get('start_time'):
        doctor.start_time = data['start_time']
    if data.get('end_time'):
        doctor.end_time = data['end_time']
    if data.get('specialization'):
        doctor.specialization = data['specialization']
    if data.get('department'):
        doctor.department = data['department']

    db.session.commit()

    return jsonify({'message': 'Doctor updated successfully!'}), 200


# view all appointments
@management_bp.route('/admin/appointments', methods=['GET'])
@admin_required
def view_appointments():
    appointments = Appointment.query.all()

    result = []
    for appt in appointments:
        patient = Patient.query.get(appt.patient_id)
        doctor = Doctor.query.get(appt.doctor_id)
        result.append({
            'appointment_id': appt.id,
            'patient_name': patient.name if patient else 'Unknown',
            'doctor_name': doctor.name if doctor else 'Unknown',
            'department': doctor.department if doctor else 'Unknown',
            'date': str(appt.date),
            'time_slot': appt.time_slot,
            'status': appt.status
        })

    return jsonify({'appointments': result}), 200


# view all patients
@management_bp.route('/admin/patients', methods=['GET'])
@admin_required
def view_patients():
    patients = Patient.query.all()

    result = []
    for p in patients:
        result.append({
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'phone': p.phone
        })

    return jsonify({'patients': result}), 200

# view single doctor
@management_bp.route('/admin/doctors/<int:doctor_id>', methods=['GET'])
@admin_required
def view_single_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    return jsonify({
        'id': doctor.id,
        'name': doctor.name,
        'specialization': doctor.specialization,
        'department': doctor.department,
        'email': doctor.email,
        'working_days': doctor.working_days,
        'start_time': doctor.start_time,
        'end_time': doctor.end_time
    }), 200