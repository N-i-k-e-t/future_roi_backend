#!/usr/bin/env python3
"""
Seed data script for FutureROI application
Run this script to populate the database with sample data
"""

import os
import sys
import json
from datetime import datetime, date

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.user import db, User
from src.models.zone import Zone, Event
from src.models.investment import Product, Goal, Plan, Projection, AssetSnapshot

def seed_zones():
    """Seed zones data"""
    zones_data = [
        {
            'country_code': 'IN',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'name': 'Mumbai Metropolitan Region',
            'rank': 1,
            'outlook': 'HIGH',
            'confidence': 'HIGH',
            'lat': 19.0760,
            'lng': 72.8777
        },
        {
            'country_code': 'IN',
            'state': 'Delhi',
            'city': 'New Delhi',
            'name': 'National Capital Region',
            'rank': 2,
            'outlook': 'HIGH',
            'confidence': 'HIGH',
            'lat': 28.6139,
            'lng': 77.2090
        },
        {
            'country_code': 'IN',
            'state': 'Karnataka',
            'city': 'Bangalore',
            'name': 'Bangalore IT Hub',
            'rank': 3,
            'outlook': 'HIGH',
            'confidence': 'MEDIUM',
            'lat': 12.9716,
            'lng': 77.5946
        },
        {
            'country_code': 'IN',
            'state': 'Maharashtra',
            'city': 'Pune',
            'name': 'Pune Metropolitan Area',
            'rank': 4,
            'outlook': 'MODERATE',
            'confidence': 'HIGH',
            'lat': 18.5204,
            'lng': 73.8567
        },
        {
            'country_code': 'IN',
            'state': 'Telangana',
            'city': 'Hyderabad',
            'name': 'Hyderabad HITEC City',
            'rank': 5,
            'outlook': 'MODERATE',
            'confidence': 'MEDIUM',
            'lat': 17.3850,
            'lng': 78.4867
        },
        {
            'country_code': 'IN',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'name': 'Chennai IT Corridor',
            'rank': 6,
            'outlook': 'MODERATE',
            'confidence': 'MEDIUM',
            'lat': 13.0827,
            'lng': 80.2707
        },
        {
            'country_code': 'IN',
            'state': 'Gujarat',
            'city': 'Ahmedabad',
            'name': 'Ahmedabad Business District',
            'rank': 7,
            'outlook': 'MODERATE',
            'confidence': 'MEDIUM',
            'lat': 23.0225,
            'lng': 72.5714
        },
        {
            'country_code': 'IN',
            'state': 'West Bengal',
            'city': 'Kolkata',
            'name': 'Kolkata Metropolitan Area',
            'rank': 8,
            'outlook': 'LOW',
            'confidence': 'MEDIUM',
            'lat': 22.5726,
            'lng': 88.3639
        },
        {
            'country_code': 'IN',
            'state': 'Madhya Pradesh',
            'city': 'Indore',
            'name': 'Indore Commercial Hub',
            'rank': 9,
            'outlook': 'MODERATE',
            'confidence': 'LOW',
            'lat': 22.7196,
            'lng': 75.8577
        },
        {
            'country_code': 'IN',
            'state': 'Gujarat',
            'city': 'Surat',
            'name': 'Surat Diamond City',
            'rank': 10,
            'outlook': 'LOW',
            'confidence': 'LOW',
            'lat': 21.1702,
            'lng': 72.8311
        }
    ]
    
    for zone_data in zones_data:
        existing_zone = Zone.query.filter_by(name=zone_data['name']).first()
        if not existing_zone:
            zone = Zone(**zone_data)
            db.session.add(zone)
    
    db.session.commit()
    print("✓ Zones seeded successfully")

def seed_events():
    """Seed events data"""
    # Get zones for foreign key references
    mumbai = Zone.query.filter_by(city='Mumbai').first()
    delhi = Zone.query.filter_by(city='New Delhi').first()
    bangalore = Zone.query.filter_by(city='Bangalore').first()
    pune = Zone.query.filter_by(city='Pune').first()
    
    events_data = [
        {
            'zone_id': mumbai.id if mumbai else 1,
            'type': 'INFRA',
            'title': 'Mumbai Metro Line 3 Completion',
            'description': 'Completion of the Colaba-Bandra-SEEPZ metro line expected to boost property values',
            'start_date': date(2024, 12, 31),
            'expected_impact_bps': 250,
            'evidence_links': json.dumps(['https://example.com/mumbai-metro']),
            'status': 'IN_PROGRESS'
        },
        {
            'zone_id': mumbai.id if mumbai else 1,
            'type': 'BUSINESS',
            'title': 'Bandra-Kurla Complex Expansion',
            'description': 'Major financial district expansion with new office towers',
            'start_date': date(2025, 6, 30),
            'expected_impact_bps': 180,
            'evidence_links': json.dumps(['https://example.com/bkc-expansion']),
            'status': 'ANNOUNCED'
        },
        {
            'zone_id': delhi.id if delhi else 2,
            'type': 'POLICY',
            'title': 'Delhi Master Plan 2041',
            'description': 'New master plan focusing on sustainable development and affordable housing',
            'start_date': date(2024, 4, 1),
            'expected_impact_bps': 200,
            'evidence_links': json.dumps(['https://example.com/delhi-master-plan']),
            'status': 'IN_PROGRESS'
        },
        {
            'zone_id': bangalore.id if bangalore else 3,
            'type': 'INFRA',
            'title': 'Bangalore Airport Metro Connection',
            'description': 'Direct metro connectivity to Kempegowda International Airport',
            'start_date': date(2025, 3, 31),
            'expected_impact_bps': 220,
            'evidence_links': json.dumps(['https://example.com/bangalore-airport-metro']),
            'status': 'IN_PROGRESS'
        },
        {
            'zone_id': pune.id if pune else 4,
            'type': 'MEGA_EVENT',
            'title': 'Pune Smart City Project Phase 2',
            'description': 'Implementation of smart infrastructure and digital governance',
            'start_date': date(2024, 8, 15),
            'expected_impact_bps': 150,
            'evidence_links': json.dumps(['https://example.com/pune-smart-city']),
            'status': 'IN_PROGRESS'
        }
    ]
    
    for event_data in events_data:
        existing_event = Event.query.filter_by(title=event_data['title']).first()
        if not existing_event:
            event = Event(**event_data)
            db.session.add(event)
    
    db.session.commit()
    print("✓ Events seeded successfully")

def seed_products():
    """Seed investment products data"""
    products_data = [
        {
            'name': 'Nifty 50 Index Fund',
            'category': 'INDEX_FUND',
            'risk': 'MEDIUM',
            'expense_ratio': 0.10,
            'provider': 'HDFC Mutual Fund',
            'min_sip': 500,
            'rationale_tags': json.dumps(['Low cost', 'Diversified', 'Market returns'])
        },
        {
            'name': 'Sensex Index Fund',
            'category': 'INDEX_FUND',
            'risk': 'MEDIUM',
            'expense_ratio': 0.12,
            'provider': 'SBI Mutual Fund',
            'min_sip': 500,
            'rationale_tags': json.dumps(['Blue chip exposure', 'Low cost', 'Passive investing'])
        },
        {
            'name': 'Flexi Cap Growth Fund',
            'category': 'FLEXI_CAP',
            'risk': 'HIGH',
            'expense_ratio': 1.25,
            'provider': 'ICICI Prudential',
            'min_sip': 1000,
            'rationale_tags': json.dumps(['Active management', 'Multi-cap exposure', 'Growth focused'])
        },
        {
            'name': 'Large Cap Equity Fund',
            'category': 'FLEXI_CAP',
            'risk': 'MEDIUM',
            'expense_ratio': 1.50,
            'provider': 'Axis Mutual Fund',
            'min_sip': 1000,
            'rationale_tags': json.dumps(['Large cap focus', 'Stable returns', 'Lower volatility'])
        },
        {
            'name': 'Corporate Bond Fund',
            'category': 'DEBT_FUND',
            'risk': 'LOW',
            'expense_ratio': 0.75,
            'provider': 'Franklin Templeton',
            'min_sip': 1000,
            'rationale_tags': json.dumps(['Fixed income', 'Capital preservation', 'Regular income'])
        },
        {
            'name': 'Government Securities Fund',
            'category': 'DEBT_FUND',
            'risk': 'LOW',
            'expense_ratio': 0.50,
            'provider': 'UTI Mutual Fund',
            'min_sip': 500,
            'rationale_tags': json.dumps(['Government backing', 'Safe investment', 'Tax benefits'])
        },
        {
            'name': 'Real Estate Investment Trust',
            'category': 'REIT',
            'risk': 'MEDIUM',
            'expense_ratio': 0.25,
            'provider': 'Embassy REIT',
            'min_sip': 2000,
            'rationale_tags': json.dumps(['Real estate exposure', 'Regular dividends', 'Inflation hedge'])
        },
        {
            'name': 'Gold ETF',
            'category': 'GOLD_ETF',
            'risk': 'MEDIUM',
            'expense_ratio': 0.50,
            'provider': 'HDFC Gold ETF',
            'min_sip': 1000,
            'rationale_tags': json.dumps(['Gold exposure', 'Inflation protection', 'Portfolio diversification'])
        },
        {
            'name': 'Government Bond 10Y',
            'category': 'BOND',
            'risk': 'LOW',
            'expense_ratio': 0.25,
            'provider': 'Government of India',
            'min_sip': 1000,
            'rationale_tags': json.dumps(['Government guarantee', 'Fixed returns', 'Long term'])
        }
    ]
    
    for product_data in products_data:
        existing_product = Product.query.filter_by(name=product_data['name']).first()
        if not existing_product:
            product = Product(**product_data)
            db.session.add(product)
    
    db.session.commit()
    print("✓ Products seeded successfully")

def seed_sample_users():
    """Seed sample users for testing"""
    users_data = [
        {
            'username': 'demo_user',
            'email': 'demo@futureroi.com',
            'name': 'Demo User',
            'city': 'Mumbai',
            'risk_profile': 'MODERATE',
            'monthly_income': 75000,
            'monthly_expenses': 45000,
            'emis': 15000,
            'onboarding_complete': True
        },
        {
            'username': 'test_conservative',
            'email': 'conservative@futureroi.com',
            'name': 'Conservative Investor',
            'city': 'Delhi',
            'risk_profile': 'CONSERVATIVE',
            'monthly_income': 50000,
            'monthly_expenses': 35000,
            'emis': 8000,
            'onboarding_complete': True
        },
        {
            'username': 'test_growth',
            'email': 'growth@futureroi.com',
            'name': 'Growth Investor',
            'city': 'Bangalore',
            'risk_profile': 'GROWTH',
            'monthly_income': 120000,
            'monthly_expenses': 60000,
            'emis': 25000,
            'onboarding_complete': True
        }
    ]
    
    for user_data in users_data:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(**user_data)
            db.session.add(user)
    
    db.session.commit()
    print("✓ Sample users seeded successfully")

def seed_sample_assets():
    """Seed sample asset snapshots"""
    demo_user = User.query.filter_by(username='demo_user').first()
    conservative_user = User.query.filter_by(username='test_conservative').first()
    growth_user = User.query.filter_by(username='test_growth').first()
    
    if demo_user:
        asset_snapshot = AssetSnapshot(
            user_id=demo_user.id,
            savings=500000,
            mf=300000,
            stocks=200000,
            gold=100000,
            epf=400000,
            real_estate=2000000,
            liabilities=800000
        )
        db.session.add(asset_snapshot)
    
    if conservative_user:
        asset_snapshot = AssetSnapshot(
            user_id=conservative_user.id,
            savings=300000,
            mf=150000,
            stocks=50000,
            gold=100000,
            epf=200000,
            real_estate=1200000,
            liabilities=400000
        )
        db.session.add(asset_snapshot)
    
    if growth_user:
        asset_snapshot = AssetSnapshot(
            user_id=growth_user.id,
            savings=200000,
            mf=800000,
            stocks=600000,
            gold=50000,
            epf=300000,
            real_estate=3000000,
            liabilities=1200000
        )
        db.session.add(asset_snapshot)
    
    db.session.commit()
    print("✓ Sample assets seeded successfully")

def seed_sample_goals():
    """Seed sample goals"""
    demo_user = User.query.filter_by(username='demo_user').first()
    mumbai_zone = Zone.query.filter_by(city='Mumbai').first()
    
    if demo_user and mumbai_zone:
        goals_data = [
            {
                'user_id': demo_user.id,
                'zone_id': mumbai_zone.id,
                'type': 'HOME',
                'target_amount': 5000000,
                'horizon_months': 120
            },
            {
                'user_id': demo_user.id,
                'type': 'RETIREMENT',
                'target_amount': 10000000,
                'horizon_months': 300
            },
            {
                'user_id': demo_user.id,
                'type': 'EMERGENCY',
                'target_amount': 500000,
                'horizon_months': 12
            }
        ]
        
        for goal_data in goals_data:
            goal = Goal(**goal_data)
            db.session.add(goal)
    
    db.session.commit()
    print("✓ Sample goals seeded successfully")

def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Seed data
        seed_zones()
        seed_events()
        seed_products()
        seed_sample_users()
        seed_sample_assets()
        seed_sample_goals()
        
        print("\n🎉 Database seeding completed successfully!")
        print("\nSample data includes:")
        print("- 10 zones (Mumbai, Delhi, Bangalore, etc.)")
        print("- 5 events (infrastructure and policy updates)")
        print("- 9 investment products (index funds, mutual funds, etc.)")
        print("- 3 sample users with different risk profiles")
        print("- Asset snapshots and goals for testing")
        print("\nYou can now start the Flask application and test the APIs!")

if __name__ == '__main__':
    main()

