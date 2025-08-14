from flask import Blueprint, request, jsonify
from src.models.zone import Zone, Event
from src.models.user import db
import openai
import os

zones_bp = Blueprint('zones', __name__)

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

@zones_bp.route('/zones', methods=['GET'])
def get_zones():
    """Get all zones with optional city filter"""
    try:
        city = request.args.get('city')
        
        if city:
            zones = Zone.query.filter(Zone.city.ilike(f'%{city}%')).all()
        else:
            zones = Zone.query.all()
        
        zones_data = []
        for zone in zones:
            zone_dict = zone.to_dict()
            # Add events count
            zone_dict['events_count'] = len(zone.events)
            zones_data.append(zone_dict)
        
        return jsonify({
            'success': True,
            'data': zones_data,
            'count': len(zones_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@zones_bp.route('/zones/<int:zone_id>', methods=['GET'])
def get_zone_details(zone_id):
    """Get detailed information about a specific zone"""
    try:
        zone = Zone.query.get_or_404(zone_id)
        zone_data = zone.to_dict()
        
        # Get events for this zone
        events = Event.query.filter_by(zone_id=zone_id).all()
        zone_data['events'] = [event.to_dict() for event in events]
        
        return jsonify({
            'success': True,
            'data': zone_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@zones_bp.route('/zones/<int:zone_id>/roi', methods=['GET'])
def calculate_zone_roi(zone_id):
    """Calculate ROI for a specific zone"""
    try:
        zone = Zone.query.get_or_404(zone_id)
        
        # Get query parameters
        investment_amount = request.args.get('amount', type=int, default=1000000)  # Default 10 lakh
        investment_type = request.args.get('type', default='real_estate')  # real_estate, stocks, sip, etc.
        time_horizon = request.args.get('horizon', type=int, default=60)  # months
        
        # Calculate base ROI based on zone data
        roi_data = calculate_roi_for_zone(zone, investment_amount, investment_type, time_horizon)
        
        return jsonify({
            'success': True,
            'data': roi_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@zones_bp.route('/zones/<int:zone_id>/analyze', methods=['POST'])
def analyze_zone_with_ai(zone_id):
    """Use AI to analyze zone investment potential"""
    try:
        zone = Zone.query.get_or_404(zone_id)
        events = Event.query.filter_by(zone_id=zone_id).all()
        
        # Prepare data for AI analysis
        zone_context = {
            'name': zone.name,
            'rank': zone.rank,
            'outlook': zone.outlook,
            'confidence': zone.confidence,
            'events': [{'title': e.title, 'type': e.type, 'impact_bps': e.expected_impact_bps} for e in events]
        }
        
        # Get AI analysis
        analysis = get_ai_zone_analysis(zone_context)
        
        return jsonify({
            'success': True,
            'data': {
                'zone': zone.to_dict(),
                'analysis': analysis
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@zones_bp.route('/zones/search', methods=['GET'])
def search_zones():
    """Search zones by name or city"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', type=int, default=10)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400
        
        zones = Zone.query.filter(
            db.or_(
                Zone.name.ilike(f'%{query}%'),
                Zone.city.ilike(f'%{query}%'),
                Zone.state.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        zones_data = [zone.to_dict() for zone in zones]
        
        return jsonify({
            'success': True,
            'data': zones_data,
            'count': len(zones_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_roi_for_zone(zone, investment_amount, investment_type, time_horizon):
    """Calculate ROI based on zone characteristics"""
    
    # Base ROI rates based on zone outlook and confidence
    base_rates = {
        'HIGH': {'real_estate': 12, 'stocks': 15, 'sip': 12, 'bonds': 7},
        'MODERATE': {'real_estate': 8, 'stocks': 12, 'sip': 10, 'bonds': 6},
        'LOW': {'real_estate': 5, 'stocks': 8, 'sip': 8, 'bonds': 5}
    }
    
    # Confidence multipliers
    confidence_multipliers = {
        'HIGH': 1.0,
        'MEDIUM': 0.9,
        'LOW': 0.8
    }
    
    base_rate = base_rates.get(zone.outlook, base_rates['MODERATE']).get(investment_type, 8)
    confidence_multiplier = confidence_multipliers.get(zone.confidence, 0.9)
    
    # Apply confidence multiplier
    adjusted_rate = base_rate * confidence_multiplier
    
    # Calculate future value using compound interest
    monthly_rate = adjusted_rate / 100 / 12
    future_value = investment_amount * ((1 + monthly_rate) ** time_horizon)
    
    # Calculate total returns
    total_returns = future_value - investment_amount
    roi_percentage = (total_returns / investment_amount) * 100
    
    # Calculate stress test scenarios
    stress_scenarios = {
        'optimistic': {
            'rate': adjusted_rate * 1.2,
            'future_value': investment_amount * ((1 + (adjusted_rate * 1.2) / 100 / 12) ** time_horizon)
        },
        'pessimistic': {
            'rate': adjusted_rate * 0.7,
            'future_value': investment_amount * ((1 + (adjusted_rate * 0.7) / 100 / 12) ** time_horizon)
        }
    }
    
    return {
        'zone_id': zone.id,
        'zone_name': zone.name,
        'investment_amount': investment_amount,
        'investment_type': investment_type,
        'time_horizon_months': time_horizon,
        'base_rate_percent': round(adjusted_rate, 2),
        'future_value': round(future_value, 2),
        'total_returns': round(total_returns, 2),
        'roi_percentage': round(roi_percentage, 2),
        'stress_scenarios': {
            'optimistic': {
                'rate_percent': round(stress_scenarios['optimistic']['rate'], 2),
                'future_value': round(stress_scenarios['optimistic']['future_value'], 2),
                'roi_percentage': round(((stress_scenarios['optimistic']['future_value'] - investment_amount) / investment_amount) * 100, 2)
            },
            'pessimistic': {
                'rate_percent': round(stress_scenarios['pessimistic']['rate'], 2),
                'future_value': round(stress_scenarios['pessimistic']['future_value'], 2),
                'roi_percentage': round(((stress_scenarios['pessimistic']['future_value'] - investment_amount) / investment_amount) * 100, 2)
            }
        }
    }

def get_ai_zone_analysis(zone_context):
    """Get AI analysis of zone investment potential"""
    try:
        if not openai.api_key:
            return {
                'growth_drivers': ['Infrastructure development', 'Economic growth', 'Population increase'],
                'risk_factors': ['Market volatility', 'Regulatory changes'],
                'investment_suitability': {
                    'real_estate': 'Moderate',
                    'stocks': 'High',
                    'bonds': 'Low'
                },
                'confidence': 'Medium',
                'note': 'AI analysis unavailable - using default analysis'
            }
        
        prompt = f"""Analyze investment potential for {zone_context['name']}:
        Current rank: {zone_context['rank']}, Outlook: {zone_context['outlook']}, Confidence: {zone_context['confidence']}
        Recent events: {', '.join([e['title'] for e in zone_context['events'][:3]])}
        
        Provide:
        - 3 key growth drivers (brief points)
        - 2 main risk factors (brief points)
        - Investment suitability for real estate, stocks, and bonds (High/Medium/Low)
        Keep explanations simple and under 50 words each."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a conservative financial advisor providing investment analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Parse AI response (simplified - in production, use more robust parsing)
        ai_text = response.choices[0].message.content
        
        return {
            'analysis_text': ai_text,
            'confidence': zone_context['confidence'],
            'generated_by': 'AI',
            'timestamp': 'now'
        }
        
    except Exception as e:
        # Fallback analysis if AI fails
        return {
            'growth_drivers': ['Infrastructure development', 'Economic growth', 'Population increase'],
            'risk_factors': ['Market volatility', 'Regulatory changes'],
            'investment_suitability': {
                'real_estate': 'Moderate',
                'stocks': 'High',
                'bonds': 'Low'
            },
            'confidence': zone_context['confidence'],
            'note': f'AI analysis failed: {str(e)} - using fallback analysis'
        }

