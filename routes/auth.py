from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Patient, Doctor
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


# ---- PATIENT REGISTER ----
@auth.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Name, email and password are required'}), 400

    if Patient.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    new_patient = Patient(
        name     = data['name'],
        email    = data['email'],
        password = generate_password_hash(data['password']),
        phone    = data.get('phone', '')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({'message': 'Registered successfully!'}), 201


# ---- PATIENT LOGIN ----
@auth.route('/api/patient/login', methods=['POST'])
def patient_login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    patient = Patient.query.filter_by(email=data['email']).first()

    if not patient or not check_password_hash(patient.password, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    login_user(patient)
    return jsonify({
        'message': 'Login successful!',
        'patient': {
            'id'   : patient.id,
            'name' : patient.name,
            'email': patient.email
        }
    }), 200


# ---- DOCTOR LOGIN ----
@auth.route('/api/doctor/login', methods=['POST'])
def doctor_login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    doctor = Doctor.query.filter_by(email=data['email']).first()

    if not doctor or not check_password_hash(doctor.password, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    login_user(doctor)
    return jsonify({
        'message': 'Login successful!',
        'doctor': {
            'id'            : doctor.id,
            'name'          : doctor.name,
            'email'         : doctor.email,
            'specialization': doctor.specialization
        }
    }), 200


# ---- ADMIN LOGIN ----
@auth.route('/api/admin/login', methods=['POST'])
def admin_login():
    from flask import current_app
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    if (data['username'] == current_app.config['ADMIN_USERNAME'] and
            data['password'] == current_app.config['ADMIN_PASSWORD']):

        # ---- THIS IS THE IMPORTANT PART ----
        session.permanent = True
        session['admin']  = True

        return jsonify({'message': 'Admin login successful!'}), 200

    return jsonify({'message': 'Invalid admin credentials'}), 401

# ---- LOGOUT (all roles) ----
@auth.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    session.clear()
    return jsonify({'message': 'Logged out successfully!'}), 200


# ---- CHECK SESSION ----
@auth.route('/api/check-session', methods=['GET'])
def check_session():
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        if user_id.startswith('patient_'):
            return jsonify({'role': 'patient', 'name': current_user.name}), 200
        elif user_id.startswith('doctor_'):
            return jsonify({'role': 'doctor', 'name': current_user.name}), 200
    if session.get('admin'):
        return jsonify({'role': 'admin', 'name': 'Admin'}), 200
    return jsonify({'role': None}), 200


# ---- GET CURRENT USER INFO ----
@auth.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'id'   : current_user.id,
        'name' : current_user.name,
        'email': current_user.email
    }), 200

