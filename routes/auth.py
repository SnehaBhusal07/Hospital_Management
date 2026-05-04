from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required
from extensions import db
from models import Patient
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

# registraton
@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Name, email and password are required'}), 400

    existing = Patient.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'message': 'Email already registered'}), 400

    hashed_password = generate_password_hash(data['password'])

    new_patient = Patient(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        phone=data.get('phone', '')
    )
    db.session.add(new_patient)
    db.session.commit()

    return jsonify({'message': 'Registered successfully!'}), 201


# login
@auth.route('/login', methods=['POST'])
def login():
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
            'id': patient.id,
            'name': patient.name,
            'email': patient.email
        }
    }), 200


# logout
@auth.route('/logout', methods=['POST'])
@login_required                   
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully!'}), 200


# to check who is logged in
@auth.route('/me', methods=['GET'])
@login_required
def me():
    from flask_login import current_user
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email
    }), 200