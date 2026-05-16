from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))                  

from flask import Flask
from flask_login import LoginManager
from extensions import db   
from routes.auth import auth     
from routes.doctor import doctor_bp
from flask import Flask, jsonify
from routes.patient import patient_bp
from routes.management import management_bp
from routes.pages import pages_bp           
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aspataal'
app.config['SESSION_COOKIE_SECURE']   = False     
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['ADMIN_USERNAME'] = 'admin'
app.config['ADMIN_PASSWORD'] = 'admin123'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 0
app.config['SESSION_TYPE']              = 'filesystem'
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USERNAME'] = 'bhusalsneha07@gmail.com'  
app.config['MAIL_PASSWORD'] = 'gefg actd wkla abxx'     
app.config['MAIL_FROM']     = 'bhusalsneha2062@gmail.com'
api_key = os.getenv("GROQ_API_KEY")

db.init_app(app)                 
login_manager = LoginManager(app)
login_manager.login_view = 'auth.patient_login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'message': 'Please log in to access this page.'}), 401

app.register_blueprint(auth) 
app.register_blueprint(doctor_bp)  
app.register_blueprint(patient_bp)
app.register_blueprint(management_bp)  
app.register_blueprint(pages_bp)              


@login_manager.user_loader
def load_user(user_id):
    from models import Patient, Doctor
    if user_id.startswith('patient_'):
        return Patient.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('doctor_'):
        return Doctor.query.get(int(user_id.split('_')[1]))
    return None


migrate = Migrate(app, db)

with app.app_context():
    from models import Patient, Doctor, Appointment, MedicalRecord,Bed

    db.create_all()
    if Bed.query.count() == 0:
        for i in range(1, 201):
            bed = Bed(bed_number=i, is_occupied=False)
            db.session.add(bed)
        db.session.commit()
        print("Beds created!")
        print("Database created!")

if __name__ == '__main__':
    app.run(debug=True)
