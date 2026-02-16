from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    verified = db.Column(db.Boolean, default=False)

    otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)

    # 🔐 Hash password
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # 🔎 Check password
    def check_password(self, password):
        return check_password_hash(self.password, password)

    # 🔢 Generate OTP (valid for 5 minutes)
    def generate_otp(self):
        from random import randint
        self.otp = str(randint(100000, 999999))
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=5)

    # ⏰ Verify OTP
    def verify_otp(self, input_otp):
        if self.otp != input_otp:
            return False

        if datetime.utcnow() > self.otp_expiry:
            return False

        self.verified = True
        self.otp = None
        self.otp_expiry = None
        return True
