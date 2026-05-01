from flask import Flask
from flask_login import LoginManager
from extensions import db        # ← from extensions, not flask_sqlalchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

db.init_app(app)                 # ← this line is important
login_manager = LoginManager(app)

@app.route('/')
def home():
    return "Hospital System is running!"

with app.app_context():
    from models import Patient, Doctor, Appointment, MedicalRecord
    db.create_all()
    print("Database created!")

if __name__ == '__main__':
    app.run(debug=True)