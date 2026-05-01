from extensions import db
from flask_login import UserMixin
from datetime import datetime

# PATIENT table
class Patient(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)   # stored as hash
    phone = db.Column(db.String(15))
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

# DOCTOR table
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    working_days = db.Column(db.String(100))   # e.g. "Mon,Tue,Wed"
    start_time = db.Column(db.String(10))       # e.g. "09:00"
    end_time = db.Column(db.String(10))         # e.g. "17:00"

# APPOINTMENT table
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)   # e.g. "10:00"
    status = db.Column(db.String(20), default='Booked')    # Booked, Completed, Cancelled

# MEDICAL RECORD table
class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    diagnosis = db.Column(db.Text)
    report = db.Column(db.Text)