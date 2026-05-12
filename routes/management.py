from flask import Blueprint, request, jsonify, session
from extensions import db
from models import Doctor, Patient, Appointment, MedicalRecord, AdmittedPatient, Bed
from werkzeug.security import generate_password_hash
from datetime import date, datetime
from flask import current_app

management_bp = Blueprint('management_bp', __name__)


# ---- ADMIN CHECK ----
def is_admin():
    return session.get('admin') is True


# ---- ADMIN LOGIN ----
@management_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    if (data['username'] == current_app.config['ADMIN_USERNAME'] and
            data['password'] == current_app.config['ADMIN_PASSWORD']):
        session['is_admin'] = True
        return jsonify({'message': 'Admin login successful!'}), 200

    return jsonify({'message': 'Invalid admin credentials'}), 401


# ---- ADMIN LOGOUT ----
@management_bp.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    session.clear()
    return jsonify({'message': 'Admin logged out'}), 200


# ---- DASHBOARD STATS ----
@management_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    total_doctors      = Doctor.query.count()
    total_patients     = Patient.query.count()
    today_appointments = Appointment.query.filter_by(
        date=date.today()
    ).count()
    pending = Appointment.query.filter_by(status='Booked').count()

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

    data     = request.get_json()
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
@management_bp.route('/api/admin/update-doctor/<int:doctor_id>',
                     methods=['PUT'])
def update_doctor(doctor_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    data = request.get_json()

    doctor.name           = data.get('name',           doctor.name)
    doctor.specialization = data.get('specialization', doctor.specialization)
    doctor.department     = data.get('department',     doctor.department)
    doctor.working_days   = data.get('working_days',   doctor.working_days)
    doctor.start_time     = data.get('start_time',     doctor.start_time)
    doctor.end_time       = data.get('end_time',       doctor.end_time)

    if data.get('password'):
        doctor.password = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({'message': 'Doctor updated successfully'}), 200


# ---- DELETE DOCTOR ----
@management_bp.route('/api/admin/delete-doctor/<int:doctor_id>',
                     methods=['DELETE'])
def delete_doctor(doctor_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    Appointment.query.filter_by(doctor_id=doctor_id).delete()
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor deleted successfully'}), 200


# ---- GET ALL APPOINTMENTS ----
@management_bp.route('/api/admin/appointments', methods=['GET'])
def get_all_appointments():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appointments = Appointment.query.order_by(
        Appointment.date.desc()
    ).all()

    result = []
    for a in appointments:
        patient = db.session.get(Patient, a.patient_id)
        doctor  = db.session.get(Doctor,  a.doctor_id)
        result.append({
            'id'          : a.id,
            'patient_name': patient.name       if patient else 'Unknown',
            'doctor_name' : doctor.name        if doctor  else 'Unknown',
            'department'  : doctor.department  if doctor  else 'Unknown',
            'date'        : str(a.date),
            'time_slot'   : a.time_slot,
            'status'      : a.status
        })
    return jsonify({'appointments': result}), 200


# ---- APPROVE APPOINTMENT ----
@management_bp.route('/api/admin/appointments/approve/<int:appt_id>',
                     methods=['POST'])
def approve_appointment(appt_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appt = db.session.get(Appointment, appt_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404

    appt.status = 'Confirmed'
    db.session.commit()
    return jsonify({'message': 'Appointment confirmed'}), 200


# ---- CANCEL APPOINTMENT ----
@management_bp.route('/api/admin/appointments/cancel/<int:appt_id>',
                     methods=['POST'])
def cancel_appointment(appt_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    appt = db.session.get(Appointment, appt_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404

    appt.status = 'Cancelled'
    db.session.commit()
    return jsonify({'message': 'Appointment cancelled'}), 200


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


# ---- TODAY'S SCHEDULE ----
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
        doctor  = db.session.get(Doctor,  a.doctor_id)
        result.append({
            'id'          : a.id,
            'patient_name': patient.name      if patient else 'Unknown',
            'doctor_name' : doctor.name       if doctor  else 'Unknown',
            'department'  : doctor.department if doctor  else 'Unknown',
            'time_slot'   : a.time_slot,
            'status'      : a.status
        })
    return jsonify({'schedule': result}), 200


# ---- MANAGEMENT STATS (beds + admissions) ----
@management_bp.route('/api/admin/management-stats', methods=['GET'])
def management_stats():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    total_beds     = Bed.query.count()
    available_beds = Bed.query.filter_by(is_occupied=False).count()
    admitted       = AdmittedPatient.query.filter_by(
                        status='Admitted').count()
    operations     = AdmittedPatient.query.filter_by(
                        admission_type='operation').count()

    return jsonify({
        'total_beds'    : total_beds,
        'available_beds': available_beds,
        'admitted'      : admitted,
        'operations'    : operations
    }), 200


# ---- ADMIT PATIENT ----
@management_bp.route('/api/admin/admit-patient', methods=['POST'])
def admit_patient():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    data = request.get_json()

    if not data.get('patient_id'):
        return jsonify({'message': 'Patient is required'}), 400
    if not data.get('doctor_id'):
        return jsonify({'message': 'Doctor is required'}), 400
    if not data.get('admitted_date'):
        return jsonify({'message': 'Admission date is required'}), 400

    # find available bed
    bed = Bed.query.filter_by(is_occupied=False).first()
    if not bed:
        return jsonify({'message': 'No beds available!'}), 400

    # parse date
    try:
        admitted_date = datetime.strptime(
            data['admitted_date'], '%Y-%m-%d'
        ).date()
    except:
        return jsonify({'message': 'Invalid date format'}), 400

    admission = AdmittedPatient(
        patient_id     = data['patient_id'],
        doctor_id      = data['doctor_id'],
        admission_type = data.get('admission_type', 'observation'),
        admitted_date  = admitted_date,
        diagnosis      = data.get('diagnosis', ''),
        status         = 'Admitted',
        bed_number     = bed.bed_number
    )

    bed.is_occupied = True
    db.session.add(admission)
    db.session.commit()

    return jsonify({
        'message'   : 'Patient admitted successfully!',
        'bed_number': bed.bed_number
    }), 201


# ---- GET ADMITTED PATIENTS ----
@management_bp.route('/api/admin/admitted-patients', methods=['GET'])
def admitted_patients():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    admissions = AdmittedPatient.query.filter_by(status='Admitted').all()
    result = []
    for a in admissions:
        result.append({
            'id'            : a.id,
            'name'          : a.patient.name,
            'doctor'        : a.doctor.name,
            'dept'          : a.doctor.department,
            'date'          : str(a.admitted_date),
            'status'        : a.status,
            'bed_number'    : a.bed_number,
            'admission_type': a.admission_type,
            'diagnosis'     : a.diagnosis
        })
    return jsonify(result), 200


# ---- GET DISCHARGED PATIENTS ----
@management_bp.route('/api/admin/discharged-patients', methods=['GET'])
def discharged_patients():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    admissions = AdmittedPatient.query.filter_by(status='Discharged').all()
    result = []
    for a in admissions:
        result.append({
            'id'             : a.id,
            'name'           : a.patient.name,
            'age'            : '—',
            'doctor'         : a.doctor.name,
            'department'     : a.doctor.department,
            'admitted_date'  : str(a.admitted_date),
            'discharged_date': str(a.discharged_date)
                if a.discharged_date else '—'
        })
    return jsonify(result), 200


# ---- DISCHARGE PATIENT ----
@management_bp.route('/api/admin/discharge/<int:admission_id>',
                     methods=['POST'])
def discharge_patient(admission_id):
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    admission = AdmittedPatient.query.get(admission_id)
    if not admission:
        return jsonify({'message': 'Admission not found'}), 404
    if admission.status == 'Discharged':
        return jsonify({'message': 'Already discharged'}), 400

    bed = Bed.query.filter_by(bed_number=admission.bed_number).first()
    if bed:
        bed.is_occupied = False

    admission.status          = 'Discharged'
    admission.discharged_date = date.today()
    db.session.commit()

    return jsonify({'message': 'Patient discharged successfully!'}), 200


# ---- GET OPERATIONS ----
@management_bp.route('/api/admin/operations', methods=['GET'])
def get_operations():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    ops    = AdmittedPatient.query.filter_by(
                admission_type='operation').all()
    result = []
    for op in ops:
        result.append({
            'name'  : op.patient.name,
            'doctor': op.doctor.name,
            'dept'  : op.doctor.department,
            'date'  : str(op.admitted_date),
            'time'  : '—',
            'status': op.status
        })
    return jsonify(result), 200


# ---- GET AVAILABLE BEDS ----
@management_bp.route('/api/admin/available-beds', methods=['GET'])
def available_beds():
    if not is_admin():
        return jsonify({'message': 'Admin login required'}), 403

    beds   = Bed.query.filter_by(is_occupied=False).all()
    result = []
    for bed in beds:
        result.append({'bed_id': bed.bed_number})
    return jsonify(result), 200

@management_bp.route('/api/admin/test-session')
def test_session():
    return jsonify({
        'session_contents': dict(session),
        'is_admin'        : session.get('is_admin')
    })