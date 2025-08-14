from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    risk_profile = db.Column(db.String(20), default='MODERATE')  # CONSERVATIVE, MODERATE, GROWTH
    monthly_income = db.Column(db.Integer, nullable=True)
    monthly_expenses = db.Column(db.Integer, nullable=True)
    emis = db.Column(db.Integer, nullable=True)
    onboarding_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    asset_snapshots = db.relationship('AssetSnapshot', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    plans = db.relationship('Plan', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'city': self.city,
            'risk_profile': self.risk_profile,
            'monthly_income': self.monthly_income,
            'monthly_expenses': self.monthly_expenses,
            'emis': self.emis,
            'onboarding_complete': self.onboarding_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
