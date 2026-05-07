from flask import Blueprint, request, jsonify
from flask_login import logout_user, login_required, current_user
from models import Doctor, Appointment, Patient, MedicalRecord
from extensions import db
from datetime import date, datetime

doctor_bp = Blueprint('doctor_bp', __name__)


# ---- GET DOCTOR INFO ----
@doctor_bp.route('/api/doctor/me', methods=['GET'])
@login_required
def doctor_me():
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    return jsonify({
        'id'            : current_user.id,
        'name'          : current_user.name,
        'specialization': current_user.specialization,
        'department'    : current_user.department,
        'email'         : current_user.email,
        'working_days'  : current_user.working_days,
        'start_time'    : current_user.start_time,
        'end_time'      : current_user.end_time
    }), 200


# ---- GET APPOINTMENTS (today by default) ----
@doctor_bp.route('/api/doctor/appointments', methods=['GET'])
@login_required
def view_appointments():
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    date_str = request.args.get('date')
    if date_str:
        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointments = Appointment.query.filter_by(
            doctor_id=current_user.id,
            date=filter_date
        ).order_by(Appointment.time_slot).all()
    else:

        appointments = Appointment.query.filter_by(
            doctor_id=current_user.id
        ).order_by(Appointment.date, Appointment.time_slot).all()


    result = []
    for appt in appointments:
        patient = db.session.get(Patient, appt.patient_id)
        result.append({
            'appointment_id': appt.id,
            'patient_id'    : patient.id,
            'patient_name'  : patient.name,
            'patient_phone' : patient.phone or '',
            'date'          : str(appt.date),
            'time_slot'     : appt.time_slot,
            'status'        : appt.status
        })

    return jsonify({'appointments': result}), 200


# ---- GET FULL SCHEDULE (all upcoming) ----
@doctor_bp.route('/api/doctor/schedule', methods=['GET'])
@login_required
def get_schedule():
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date >= date.today()
    ).order_by(Appointment.date, Appointment.time_slot).all()

    result = []
    for appt in appointments:
        patient = db.session.get(Patient, appt.patient_id)
        result.append({
            'appointment_id': appt.id,
            'patient_id'    : patient.id,
            'patient_name'  : patient.name,
            'date'          : str(appt.date),
            'time_slot'     : appt.time_slot,
            'status'        : appt.status
        })

    return jsonify({'schedule': result}), 200


# ---- UPDATE APPOINTMENT STATUS ----
@doctor_bp.route('/api/doctor/appointment/<int:appt_id>/status', methods=['POST'])
@login_required
def update_status(appt_id):
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or not data.get('status'):
        return jsonify({'message': 'Status is required'}), 400

    appt = db.session.get(Appointment, appt_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
    if appt.doctor_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403

    appt.status = data['status']
    db.session.commit()
    return jsonify({'message': 'Status updated'}), 200


# ---- GET PATIENT HISTORY ----
@doctor_bp.route('/api/doctor/patient/<int:patient_id>/history', methods=['GET'])
@login_required
def patient_history(patient_id):
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id,
        patient_id=patient_id
    ).order_by(Appointment.date.desc()).all()

    records = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.date.desc()).all()

    appt_list = []
    for a in appointments:
        appt_list.append({
            'id'       : a.id,
            'date'     : str(a.date),
            'time_slot': a.time_slot,
            'status'   : a.status
        })

    record_list = []
    for r in records:
        doctor = db.session.get(Doctor, r.doctor_id)
        record_list.append({
            'date'        : str(r.date),
            'doctor_name' : doctor.name if doctor else 'Unknown',
            'diagnosis'   : r.diagnosis,
            'prescription': r.prescription if hasattr(r, 'prescription') else '',
            'report'      : r.report,
            'status'      : r.status if hasattr(r, 'status') else 'Completed'
        })

    return jsonify({
        'patient': {
            'id'   : patient.id,
            'name' : patient.name,
            'phone': patient.phone or '',
            'email': patient.email
        },
        'appointments'   : appt_list,
        'medical_records': record_list
    }), 200


# ---- GET MY PATIENTS ----
@doctor_bp.route('/api/doctor/patients', methods=['GET'])
@login_required
def get_my_patients():
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).all()

    seen     = set()
    patients = []
    for a in appointments:
        if a.patient_id not in seen:
            seen.add(a.patient_id)
            patient = db.session.get(Patient, a.patient_id)
            if patient:
                patients.append({
                    'id'   : patient.id,
                    'name' : patient.name,
                    'phone': patient.phone or '',
                    'email': patient.email
                })

    return jsonify({'patients': patients}), 200


# ---- SAVE DIAGNOSIS ----
@doctor_bp.route('/api/doctor/patient/<int:patient_id>/update', methods=['POST'])
@login_required
def update_patient(patient_id):
    if not current_user.get_id().startswith('doctor_'):
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    if not data.get('diagnosis'):
        return jsonify({'message': 'Diagnosis is required'}), 400

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    new_record = MedicalRecord(
        patient_id   = patient_id,
        doctor_id    = current_user.id,
        diagnosis    = data.get('diagnosis', ''),
        prescription = data.get('prescription', ''),
        report       = data.get('report', ''),
        status       = data.get('status', 'Completed')
    )
    db.session.add(new_record)

    # mark appointment as completed if id provided
    if data.get('appointment_id'):
        appt = db.session.get(Appointment, data['appointment_id'])
        if appt and appt.doctor_id == current_user.id:
            appt.status = 'Completed'

    db.session.commit()
    return jsonify({'message': 'Patient record updated successfully!'}), 201