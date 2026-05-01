from flask import request, jsonify
from app import app, db
from models import Patient
from werkzeug.security import generate_password_hash, check_password_hash

# Register a new patient
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()   # get data sent from frontend

    # Check if email already exists
    existing = Patient.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'message': 'Email already registered'}), 400

    # Hash the password before saving
    hashed_password = generate_password_hash(data['password'])

    new_patient = Patient(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        phone=data.get('phone', '')
    )
    db.session.add(new_patient)
    db.session.commit()

    return jsonify({'message': 'Patient registered successfully!'}), 201
