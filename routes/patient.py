from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Doctor, Appointment, MedicalRecord, Patient,AdmittedPatient
from extensions import db
from datetime import datetime, timedelta, date
from groq import Groq
import json
import os
from utils.email import send_booking_email
patient_bp = Blueprint('patient_bp', __name__)


# ---- DASHBOARD ----
@patient_bp.route('/api/patient/dashboard', methods=['GET'])
@login_required
def dashboard():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    patient = Patient.query.get(current_user.id)

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(Appointment.date.desc()).limit(5).all()

    upcoming  = Appointment.query.filter_by(
        patient_id=current_user.id, status='Booked').count()
    completed = Appointment.query.filter_by(
        patient_id=current_user.id, status='Completed').count()
    pending   = Appointment.query.filter_by(
        patient_id=current_user.id, status='Pending').count()

    appt_list = []
    for a in appointments:
        doctor = Doctor.query.get(a.doctor_id)
        appt_list.append({
            'doctor_name'    : doctor.name,
            'specialization' : doctor.specialization,
            'date'           : str(a.date),
            'time_slot'      : a.time_slot,
            'status'         : a.status
        })

    return jsonify({
        'name'         : patient.name,
        'phone'        : patient.phone,
        'upcoming'     : upcoming,
        'completed'    : completed,
        'pending'      : pending,
        'appointments' : appt_list
    }), 200


# ---- GET ALL DOCTORS ----
@patient_bp.route('/api/doctors', methods=['GET'])
def get_doctors():
    department = request.args.get('department')

    if department:
        doctors = Doctor.query.filter_by(department=department).all()
    else:
        doctors = Doctor.query.all()

    result = []
    for doc in doctors:
        result.append({
            'id'            : doc.id,
            'name'          : doc.name,
            'specialization': doc.specialization,
            'department'    : doc.department,
            'working_days'  : doc.working_days,
            'start_time'    : doc.start_time,
            'end_time'      : doc.end_time
        })

    return jsonify({'doctors': result}), 200


# ---- GET AVAILABLE TIME SLOTS ----
@patient_bp.route('/api/slots', methods=['GET'])
def get_slots():
    doctor_id = request.args.get('doctor_id')
    date_str  = request.args.get('date')

    if not doctor_id or not date_str:
        return jsonify({'message': 'Doctor and date are required'}), 400

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    selected_date = datetime.strptime(date_str, '%Y-%m-%d')

    if selected_date.date() < datetime.today().date():
        return jsonify({'message': 'Cannot check slots for a past date'}), 400

    day_name = selected_date.strftime('%a')
    if doctor.working_days and day_name not in doctor.working_days.split(','):
        return jsonify({'message': 'Doctor not available on this day'}), 400

    all_slots    = generate_slots(doctor.start_time, doctor.end_time)
    booked       = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=selected_date.date()
    ).all()
    booked_slots = [appt.time_slot for appt in booked]

    slot_list = []
    for s in all_slots:
        slot_list.append({
            'time'   : s,
            'booked' : s in booked_slots
        })

    return jsonify({'slots': slot_list}), 200


# ---- BOOK APPOINTMENT ----
@patient_bp.route('/api/book', methods=['POST'])
@login_required
def book_appointment():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()

    if not data.get('doctor_id') or not data.get('date') or not data.get('time_slot'):
        return jsonify({'message': 'Doctor, date and time slot are required'}), 400

    selected_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

    if selected_date < datetime.today().date():
        return jsonify({'message': 'Cannot book on a past date'}), 400

    doctor   = Doctor.query.get(data['doctor_id'])
    day_name = selected_date.strftime('%a')

    if doctor.working_days and day_name not in doctor.working_days.split(','):
        return jsonify({'message': 'Doctor not available on this day'}), 400

    existing = Appointment.query.filter_by(
        doctor_id=data['doctor_id'],
        date=selected_date,
        time_slot=data['time_slot']
    ).first()

    if existing:
        return jsonify({'message': 'This slot is already booked'}), 400

    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=data['doctor_id'],
        date=selected_date,
        time_slot=data['time_slot'],
        status='Booked'
    )
    db.session.add(new_appointment)
    db.session.commit()

    try:
        send_booking_email(
            to_email       = current_user.email,
            patient_name   = current_user.name,
            doctor_name    = doctor.name,
            specialization = doctor.specialization,
            date           = str(selected_date),
            time_slot      = data['time_slot'],
            appointment_id = new_appointment.id
        )
        email_sent = True
    except:
        email_sent=False


    return jsonify({'message': 'Appointment booked successfully!',
                    'emaill_sent':email_sent}), 201


# ---- CANCEL APPOINTMENT ----
@patient_bp.route('/api/appointments/cancel/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointment = Appointment.query.get(appt_id)

    if not appointment or appointment.patient_id != current_user.id:
        return jsonify({'message': 'Appointment not found'}), 404

    if appointment.status == 'Cancelled':
        return jsonify({'message': 'Already cancelled'}), 400

    appointment.status = 'Cancelled'
    db.session.commit()
    return jsonify({'message': 'Appointment cancelled'}), 200


# ---- MY APPOINTMENTS ----
@patient_bp.route('/api/my-appointments', methods=['GET'])
@login_required
def my_appointments():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(Appointment.date.desc()).all()

    today    = date.today()
    upcoming = []
    past     = []

    for appt in appointments:
        doctor = Doctor.query.get(appt.doctor_id)
        item = {
            'appointment_id': appt.id,
            'doctor_name'   : doctor.name,
            'specialization': doctor.specialization,
            'department'    : doctor.department,
            'date'          : str(appt.date),
            'time_slot'     : appt.time_slot,
            'status'        : appt.status
        }
        if appt.date >= today and appt.status != 'Cancelled':
            upcoming.append(item)
        else:
            past.append(item)

    return jsonify({'upcoming': upcoming, 'past': past}), 200


# ---- MEDICAL HISTORY ----
@patient_bp.route('/api/my-history', methods=['GET'])
@login_required
def my_history():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    records = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(MedicalRecord.date.desc()).all()

    result = []
    for record in records:
        doctor = Doctor.query.get(record.doctor_id)
        result.append({
            'date'          : str(record.date),
            'doctor_name'   : doctor.name if doctor else 'Unknown',
            'specialization': doctor.specialization if doctor else 'Unknown',
            'department'    : doctor.department if doctor else 'Unknown',
            'diagnosis'     : record.diagnosis,
            'report'        : record.report
        })

    return jsonify({'medical_history': result}), 200


# ---- REPORTS ----
@patient_bp.route('/api/my-report', methods=['GET'])
@login_required
def my_report():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    records = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(MedicalRecord.date.desc()).all()

    if not records:
        return jsonify({'reports': []}), 200

    result = []
    for record in records:
        doctor = Doctor.query.get(record.doctor_id)
        result.append({
            'date'       : str(record.date),
            'doctor_name': doctor.name if doctor else 'Unknown',
            'department' : doctor.department if doctor else 'Unknown',
            'diagnosis'  : record.diagnosis,
            'report'     : record.report
        })

    return jsonify({'reports': result}), 200


# ---- SLOT GENERATOR ----
def generate_slots(start_time, end_time):
    slots = []
    if not start_time or not end_time:
        return slots

    start   = datetime.strptime(start_time, '%H:%M')
    end     = datetime.strptime(end_time, '%H:%M')
    current = start

    while current < end:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=15)

    return slots


# @patient_bp.route('/api/symptom-check', methods=['POST'])
# def symptom_check():
#     data = request.get_json()
#     symptoms = data.get('symptoms', '')

#     if not symptoms:
#         return jsonify({'message': 'Please describe your symptoms'}), 400

#     client = anthropic.Anthropic()

#     message = client.messages.create(
#         model="claude-opus-4-20250514",
#         max_tokens=1024,
#         messages=[
#             {
#                 "role": "user",
#                 "content": f"""You are a medical assistant helping patients find the right hospital department.
                
# The patient describes: {symptoms}

# Based on these symptoms, suggest the most appropriate department from this list only:
# cardiology, neurology, orthopedics, pediatrics, dermatology, ent, ophthalmology, gynecology, psychiatry, radiology, oncology, emergency

# Respond in this exact JSON format:
# {{
#     "department": "department_name",
#     "reason": "brief explanation why this department",
#     "urgency": "low/medium/high",
#     "advice": "one sentence of general advice"
# }}

# Only respond with the JSON, nothing else."""
#             }
#         ]
#     )

#     import json
#     result = json.loads(message.content[0].text)
#     return jsonify(result), 200

#temp
# import os

# @patient_bp.route('/api/symptom-check', methods=['POST'])
# def symptom_check():
#     data = request.get_json()
#     symptoms = data.get('symptoms', '')

#     if not symptoms:
#         return jsonify({'message': 'Please describe your symptoms'}), 400

#     api_key = os.environ.get('ANTHROPIC_API_KEY')
#     print(f"API Key found: {api_key is not None}")   # ← shows in terminal

#     client = anthropic.Anthropic(api_key=api_key)
#     ...


@patient_bp.route('/api/symptom-check', methods=['POST'])
def symptom_check():
    data     = request.get_json()
    symptoms = data.get('symptoms', '')

    if not symptoms:
        return jsonify({'message': 'Please describe your symptoms'}), 400

    try:
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"""You are a medical assistant helping patients
find the right hospital department.

Patient description: {symptoms}

Suggest the most appropriate department from this list only:
cardiology, neurology, orthopedics, pediatrics, dermatology,
ent, ophthalmology, gynecology, psychiatry, general medicine, emergency

Respond in this exact JSON format only, no other text:
{{
    "department": "department_name",
    "reason": "brief explanation why this department",
    "urgency": "low/medium/high",
    "advice": "one sentence of general advice",
    "warnings": ["warning sign 1", "warning sign 2"]
}}

warnings should list 2-3 symptoms that would require emergency care."""
            }]
        )

        result = json.loads(response.choices[0].message.content)
        return jsonify(result), 200

    except Exception as e:
        print(f"API error: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500@patient_bp.route('/api/symptom-check', methods=['POST'])
def symptom_check():
    data     = request.get_json()
    symptoms = data.get('symptoms', '')

    if not symptoms:
        return jsonify({'message': 'Please describe your symptoms'}), 400

    # ---- DEBUG: print key status ----
    api_key = os.environ.get('GROQ_API_KEY')
    print(f"GROQ API Key found: {api_key is not None}")
    print(f"Symptoms received: {symptoms}")

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"""You are a medical assistant helping patients
find the right hospital department.

Patient description: {symptoms}

Suggest the most appropriate department from this list only:
cardiology, neurology, orthopedics, pediatrics, dermatology,
ent, ophthalmology, gynecology, psychiatry, general medicine, emergency

Respond in this exact JSON format only, no other text:
{{
    "department": "department_name",
    "reason": "brief explanation why this department",
    "urgency": "low/medium/high",
    "advice": "one sentence of general advice"
}}"""
            }]
        )

        print(f"Raw AI response: {response.choices[0].message.content}")

        result = json.loads(response.choices[0].message.content)
        return jsonify(result), 200

    except Exception as e:
        print(f"GROQ ERROR: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500
    
    # ---- PATIENT ADMISSIONS ----
@patient_bp.route('/api/patient/admissions', methods=['GET'])
@login_required
def patient_admissions():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    admissions = AdmittedPatient.query.filter_by(
        patient_id=current_user.id
    ).order_by(AdmittedPatient.admitted_date.desc()).all()

    result = []
    for a in admissions:
        doctor = db.session.get(Doctor, a.doctor_id)
        result.append({
            'id'            : a.id,
            'doctor_name'   : doctor.name       if doctor else 'Unknown',
            'department'    : doctor.department  if doctor else 'Unknown',
            'admission_type': a.admission_type   or 'observation',
            'admitted_date' : str(a.admitted_date),
            'discharged_date': str(a.discharged_date) if a.discharged_date else None,
            'bed_number'    : a.bed_number,
            'diagnosis'     : a.diagnosis        or '—',
            'status'        : a.status
        })

    return jsonify({'admissions': result}), 200

