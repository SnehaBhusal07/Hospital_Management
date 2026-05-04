from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import Doctor, Appointment, Patient, MedicalRecord
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash

doctor_bp = Blueprint('doctor_bp', __name__)


# doctor login
@doctor_bp.route('/doctor/login', methods=['POST'])
def doctor_login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    doctor = Doctor.query.filter_by(email=data['email']).first()

    if not doctor or not check_password_hash(doctor.password, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    login_user(doctor)

    return jsonify({
        'message': 'Doctor login successful!',
        'doctor': {
            'id': doctor.id,
            'name': doctor.name,
            'specialization': doctor.specialization,
            'email': doctor.email
        }
    }), 200


# doctor logout
@doctor_bp.route('/doctor/logout', methods=['POST'])
@login_required
def doctor_logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully!'}), 200


# viewing scheduled patients
@doctor_bp.route('/doctor/appointments', methods=['GET'])
@login_required
def view_appointments():
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).all()

    result = []
    for appt in appointments:
        patient = Patient.query.get(appt.patient_id)
        result.append({
            'appointment_id': appt.id,
            'patient_name': patient.name,
            'patient_email': patient.email,
            'date': str(appt.date),
            'time_slot': appt.time_slot,
            'status': appt.status
        })

    return jsonify({'appointments': result}), 200


# view patient history
@doctor_bp.route('/doctor/patient/<int:patient_id>/history', methods=['GET'])
@login_required
def patient_history(patient_id):
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()

    result = []
    for record in records:
        result.append({
            'date': str(record.date),
            'diagnosis': record.diagnosis,
            'report': record.report
        })

    return jsonify({'history': result}), 200


# updating patient report
@doctor_bp.route('/doctor/patient/<int:patient_id>/update', methods=['POST'])
@login_required
def update_patient(patient_id):
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()

    new_record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=current_user.id,
        diagnosis=data.get('diagnosis', ''),
        report=data.get('report', '')
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({'message': 'Patient record updated successfully!'}), 201