from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Doctor, Appointment, MedicalRecord
from extensions import db
from datetime import datetime, timedelta

patient_bp = Blueprint('patient_bp', __name__)


# to get doctors by department (called while selecting department by patient)
@patient_bp.route('/api/doctors', methods=['GET'])
def get_doctors():
    department = request.args.get('department')  # e.g. /doctors?department=cardiology

    if not department:
        return jsonify({'message': 'Department is required'}), 400

    doctors = Doctor.query.filter_by(department=department).all()

    result = []
    for doc in doctors:
        result.append({
            'id': doc.id,
            'name': doc.name,
            'specialization': doc.specialization,
            'department': doc.department
        })

    return jsonify({'doctors': result}), 200


# to get available time slots
@patient_bp.route('/api/slots', methods=['GET'])
def get_slots():
    doctor_id = request.args.get('doctor_id')
    date_str = request.args.get('date')           # format: YYYY-MM-DD

    if not doctor_id or not date_str:
        return jsonify({'message': 'Doctor and date are required'}), 400

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    # check doctor's working day
    selected_date = datetime.strptime(date_str, '%Y-%m-%d')

    if selected_date.date() < datetime.today().date():
        return jsonify({'message': 'Cannot check slots for a past date'}), 400

    day_name = selected_date.strftime('%a')        # e.g. Mon, Tue, Wed

    if doctor.working_days and day_name not in doctor.working_days.split(','):
        return jsonify({'message': 'Doctor is not available on this day'}), 400

    # generate 15-minute time slots
    slots = generate_slots(doctor.start_time, doctor.end_time)

    # check already booked slots for the day and remove them
    booked = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=selected_date.date()
    ).all()
    booked_slots = [appt.time_slot for appt in booked]

    available_slots = [s for s in slots if s not in booked_slots]

    return jsonify({'available_slots': available_slots}), 200


# booking appointment
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
        return jsonify({'message': 'Cannot book an appointment on a past date'}), 400

    doctor = Doctor.query.get(data['doctor_id'])
    day_name = selected_date.strftime('%a')        # Mon, Tue etc
    if doctor.working_days and day_name not in doctor.working_days.split(','):
        return jsonify({'message': 'Doctor is not available on this day'}), 400

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

    return jsonify({'message': 'Appointment booked successfully!'}), 201


# viewing appointments
@patient_bp.route('/api/my-appointments', methods=['GET'])
@login_required
def my_appointments():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).all()

    result = []
    for appt in appointments:
        doctor = Doctor.query.get(appt.doctor_id)
        result.append({
            'appointment_id': appt.id,
            'doctor_name': doctor.name,
            'department': doctor.department,
            'date': str(appt.date),
            'time_slot': appt.time_slot,
            'status': appt.status
        })

    return jsonify({'appointments': result}), 200


# 15 minute time slots generation
def generate_slots(start_time, end_time):
    slots = []
    if not start_time or not end_time:
        return slots

    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')

    current = start
    while current < end:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=15)

    return slots


# view medical history
@patient_bp.route('/api/my-history', methods=['GET'])
@login_required
def my_history():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    records = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).all()

    if not records:
        return jsonify({'message': 'No medical history found'}), 404

    result = []
    for record in records:
        doctor = Doctor.query.get(record.doctor_id)
        result.append({
            'date': str(record.date),
            'doctor_name': doctor.name if doctor else 'Unknown',
            'department': doctor.department if doctor else 'Unknown',
            'diagnosis': record.diagnosis,
            'report': record.report
        })

    return jsonify({'medical_history': result}), 200


# view latest report
@patient_bp.route('/api/my-report', methods=['GET'])
@login_required
def my_report():
    if not current_user.get_id().startswith('patient_'):
        return jsonify({'message': 'Unauthorized'}), 403

    # Get most recent record only
    latest_record = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(MedicalRecord.date.desc()).first()

    if not latest_record:
        return jsonify({'message': 'No reports found'}), 404

    doctor = Doctor.query.get(latest_record.doctor_id)

    return jsonify({
        'latest_report': {
            'date': str(latest_record.date),
            'doctor_name': doctor.name if doctor else 'Unknown',
            'department': doctor.department if doctor else 'Unknown',
            'diagnosis': latest_record.diagnosis,
            'report': latest_record.report
        }
    }), 200