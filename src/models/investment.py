from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime
import json

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # INDEX_FUND, FLEXI_CAP, DEBT_FUND, REIT, GOLD_ETF, BOND
    risk = db.Column(db.String(20), nullable=False)  # LOW, MEDIUM, HIGH
    expense_ratio = db.Column(db.Float, nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    min_sip = db.Column(db.Integer, nullable=False)
    rationale_tags = db.Column(db.Text)  # JSON array of tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        rationale_tags = []
        if self.rationale_tags:
            try:
                rationale_tags = json.loads(self.rationale_tags)
            except:
                rationale_tags = []
                
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'risk': self.risk,
            'expense_ratio': self.expense_ratio,
            'provider': self.provider,
            'min_sip': self.min_sip,
            'rationale_tags': rationale_tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # HOME, EDUCATION, RETIREMENT, EMERGENCY, WEALTH
    target_amount = db.Column(db.Integer, nullable=False)
    horizon_months = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plans = db.relationship('Plan', backref='goal', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Goal {self.type} - {self.target_amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'zone_id': self.zone_id,
            'type': self.type,
            'target_amount': self.target_amount,
            'horizon_months': self.horizon_months,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Plan(db.Model):
    __tablename__ = 'plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    allocation_json = db.Column(db.Text, nullable=False)  # JSON allocation data
    monthly_amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projections = db.relationship('Projection', backref='plan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Plan {self.id} - {self.monthly_amount}>'

    def to_dict(self):
        allocation = {}
        if self.allocation_json:
            try:
                allocation = json.loads(self.allocation_json)
            except:
                allocation = {}
                
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'allocation': allocation,
            'monthly_amount': self.monthly_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Projection(db.Model):
    __tablename__ = 'projections'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    base_coverage_min = db.Column(db.Integer, nullable=False)
    base_coverage_max = db.Column(db.Integer, nullable=False)
    stress_coverage_min = db.Column(db.Integer, nullable=False)
    stress_coverage_max = db.Column(db.Integer, nullable=False)
    assumptions = db.Column(db.Text)  # JSON array of assumptions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Projection {self.id}>'

    def to_dict(self):
        assumptions = []
        if self.assumptions:
            try:
                assumptions = json.loads(self.assumptions)
            except:
                assumptions = []
                
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'base_coverage_min': self.base_coverage_min,
            'base_coverage_max': self.base_coverage_max,
            'stress_coverage_min': self.stress_coverage_min,
            'stress_coverage_max': self.stress_coverage_max,
            'assumptions': assumptions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AssetSnapshot(db.Model):
    __tablename__ = 'asset_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    savings = db.Column(db.Integer, default=0)
    mf = db.Column(db.Integer, default=0)  # Mutual Funds
    stocks = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=0)
    epf = db.Column(db.Integer, default=0)  # Employee Provident Fund
    real_estate = db.Column(db.Integer, default=0)
    liabilities = db.Column(db.Integer, default=0)
    as_of_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AssetSnapshot {self.user_id} - {self.as_of_date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'savings': self.savings,
            'mf': self.mf,
            'stocks': self.stocks,
            'gold': self.gold,
            'epf': self.epf,
            'real_estate': self.real_estate,
            'liabilities': self.liabilities,
            'as_of_date': self.as_of_date.isoformat() if self.as_of_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

