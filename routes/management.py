from flask import Blueprint, request, jsonify, session,redirect
from extensions import db
from models import Doctor, Patient, Appointment, MedicalRecord
from werkzeug.security import generate_password_hash
from datetime import date, datetime

management_bp = Blueprint('management_bp', __name__)


# ---- ADMIN CHECK HELPER ----
def is_admin():
    return session.get('admin') is True


# ---- DASHBOARD STATS ----
@management_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    total_doctors      = Doctor.query.count()
    total_patients     = Patient.query.count()
    today_appointments = Appointment.query.filter_by(date=date.today()).count()
    pending            = Appointment.query.filter_by(status='Booked').count()

    return jsonify({
        'total_doctors'     : total_doctors,
        'total_patients'    : total_patients,
        'today_appointments': today_appointments,
        'pending_approvals' : pending
    }), 200


# ---- GET ALL DOCTORS ----
@management_bp.route('/api/admin/doctors', methods=['GET'])
def get_all_doctors():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    doctors = Doctor.query.all()
    result  = []
    for d in doctors:
        result.append({
            'id'            : d.id,
            'name'          : d.name,
            'specialization': d.specialization,
            'department'    : d.department,
            'email'         : d.email,
            'working_days'  : d.working_days,
            'start_time'    : d.start_time,
            'end_time'      : d.end_time
        })
    return jsonify({'doctors': result}), 200


# ---- ADD DOCTOR ----
@management_bp.route('/api/admin/add-doctor', methods=['POST'])
def add_doctor():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    data = request.get_json()

    required = ['name', 'specialization', 'department', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    if Doctor.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    doctor = Doctor(
        name           = data['name'],
        specialization = data['specialization'],
        department     = data['department'],
        email          = data['email'],
        password       = generate_password_hash(data['password']),
        working_days   = data.get('working_days', ''),
        start_time     = data.get('start_time', ''),
        end_time       = data.get('end_time', '')
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor added successfully'}), 201


# ---- UPDATE DOCTOR ----
@management_bp.route('/api/admin/update-doctor/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    data = request.get_json()

    doctor.name           = data.get('name', doctor.name)
    doctor.specialization = data.get('specialization', doctor.specialization)
    doctor.department     = data.get('department', doctor.department)
    doctor.working_days   = data.get('working_days', doctor.working_days)
    doctor.start_time     = data.get('start_time', doctor.start_time)
    doctor.end_time       = data.get('end_time', doctor.end_time)

    if data.get('password'):
        doctor.password = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({'message': 'Doctor updated successfully'}), 200


# ---- DELETE DOCTOR ----
@management_bp.route('/api/admin/delete-doctor/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    db.session.delete(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor deleted successfully'}), 200


# ---- GET ALL APPOINTMENTS ----
@management_bp.route('/api/admin/appointments', methods=['GET'])
def get_all_appointments():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    status_filter = request.args.get('status')

    if status_filter and status_filter != 'all':
        appointments = Appointment.query.filter_by(
            status=status_filter
        ).order_by(Appointment.date.desc()).all()
    else:
        appointments = Appointment.query.order_by(
            Appointment.date.desc()
        ).all()

    result = []
    for a in appointments:
        patient = db.session.get(Patient, a.patient_id)
        doctor  = db.session.get(Doctor, a.doctor_id)
        result.append({
            'id'          : a.id,
            'patient_name': patient.name if patient else 'Unknown',
            'doctor_name' : doctor.name if doctor else 'Unknown',
            'department'  : doctor.department if doctor else 'Unknown',
            'date'        : str(a.date),
            'time_slot'   : a.time_slot,
            'status'      : a.status
        })

    return jsonify({'appointments': result}), 200


# ---- APPROVE APPOINTMENT ----
@management_bp.route('/api/admin/appointments/approve/<int:appt_id>', methods=['POST'])
def approve_appointment(appt_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appointment = db.session.get(Appointment, appt_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    appointment.status = 'Confirmed'
    db.session.commit()
    return jsonify({'message': 'Appointment confirmed'}), 200


# ---- CANCEL APPOINTMENT ----
@management_bp.route('/api/admin/appointments/cancel/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appointment = db.session.get(Appointment, appt_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    appointment.status = 'Cancelled'
    db.session.commit()
    return jsonify({'message': 'Appointment cancelled'}), 200


# ---- GET TODAY'S SCHEDULE ----
@management_bp.route('/api/admin/schedule/today', methods=['GET'])
def today_schedule():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appointments = Appointment.query.filter_by(
        date=date.today()
    ).order_by(Appointment.time_slot).all()

    result = []
    for a in appointments:
        patient = db.session.get(Patient, a.patient_id)
        doctor  = db.session.get(Doctor, a.doctor_id)
        result.append({
            'id'          : a.id,
            'patient_name': patient.name if patient else 'Unknown',
            'doctor_name' : doctor.name if doctor else 'Unknown',
            'department'  : doctor.department if doctor else 'Unknown',
            'time_slot'   : a.time_slot,
            'status'      : a.status
        })

    return jsonify({'schedule': result}), 200


# ---- GET ALL PATIENTS ----
@management_bp.route('/api/admin/patients', methods=['GET'])
def get_all_patients():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    patients = Patient.query.all()
    result   = []
    for p in patients:
        result.append({
            'id'   : p.id,
            'name' : p.name,
            'email': p.email,
            'phone': p.phone or ''
        })
    return jsonify({'patients': result}), 200

from flask import render_template


@management_bp.route('/api/admin/admitted-patients')
def get_admitted():
    if not is_admin():
        return jsonify({'message':'Admin login required'}),403
    records = MedicalRecord.query.filter_by(status='admitted').all()
    data=[]
    for r in records:
        patient=Patient.query.get(r.patient_id)
        doctor=Doctor.query.get(r.doctor_id)
        data.append({
            "name":patient.name,
            "age":'N/A',
            "doctor": doctor.name,
            "dept": doctor.department,
            "date": r.date.strftime('%Y-%m-%d'),
            "status": r.status
        })
    return jsonify(data)

@management_bp.route('/api/admin/operations')
def get_operations():
    if not is_admin():
        return jsonify({'message':'Admin login required'}),403
    appointments=Appointment.query.all()
    data=[]
    for a in appointments:
        patient = db.session.get(Patient, a.patient_id)  # ← fetch manually
        doctor = db.session.get(Doctor, a.doctor_id) 
        data.append({
            "name": patient.name if patient else 'Unknown',
            "doctor": doctor.name if doctor else 'Unknown',
            "dept": doctor.department if doctor else 'Unknown',
            "date": a.date.strftime('%Y-%m-%d'),
            "time": a.time_slot
        })
    return jsonify(data)
@management_bp.route('/api/admin/discharged-patients')
def get_discharged():
    if not is_admin():
        return jsonify({'message':'Admin login required'}),403
    discharge=MedicalRecord.query.filter_by(status='discharge').all()
    data=[]
    for r in discharge:
        patient=Patient.query.get(r.patient_id)
        doctor=Doctor.query.get(r.doctor_id)
        data.append({
            "name":patient.name,
            "age":'N/A',
            "doctor": doctor.name,
            "dept": doctor.department,
            "admitted_date": r.date.strftime('%Y-%m-%d'),
            "discharged_date": r.discharged_date.strftime('%Y-%m-%d')if r.discharged_date else 'N/A'
        })
    return jsonify(data)
# ---- ADMIN LOGOUT ----
@management_bp.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    session.clear()
    return jsonify({'message': 'Admin logged out'}), 200
