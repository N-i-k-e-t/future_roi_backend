from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime
import json

class Zone(db.Model):
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.String(2), default='IN', nullable=False)
    state = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    outlook = db.Column(db.String(20), nullable=False)  # LOW, MODERATE, HIGH
    confidence = db.Column(db.String(20), nullable=False)  # LOW, MEDIUM, HIGH
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='zone', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='zone', lazy=True)

    def __repr__(self):
        return f'<Zone {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'country_code': self.country_code,
            'state': self.state,
            'city': self.city,
            'name': self.name,
            'rank': self.rank,
            'outlook': self.outlook,
            'confidence': self.confidence,
            'lat': self.lat,
            'lng': self.lng,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # INFRA, POLICY, BUSINESS, DEMOGRAPHIC, MEGA_EVENT
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    expected_impact_bps = db.Column(db.Integer, nullable=False)  # basis points
    evidence_links = db.Column(db.Text)  # JSON array of links
    status = db.Column(db.String(20), default='ANNOUNCED')  # ANNOUNCED, IN_PROGRESS, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Event {self.title}>'

    def to_dict(self):
        evidence_links = []
        if self.evidence_links:
            try:
                evidence_links = json.loads(self.evidence_links)
            except:
                evidence_links = []
                
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expected_impact_bps': self.expected_impact_bps,
            'evidence_links': evidence_links,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

