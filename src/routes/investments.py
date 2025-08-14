from flask import Blueprint, request, jsonify
from src.models.investment import Product, Goal, Plan, Projection, AssetSnapshot
from src.models.zone import Zone
from src.models.user import User, db
import openai
import os
import json
from datetime import datetime

investments_bp = Blueprint('investments', __name__)

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

@investments_bp.route('/products', methods=['GET'])
def get_products():
    """Get all investment products with optional filtering"""
    try:
        category = request.args.get('category')
        risk = request.args.get('risk')
        
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category.upper())
        if risk:
            query = query.filter(Product.risk == risk.upper())
        
        products = query.all()
        products_data = [product.to_dict() for product in products]
        
        return jsonify({
            'success': True,
            'data': products_data,
            'count': len(products_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/recommendations', methods=['POST'])
def get_investment_recommendations():
    """Get AI-powered investment recommendations"""
    try:
        data = request.get_json()
        
        # Extract user profile and goal data
        user_profile = data.get('user_profile', {})
        goal_data = data.get('goal_data', {})
        zone_id = data.get('zone_id')
        
        # Get zone data if provided
        zone_data = None
        if zone_id:
            zone = Zone.query.get(zone_id)
            if zone:
                zone_data = zone.to_dict()
        
        # Generate recommendations
        recommendations = generate_portfolio_recommendations(user_profile, goal_data, zone_data)
        
        return jsonify({
            'success': True,
            'data': recommendations
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/goals', methods=['POST'])
def create_goal():
    """Create a new investment goal"""
    try:
        data = request.get_json()
        
        goal = Goal(
            user_id=data['user_id'],
            zone_id=data.get('zone_id'),
            type=data['type'],
            target_amount=data['target_amount'],
            horizon_months=data['horizon_months']
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': goal.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/goals/<int:user_id>', methods=['GET'])
def get_user_goals(user_id):
    """Get all goals for a user"""
    try:
        goals = Goal.query.filter_by(user_id=user_id).all()
        goals_data = []
        
        for goal in goals:
            goal_dict = goal.to_dict()
            # Add zone information if available
            if goal.zone:
                goal_dict['zone'] = goal.zone.to_dict()
            # Add plans count
            goal_dict['plans_count'] = len(goal.plans)
            goals_data.append(goal_dict)
        
        return jsonify({
            'success': True,
            'data': goals_data,
            'count': len(goals_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/plans', methods=['POST'])
def create_plan():
    """Create a new investment plan"""
    try:
        data = request.get_json()
        
        plan = Plan(
            user_id=data['user_id'],
            goal_id=data['goal_id'],
            allocation_json=json.dumps(data['allocation']),
            monthly_amount=data['monthly_amount']
        )
        
        db.session.add(plan)
        db.session.commit()
        
        # Create projections for the plan
        projections_data = data.get('projections', {})
        if projections_data:
            projection = Projection(
                plan_id=plan.id,
                base_coverage_min=projections_data.get('base_coverage_min', 0),
                base_coverage_max=projections_data.get('base_coverage_max', 0),
                stress_coverage_min=projections_data.get('stress_coverage_min', 0),
                stress_coverage_max=projections_data.get('stress_coverage_max', 0),
                assumptions=json.dumps(projections_data.get('assumptions', []))
            )
            db.session.add(projection)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': plan.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/plans/<int:user_id>', methods=['GET'])
def get_user_plans(user_id):
    """Get all plans for a user"""
    try:
        plans = Plan.query.filter_by(user_id=user_id).all()
        plans_data = []
        
        for plan in plans:
            plan_dict = plan.to_dict()
            # Add goal information
            if plan.goal:
                plan_dict['goal'] = plan.goal.to_dict()
            # Add projections
            if plan.projections:
                plan_dict['projections'] = [proj.to_dict() for proj in plan.projections]
            plans_data.append(plan_dict)
        
        return jsonify({
            'success': True,
            'data': plans_data,
            'count': len(plans_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/health-score/<int:user_id>', methods=['GET'])
def get_financial_health_score(user_id):
    """Calculate financial health score for a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get latest asset snapshot
        latest_snapshot = AssetSnapshot.query.filter_by(user_id=user_id).order_by(AssetSnapshot.created_at.desc()).first()
        
        # Calculate health score
        health_score = calculate_financial_health_score(user, latest_snapshot)
        
        return jsonify({
            'success': True,
            'data': health_score
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@investments_bp.route('/assets/<int:user_id>', methods=['POST'])
def update_user_assets(user_id):
    """Update user's asset snapshot"""
    try:
        data = request.get_json()
        
        asset_snapshot = AssetSnapshot(
            user_id=user_id,
            savings=data.get('savings', 0),
            mf=data.get('mf', 0),
            stocks=data.get('stocks', 0),
            gold=data.get('gold', 0),
            epf=data.get('epf', 0),
            real_estate=data.get('real_estate', 0),
            liabilities=data.get('liabilities', 0)
        )
        
        db.session.add(asset_snapshot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': asset_snapshot.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_portfolio_recommendations(user_profile, goal_data, zone_data):
    """Generate AI-powered portfolio recommendations"""
    try:
        if not openai.api_key:
            return get_default_recommendations(user_profile, goal_data, zone_data)
        
        # Prepare context for AI
        context = f"""
        User Profile:
        - Risk Profile: {user_profile.get('risk_profile', 'MODERATE')}
        - Monthly Income: ₹{user_profile.get('monthly_income', 50000)}
        - Goal: {goal_data.get('type', 'WEALTH')} goal
        - Target Amount: ₹{goal_data.get('target_amount', 1000000)}
        - Timeline: {goal_data.get('horizon_months', 60)} months
        """
        
        if zone_data:
            context += f"""
        Investment Zone:
        - Location: {zone_data.get('name')}
        - Outlook: {zone_data.get('outlook')}
        - Confidence: {zone_data.get('confidence')}
        """
        
        prompt = f"""You are a conservative financial advisor. Create 3 portfolios (recommended, conservative, growth) for:
        {context}
        
        Provide allocation percentages for: Index Funds, Flexi-cap MF, Debt Funds, REITs, Gold ETF
        Include 3 rationale bullets and confidence level (Low/Medium/High)
        Show ranges, never guaranteed returns.
        
        Format as JSON with portfolios array containing name, allocation object, rationale array, and confidence."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a conservative financial advisor providing portfolio recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse AI response (simplified - in production, use more robust parsing)
        ai_text = response.choices[0].message.content
        
        return {
            'portfolios': parse_ai_recommendations(ai_text),
            'generated_by': 'AI',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return get_default_recommendations(user_profile, goal_data, zone_data)

def get_default_recommendations(user_profile, goal_data, zone_data):
    """Fallback recommendations when AI is not available"""
    risk_profile = user_profile.get('risk_profile', 'MODERATE')
    
    if risk_profile == 'CONSERVATIVE':
        portfolios = [
            {
                'name': 'Conservative',
                'allocation': {'debt_funds': 60, 'index_funds': 25, 'gold_etf': 15},
                'rationale': ['Capital preservation focus', 'Low volatility', 'Steady returns'],
                'confidence': 'High'
            },
            {
                'name': 'Ultra Conservative',
                'allocation': {'debt_funds': 70, 'index_funds': 20, 'gold_etf': 10},
                'rationale': ['Maximum safety', 'Minimal risk', 'Predictable returns'],
                'confidence': 'High'
            }
        ]
    elif risk_profile == 'GROWTH':
        portfolios = [
            {
                'name': 'Growth',
                'allocation': {'flexi_cap': 40, 'index_funds': 35, 'reits': 15, 'gold_etf': 10},
                'rationale': ['High growth potential', 'Diversified equity exposure', 'Long-term wealth creation'],
                'confidence': 'Medium'
            },
            {
                'name': 'Aggressive Growth',
                'allocation': {'flexi_cap': 50, 'index_funds': 30, 'reits': 20},
                'rationale': ['Maximum growth focus', 'Higher risk tolerance', 'Long investment horizon'],
                'confidence': 'Medium'
            }
        ]
    else:  # MODERATE
        portfolios = [
            {
                'name': 'Recommended',
                'allocation': {'index_funds': 40, 'flexi_cap': 25, 'debt_funds': 20, 'gold_etf': 15},
                'rationale': ['Balanced risk-return', 'Diversified portfolio', 'Suitable for moderate risk'],
                'confidence': 'High'
            },
            {
                'name': 'Conservative',
                'allocation': {'debt_funds': 40, 'index_funds': 35, 'gold_etf': 25},
                'rationale': ['Lower risk approach', 'Stable returns', 'Capital protection'],
                'confidence': 'High'
            },
            {
                'name': 'Growth',
                'allocation': {'flexi_cap': 35, 'index_funds': 35, 'reits': 20, 'gold_etf': 10},
                'rationale': ['Higher growth potential', 'Equity focused', 'Long-term gains'],
                'confidence': 'Medium'
            }
        ]
    
    return {
        'portfolios': portfolios,
        'generated_by': 'Default Algorithm',
        'timestamp': datetime.utcnow().isoformat()
    }

def parse_ai_recommendations(ai_text):
    """Parse AI response into structured recommendations"""
    # Simplified parsing - in production, use more robust JSON parsing
    try:
        # Try to extract JSON from AI response
        import re
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Fallback to default if parsing fails
    return [
        {
            'name': 'AI Recommended',
            'allocation': {'index_funds': 40, 'flexi_cap': 25, 'debt_funds': 20, 'gold_etf': 15},
            'rationale': ['AI-generated recommendation', 'Balanced approach', 'Risk-adjusted returns'],
            'confidence': 'Medium'
        }
    ]

def calculate_financial_health_score(user, asset_snapshot):
    """Calculate financial health score based on user data"""
    score = 0
    factors = {}
    
    # Income factor (20 points)
    if user.monthly_income:
        if user.monthly_income >= 100000:
            score += 20
            factors['income'] = 'Excellent'
        elif user.monthly_income >= 50000:
            score += 15
            factors['income'] = 'Good'
        elif user.monthly_income >= 25000:
            score += 10
            factors['income'] = 'Average'
        else:
            score += 5
            factors['income'] = 'Below Average'
    
    # Expense ratio factor (20 points)
    if user.monthly_income and user.monthly_expenses:
        expense_ratio = user.monthly_expenses / user.monthly_income
        if expense_ratio <= 0.5:
            score += 20
            factors['expense_ratio'] = 'Excellent'
        elif expense_ratio <= 0.7:
            score += 15
            factors['expense_ratio'] = 'Good'
        elif expense_ratio <= 0.9:
            score += 10
            factors['expense_ratio'] = 'Average'
        else:
            score += 5
            factors['expense_ratio'] = 'Poor'
    
    # Asset diversification factor (30 points)
    if asset_snapshot:
        total_assets = (asset_snapshot.savings + asset_snapshot.mf + 
                       asset_snapshot.stocks + asset_snapshot.gold + 
                       asset_snapshot.epf + asset_snapshot.real_estate)
        
        if total_assets > 0:
            # Check diversification
            asset_types = 0
            if asset_snapshot.savings > 0: asset_types += 1
            if asset_snapshot.mf > 0: asset_types += 1
            if asset_snapshot.stocks > 0: asset_types += 1
            if asset_snapshot.gold > 0: asset_types += 1
            if asset_snapshot.epf > 0: asset_types += 1
            if asset_snapshot.real_estate > 0: asset_types += 1
            
            if asset_types >= 4:
                score += 30
                factors['diversification'] = 'Excellent'
            elif asset_types >= 3:
                score += 20
                factors['diversification'] = 'Good'
            elif asset_types >= 2:
                score += 15
                factors['diversification'] = 'Average'
            else:
                score += 10
                factors['diversification'] = 'Poor'
    
    # Debt factor (20 points)
    if asset_snapshot and asset_snapshot.liabilities:
        if user.monthly_income:
            debt_to_income = (asset_snapshot.liabilities * 12) / user.monthly_income
            if debt_to_income <= 2:
                score += 20
                factors['debt'] = 'Excellent'
            elif debt_to_income <= 4:
                score += 15
                factors['debt'] = 'Good'
            elif debt_to_income <= 6:
                score += 10
                factors['debt'] = 'Average'
            else:
                score += 5
                factors['debt'] = 'Poor'
    else:
        score += 20  # No debt is good
        factors['debt'] = 'Excellent'
    
    # Goal setting factor (10 points)
    goals_count = Goal.query.filter_by(user_id=user.id).count()
    if goals_count >= 3:
        score += 10
        factors['goal_planning'] = 'Excellent'
    elif goals_count >= 2:
        score += 8
        factors['goal_planning'] = 'Good'
    elif goals_count >= 1:
        score += 5
        factors['goal_planning'] = 'Average'
    else:
        factors['goal_planning'] = 'Poor'
    
    # Determine overall rating
    if score >= 85:
        rating = 'Excellent'
    elif score >= 70:
        rating = 'Good'
    elif score >= 55:
        rating = 'Average'
    elif score >= 40:
        rating = 'Below Average'
    else:
        rating = 'Poor'
    
    return {
        'score': min(score, 100),  # Cap at 100
        'rating': rating,
        'factors': factors,
        'recommendations': get_health_recommendations(score, factors)
    }

def get_health_recommendations(score, factors):
    """Get recommendations to improve financial health"""
    recommendations = []
    
    if factors.get('expense_ratio') in ['Average', 'Poor']:
        recommendations.append('Reduce monthly expenses to improve savings rate')
    
    if factors.get('diversification') in ['Average', 'Poor']:
        recommendations.append('Diversify investments across different asset classes')
    
    if factors.get('debt') in ['Average', 'Poor']:
        recommendations.append('Focus on reducing debt burden')
    
    if factors.get('goal_planning') in ['Average', 'Poor']:
        recommendations.append('Set clear financial goals with timelines')
    
    if score < 70:
        recommendations.append('Consider consulting a financial advisor')
    
    return recommendations

