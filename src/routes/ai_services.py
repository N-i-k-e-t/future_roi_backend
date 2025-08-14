from flask import Blueprint, request, jsonify
from src.models.zone import Zone, Event
from src.models.investment import Product
from src.models.user import db
import openai
import os
import json
from datetime import datetime

ai_services_bp = Blueprint('ai_services', __name__)

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

@ai_services_bp.route('/ai/search', methods=['POST'])
def ai_enhanced_search():
    """AI-enhanced search that understands natural language queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Use AI to interpret the search query
        search_results = interpret_search_query(query)
        
        return jsonify({
            'success': True,
            'data': search_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_services_bp.route('/ai/location-analysis', methods=['POST'])
def location_based_analysis():
    """Analyze investment potential based on user's current location"""
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lng = data.get('longitude')
        radius = data.get('radius', 50)  # km
        
        if not lat or not lng:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
        
        # Find nearby zones
        nearby_zones = find_nearby_zones(lat, lng, radius)
        
        # Get AI analysis for the location
        location_analysis = get_location_investment_analysis(lat, lng, nearby_zones)
        
        return jsonify({
            'success': True,
            'data': {
                'location': {'latitude': lat, 'longitude': lng},
                'nearby_zones': nearby_zones,
                'analysis': location_analysis
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_services_bp.route('/ai/smart-recommendations', methods=['POST'])
def smart_investment_recommendations():
    """Get AI-powered investment recommendations based on multiple factors"""
    try:
        data = request.get_json()
        
        user_profile = data.get('user_profile', {})
        location_data = data.get('location_data', {})
        market_conditions = data.get('market_conditions', {})
        investment_goals = data.get('investment_goals', {})
        
        # Generate comprehensive recommendations
        recommendations = generate_smart_recommendations(
            user_profile, location_data, market_conditions, investment_goals
        )
        
        return jsonify({
            'success': True,
            'data': recommendations
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_services_bp.route('/ai/market-insights', methods=['GET'])
def get_market_insights():
    """Get AI-generated market insights and trends"""
    try:
        # Get recent events and zone data
        recent_events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
        top_zones = Zone.query.order_by(Zone.rank).limit(5).all()
        
        # Generate market insights
        insights = generate_market_insights(recent_events, top_zones)
        
        return jsonify({
            'success': True,
            'data': insights
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_services_bp.route('/ai/risk-assessment', methods=['POST'])
def assess_investment_risk():
    """Assess investment risk using AI analysis"""
    try:
        data = request.get_json()
        
        investment_type = data.get('investment_type', 'real_estate')
        amount = data.get('amount', 1000000)
        zone_id = data.get('zone_id')
        time_horizon = data.get('time_horizon', 60)
        user_profile = data.get('user_profile', {})
        
        # Get zone data if provided
        zone = None
        if zone_id:
            zone = Zone.query.get(zone_id)
        
        # Perform AI risk assessment
        risk_assessment = perform_risk_assessment(
            investment_type, amount, zone, time_horizon, user_profile
        )
        
        return jsonify({
            'success': True,
            'data': risk_assessment
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def interpret_search_query(query):
    """Use AI to interpret natural language search queries"""
    try:
        if not openai.api_key:
            return fallback_search_interpretation(query)
        
        prompt = f"""
        Interpret this real estate investment search query: "{query}"
        
        Extract:
        1. Location (city, state, or region)
        2. Investment type (real estate, stocks, mutual funds, etc.)
        3. Budget range if mentioned
        4. Time horizon if mentioned
        5. Risk preference if mentioned
        
        Return as JSON with keys: location, investment_type, budget_range, time_horizon, risk_preference
        If not mentioned, use null for that field.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial search assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        try:
            parsed_query = json.loads(ai_response)
        except:
            parsed_query = fallback_search_interpretation(query)
        
        # Search based on interpreted query
        search_results = execute_interpreted_search(parsed_query)
        
        return {
            'interpreted_query': parsed_query,
            'results': search_results,
            'generated_by': 'AI'
        }
        
    except Exception as e:
        return fallback_search_interpretation(query)

def fallback_search_interpretation(query):
    """Fallback search interpretation when AI is not available"""
    # Simple keyword-based interpretation
    query_lower = query.lower()
    
    # Extract location
    location = None
    cities = ['mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad', 'chennai', 'kolkata', 'ahmedabad']
    for city in cities:
        if city in query_lower:
            location = city.title()
            break
    
    # Extract investment type
    investment_type = 'real_estate'  # default
    if any(word in query_lower for word in ['stock', 'equity', 'share']):
        investment_type = 'stocks'
    elif any(word in query_lower for word in ['mutual fund', 'sip', 'mf']):
        investment_type = 'sip'
    
    # Search based on interpretation
    search_results = execute_interpreted_search({
        'location': location,
        'investment_type': investment_type,
        'budget_range': None,
        'time_horizon': None,
        'risk_preference': None
    })
    
    return {
        'interpreted_query': {
            'location': location,
            'investment_type': investment_type,
            'budget_range': None,
            'time_horizon': None,
            'risk_preference': None
        },
        'results': search_results,
        'generated_by': 'Fallback Algorithm'
    }

def execute_interpreted_search(parsed_query):
    """Execute search based on interpreted query"""
    results = []
    
    # Search zones based on location
    if parsed_query.get('location'):
        zones = Zone.query.filter(
            db.or_(
                Zone.city.ilike(f"%{parsed_query['location']}%"),
                Zone.name.ilike(f"%{parsed_query['location']}%")
            )
        ).all()
        
        for zone in zones:
            zone_data = zone.to_dict()
            zone_data['match_type'] = 'location'
            zone_data['relevance_score'] = 0.9
            results.append(zone_data)
    
    # If no location-specific results, return top zones
    if not results:
        top_zones = Zone.query.order_by(Zone.rank).limit(5).all()
        for zone in top_zones:
            zone_data = zone.to_dict()
            zone_data['match_type'] = 'general'
            zone_data['relevance_score'] = 0.7
            results.append(zone_data)
    
    return results

def find_nearby_zones(lat, lng, radius_km):
    """Find zones within a given radius of coordinates"""
    # Simple distance calculation (for demo purposes)
    # In production, use proper geospatial queries
    
    all_zones = Zone.query.all()
    nearby_zones = []
    
    for zone in all_zones:
        # Calculate approximate distance using Haversine formula (simplified)
        lat_diff = abs(zone.lat - lat)
        lng_diff = abs(zone.lng - lng)
        
        # Rough distance calculation (1 degree ≈ 111 km)
        distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
        
        if distance <= radius_km:
            zone_data = zone.to_dict()
            zone_data['distance_km'] = round(distance, 2)
            nearby_zones.append(zone_data)
    
    # Sort by distance
    nearby_zones.sort(key=lambda x: x['distance_km'])
    
    return nearby_zones

def get_location_investment_analysis(lat, lng, nearby_zones):
    """Get AI analysis for a specific location"""
    try:
        if not openai.api_key or not nearby_zones:
            return get_fallback_location_analysis(nearby_zones)
        
        zones_summary = []
        for zone in nearby_zones[:3]:  # Top 3 nearby zones
            zones_summary.append(f"{zone['name']} (Rank #{zone['rank']}, {zone['outlook']} outlook)")
        
        prompt = f"""
        Analyze investment potential for location at {lat}, {lng}.
        Nearby investment zones: {', '.join(zones_summary)}
        
        Provide:
        1. Overall location assessment (2-3 sentences)
        2. Best investment opportunities in the area
        3. Key factors to consider
        4. Risk factors
        
        Keep response concise and practical.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a real estate investment analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return {
            'analysis': response.choices[0].message.content,
            'generated_by': 'AI',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return get_fallback_location_analysis(nearby_zones)

def get_fallback_location_analysis(nearby_zones):
    """Fallback location analysis when AI is not available"""
    if not nearby_zones:
        return {
            'analysis': 'No investment zones found in this area. Consider exploring nearby metropolitan regions for better investment opportunities.',
            'generated_by': 'Fallback Algorithm',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    best_zone = nearby_zones[0]  # Closest zone
    
    analysis = f"""
    Location Analysis: You are near {best_zone['name']}, which ranks #{best_zone['rank']} in our investment zones with {best_zone['outlook']} growth outlook.
    
    Investment Opportunities: This area shows {best_zone['confidence']} confidence levels for real estate investments. Consider diversifying across multiple asset classes.
    
    Key Factors: Proximity to established investment zones, infrastructure development, and market accessibility are positive indicators.
    
    Risk Considerations: Market volatility and location-specific factors should be evaluated based on your investment timeline and risk tolerance.
    """
    
    return {
        'analysis': analysis.strip(),
        'generated_by': 'Fallback Algorithm',
        'timestamp': datetime.utcnow().isoformat()
    }

def generate_smart_recommendations(user_profile, location_data, market_conditions, investment_goals):
    """Generate comprehensive investment recommendations"""
    try:
        if not openai.api_key:
            return get_fallback_smart_recommendations(user_profile, investment_goals)
        
        context = f"""
        User Profile: {user_profile.get('risk_profile', 'MODERATE')} risk tolerance, 
        Income: ₹{user_profile.get('monthly_income', 50000)}/month
        
        Location: {location_data.get('city', 'Not specified')}
        
        Goals: {investment_goals.get('type', 'WEALTH')} goal, 
        Target: ₹{investment_goals.get('target_amount', 1000000)}, 
        Timeline: {investment_goals.get('horizon_months', 60)} months
        """
        
        prompt = f"""
        Provide smart investment recommendations based on:
        {context}
        
        Include:
        1. Recommended asset allocation
        2. Specific investment products to consider
        3. Timeline-based strategy
        4. Risk management tips
        5. Action steps
        
        Keep recommendations practical and actionable.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a comprehensive financial advisor providing personalized investment strategies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return {
            'recommendations': response.choices[0].message.content,
            'generated_by': 'AI',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return get_fallback_smart_recommendations(user_profile, investment_goals)

def get_fallback_smart_recommendations(user_profile, investment_goals):
    """Fallback smart recommendations"""
    risk_profile = user_profile.get('risk_profile', 'MODERATE')
    goal_type = investment_goals.get('type', 'WEALTH')
    
    if risk_profile == 'CONSERVATIVE':
        recommendations = """
        Smart Investment Strategy:
        1. Asset Allocation: 60% Debt Funds, 25% Index Funds, 15% Gold ETF
        2. Products: Government bonds, high-grade corporate bonds, blue-chip index funds
        3. Timeline Strategy: Focus on capital preservation with steady 6-8% returns
        4. Risk Management: Diversify across debt instruments, avoid high-volatility assets
        5. Action Steps: Start with debt funds, gradually add equity exposure over time
        """
    elif risk_profile == 'GROWTH':
        recommendations = """
        Smart Investment Strategy:
        1. Asset Allocation: 50% Equity Funds, 30% Index Funds, 15% REITs, 5% Gold
        2. Products: Growth-oriented mutual funds, technology sector funds, real estate investments
        3. Timeline Strategy: Aggressive growth focus for long-term wealth creation
        4. Risk Management: Regular portfolio rebalancing, systematic investment approach
        5. Action Steps: Start SIPs in growth funds, consider direct equity after building base
        """
    else:  # MODERATE
        recommendations = """
        Smart Investment Strategy:
        1. Asset Allocation: 40% Index Funds, 25% Flexi-cap Funds, 20% Debt Funds, 15% Gold ETF
        2. Products: Balanced mutual funds, diversified index funds, hybrid instruments
        3. Timeline Strategy: Balanced approach targeting 10-12% annual returns
        4. Risk Management: Regular review and rebalancing, gradual risk adjustment
        5. Action Steps: Begin with balanced funds, increase equity allocation over time
        """
    
    return {
        'recommendations': recommendations.strip(),
        'generated_by': 'Fallback Algorithm',
        'timestamp': datetime.utcnow().isoformat()
    }

def generate_market_insights(recent_events, top_zones):
    """Generate market insights based on recent events and zone data"""
    try:
        if not openai.api_key:
            return get_fallback_market_insights(recent_events, top_zones)
        
        events_summary = [f"{event.title} ({event.type})" for event in recent_events[:5]]
        zones_summary = [f"{zone.name} (Rank #{zone.rank})" for zone in top_zones]
        
        prompt = f"""
        Generate market insights based on:
        Recent Events: {', '.join(events_summary)}
        Top Investment Zones: {', '.join(zones_summary)}
        
        Provide:
        1. Current market trends (2-3 key points)
        2. Emerging opportunities
        3. Areas to watch
        4. Investment timing considerations
        
        Keep insights actionable and forward-looking.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a market analyst providing investment insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return {
            'insights': response.choices[0].message.content,
            'generated_by': 'AI',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return get_fallback_market_insights(recent_events, top_zones)

def get_fallback_market_insights(recent_events, top_zones):
    """Fallback market insights"""
    insights = """
    Current Market Trends:
    • Infrastructure development continues to drive real estate growth in tier-1 cities
    • Technology sector expansion is creating new investment opportunities
    • Government policy support for affordable housing is opening new segments
    
    Emerging Opportunities:
    • Tier-2 cities showing strong growth potential with lower entry costs
    • REITs gaining popularity as alternative real estate investment option
    • Sustainable and green building projects attracting premium valuations
    
    Areas to Watch:
    • Metro connectivity projects in major cities
    • IT park developments in emerging tech hubs
    • Smart city initiatives and their impact on property values
    
    Investment Timing:
    • Current market conditions favor systematic investment approaches
    • Consider staggered entry for large investments to average out market volatility
    • Long-term outlook remains positive despite short-term fluctuations
    """
    
    return {
        'insights': insights.strip(),
        'generated_by': 'Fallback Algorithm',
        'timestamp': datetime.utcnow().isoformat()
    }

def perform_risk_assessment(investment_type, amount, zone, time_horizon, user_profile):
    """Perform comprehensive risk assessment"""
    risk_factors = []
    risk_score = 0  # 0-100 scale
    
    # Zone-based risk assessment
    if zone:
        if zone.confidence == 'LOW':
            risk_score += 20
            risk_factors.append('Low confidence in zone outlook')
        elif zone.confidence == 'MEDIUM':
            risk_score += 10
            risk_factors.append('Moderate confidence in zone performance')
        
        if zone.outlook == 'LOW':
            risk_score += 15
            risk_factors.append('Zone has low growth outlook')
    
    # Investment type risk
    if investment_type == 'real_estate':
        risk_score += 15
        risk_factors.append('Real estate liquidity constraints')
    elif investment_type == 'stocks':
        risk_score += 25
        risk_factors.append('High market volatility in equity investments')
    
    # Time horizon risk
    if time_horizon < 36:  # Less than 3 years
        risk_score += 20
        risk_factors.append('Short investment horizon increases risk')
    elif time_horizon > 120:  # More than 10 years
        risk_score += 5
        risk_factors.append('Long-term market uncertainty')
    
    # Amount-based risk
    if amount > 5000000:  # More than 50 lakhs
        risk_score += 10
        risk_factors.append('Large investment amount concentration risk')
    
    # User profile risk
    risk_profile = user_profile.get('risk_profile', 'MODERATE')
    if risk_profile == 'CONSERVATIVE' and investment_type in ['stocks', 'real_estate']:
        risk_score += 15
        risk_factors.append('Investment type misaligned with conservative risk profile')
    
    # Determine risk level
    if risk_score <= 30:
        risk_level = 'LOW'
        risk_description = 'Low risk investment with stable returns expected'
    elif risk_score <= 60:
        risk_level = 'MEDIUM'
        risk_description = 'Moderate risk with balanced return potential'
    else:
        risk_level = 'HIGH'
        risk_description = 'High risk investment requiring careful monitoring'
    
    # Risk mitigation suggestions
    mitigation_strategies = []
    if risk_score > 50:
        mitigation_strategies.extend([
            'Consider diversifying across multiple asset classes',
            'Implement systematic investment approach to reduce timing risk',
            'Regular portfolio review and rebalancing'
        ])
    
    if investment_type == 'real_estate' and amount > 2000000:
        mitigation_strategies.append('Consider REITs for better liquidity and diversification')
    
    return {
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'risk_description': risk_description,
        'risk_factors': risk_factors,
        'mitigation_strategies': mitigation_strategies,
        'assessment_date': datetime.utcnow().isoformat()
    }

