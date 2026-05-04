from flask import Flask
from flask_login import LoginManager
from extensions import db   
from routes.auth import auth     
from routes.doctor import doctor_bp
from flask import Flask, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aspataal'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

db.init_app(app)                 
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'message': 'Please log in to access this page.'}), 401

app.register_blueprint(auth) 
app.register_blueprint(doctor_bp)                  

@login_manager.user_loader
def load_user(user_id):
    from models import Patient, Doctor
    if user_id.startswith('patient_'):
        return Patient.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('doctor_'):
        return Doctor.query.get(int(user_id.split('_')[1]))
    return None

@app.route('/')
def home():
    return "Hospital System is running!"

with app.app_context():
    from models import Patient, Doctor, Appointment, MedicalRecord
    db.create_all()
    print("Database created!")

if __name__ == '__main__':
    app.run(debug=True)