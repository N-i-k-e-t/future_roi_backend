from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.investment import Product, Goal, Plan, Projection, AssetSnapshot
from src.models.zone import Zone
import json
from datetime import datetime, timedelta
import random

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolio/compare', methods=['POST'])
def compare_investments():
    """Compare different investment options (real estate vs SIP vs stocks etc.)"""
    try:
        data = request.get_json()
        
        investment_amount = data.get('amount', 1000000)
        time_horizon = data.get('horizon_months', 60)
        risk_profile = data.get('risk_profile', 'MODERATE')
        zone_id = data.get('zone_id')
        
        # Get comparison data for different investment types
        comparisons = []
        
        # Real Estate (if zone provided)
        if zone_id:
            zone = Zone.query.get(zone_id)
            if zone:
                real_estate_data = calculate_investment_returns(
                    'real_estate', investment_amount, time_horizon, zone
                )
                comparisons.append(real_estate_data)
        
        # SIP/Mutual Funds
        sip_data = calculate_investment_returns(
            'sip', investment_amount, time_horizon
        )
        comparisons.append(sip_data)
        
        # Stocks/Equity
        stocks_data = calculate_investment_returns(
            'stocks', investment_amount, time_horizon
        )
        comparisons.append(stocks_data)
        
        # Fixed Deposits
        fd_data = calculate_investment_returns(
            'fixed_deposit', investment_amount, time_horizon
        )
        comparisons.append(fd_data)
        
        # Gold
        gold_data = calculate_investment_returns(
            'gold', investment_amount, time_horizon
        )
        comparisons.append(gold_data)
        
        # PPF
        ppf_data = calculate_investment_returns(
            'ppf', investment_amount, time_horizon
        )
        comparisons.append(ppf_data)
        
        # Sort by ROI percentage
        comparisons.sort(key=lambda x: x['roi_percentage'], reverse=True)
        
        # Generate recommendations
        recommendations = generate_investment_recommendations(
            comparisons, risk_profile, time_horizon, investment_amount
        )
        
        return jsonify({
            'success': True,
            'data': {
                'comparisons': comparisons,
                'recommendations': recommendations,
                'analysis_date': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/create', methods=['POST'])
def create_portfolio():
    """Create a new investment portfolio for a user"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id', 1)  # Default user for demo
        portfolio_name = data.get('name', 'My Portfolio')
        initial_amount = data.get('initial_amount', 0)
        monthly_sip = data.get('monthly_sip', 0)
        allocations = data.get('allocations', {})  # {investment_type: percentage}
        
        # Create portfolio plan
        plan = Plan(
            user_id=user_id,
            name=portfolio_name,
            type='PORTFOLIO',
            status='ACTIVE',
            target_amount=initial_amount * 2,  # Default target
            current_amount=initial_amount,
            monthly_contribution=monthly_sip,
            start_date=datetime.utcnow(),
            target_date=datetime.utcnow() + timedelta(days=365*5),  # 5 years
            risk_profile='MODERATE',
            notes=json.dumps(allocations)
        )
        
        db.session.add(plan)
        db.session.commit()
        
        # Create initial asset snapshots
        for investment_type, percentage in allocations.items():
            amount = (initial_amount * percentage) / 100
            if amount > 0:
                snapshot = AssetSnapshot(
                    plan_id=plan.id,
                    asset_type=investment_type,
                    amount=amount,
                    units=amount,  # Simplified
                    price_per_unit=1.0,
                    date=datetime.utcnow()
                )
                db.session.add(snapshot)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio_id': plan.id,
                'name': plan.name,
                'initial_amount': initial_amount,
                'allocations': allocations,
                'created_at': plan.created_at.isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
    """Get portfolio details and current performance"""
    try:
        plan = Plan.query.get(portfolio_id)
        if not plan:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
        
        # Get latest asset snapshots
        latest_snapshots = db.session.query(AssetSnapshot)\
            .filter_by(plan_id=portfolio_id)\
            .order_by(AssetSnapshot.date.desc())\
            .all()
        
        # Calculate current value and performance
        current_value = sum(snapshot.amount for snapshot in latest_snapshots)
        initial_value = plan.current_amount or 0
        
        if initial_value > 0:
            total_return = current_value - initial_value
            return_percentage = (total_return / initial_value) * 100
        else:
            total_return = 0
            return_percentage = 0
        
        # Group assets by type
        asset_breakdown = {}
        for snapshot in latest_snapshots:
            if snapshot.asset_type not in asset_breakdown:
                asset_breakdown[snapshot.asset_type] = {
                    'amount': 0,
                    'percentage': 0
                }
            asset_breakdown[snapshot.asset_type]['amount'] += snapshot.amount
        
        # Calculate percentages
        for asset_type in asset_breakdown:
            if current_value > 0:
                asset_breakdown[asset_type]['percentage'] = \
                    (asset_breakdown[asset_type]['amount'] / current_value) * 100
        
        # Get performance history (simplified)
        performance_history = generate_performance_history(plan, latest_snapshots)
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio': {
                    'id': plan.id,
                    'name': plan.name,
                    'type': plan.type,
                    'status': plan.status,
                    'created_at': plan.created_at.isoformat(),
                    'initial_value': initial_value,
                    'current_value': current_value,
                    'total_return': total_return,
                    'return_percentage': return_percentage,
                    'monthly_sip': plan.monthly_contribution,
                    'target_amount': plan.target_amount,
                    'target_date': plan.target_date.isoformat() if plan.target_date else None
                },
                'asset_breakdown': asset_breakdown,
                'performance_history': performance_history
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>/rebalance', methods=['POST'])
def rebalance_portfolio(portfolio_id):
    """Rebalance portfolio based on new allocation preferences"""
    try:
        data = request.get_json()
        new_allocations = data.get('allocations', {})
        
        plan = Plan.query.get(portfolio_id)
        if not plan:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
        
        # Get current total value
        current_snapshots = db.session.query(AssetSnapshot)\
            .filter_by(plan_id=portfolio_id)\
            .order_by(AssetSnapshot.date.desc())\
            .all()
        
        total_value = sum(snapshot.amount for snapshot in current_snapshots)
        
        # Create new snapshots based on rebalancing
        rebalance_actions = []
        
        for asset_type, target_percentage in new_allocations.items():
            target_amount = (total_value * target_percentage) / 100
            
            # Find current amount in this asset
            current_amount = 0
            for snapshot in current_snapshots:
                if snapshot.asset_type == asset_type:
                    current_amount += snapshot.amount
            
            difference = target_amount - current_amount
            
            if abs(difference) > 100:  # Only rebalance if difference > ₹100
                action = {
                    'asset_type': asset_type,
                    'current_amount': current_amount,
                    'target_amount': target_amount,
                    'action': 'BUY' if difference > 0 else 'SELL',
                    'amount': abs(difference)
                }
                rebalance_actions.append(action)
                
                # Create new snapshot
                new_snapshot = AssetSnapshot(
                    plan_id=portfolio_id,
                    asset_type=asset_type,
                    amount=target_amount,
                    units=target_amount,  # Simplified
                    price_per_unit=1.0,
                    date=datetime.utcnow()
                )
                db.session.add(new_snapshot)
        
        # Update plan notes with new allocations
        plan.notes = json.dumps(new_allocations)
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio_id': portfolio_id,
                'rebalance_actions': rebalance_actions,
                'new_allocations': new_allocations,
                'total_value': total_value,
                'rebalance_date': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/expense-tracker', methods=['POST'])
def track_expenses():
    """Track personal expenses to determine investment capacity"""
    try:
        data = request.get_json()
        
        monthly_income = data.get('monthly_income', 0)
        expenses = data.get('expenses', {})  # {category: amount}
        
        total_expenses = sum(expenses.values())
        available_for_investment = monthly_income - total_expenses
        
        # Calculate recommended investment allocation
        recommendations = calculate_investment_capacity(
            monthly_income, total_expenses, available_for_investment
        )
        
        # Expense analysis
        expense_analysis = analyze_expenses(expenses, monthly_income)
        
        return jsonify({
            'success': True,
            'data': {
                'monthly_income': monthly_income,
                'total_expenses': total_expenses,
                'available_for_investment': available_for_investment,
                'investment_percentage': (available_for_investment / monthly_income * 100) if monthly_income > 0 else 0,
                'expense_breakdown': expenses,
                'recommendations': recommendations,
                'expense_analysis': expense_analysis
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/sip-calculator', methods=['POST'])
def sip_calculator():
    """Calculate SIP returns and compare with lump sum"""
    try:
        data = request.get_json()
        
        monthly_sip = data.get('monthly_sip', 10000)
        annual_return = data.get('annual_return', 12)  # percentage
        time_period = data.get('time_period', 10)  # years
        
        # Calculate SIP returns
        monthly_return = annual_return / 12 / 100
        total_months = time_period * 12
        
        # SIP future value formula
        if monthly_return > 0:
            sip_future_value = monthly_sip * (((1 + monthly_return) ** total_months - 1) / monthly_return) * (1 + monthly_return)
        else:
            sip_future_value = monthly_sip * total_months
        
        total_invested = monthly_sip * total_months
        sip_returns = sip_future_value - total_invested
        
        # Compare with lump sum investment
        lump_sum_amount = total_invested
        lump_sum_future_value = lump_sum_amount * ((1 + annual_return/100) ** time_period)
        lump_sum_returns = lump_sum_future_value - lump_sum_amount
        
        # Year-wise breakdown
        yearly_breakdown = []
        current_value = 0
        invested_so_far = 0
        
        for year in range(1, time_period + 1):
            invested_so_far += monthly_sip * 12
            if monthly_return > 0:
                current_value = monthly_sip * (((1 + monthly_return) ** (year * 12) - 1) / monthly_return) * (1 + monthly_return)
            else:
                current_value = invested_so_far
            
            yearly_breakdown.append({
                'year': year,
                'invested': invested_so_far,
                'value': current_value,
                'returns': current_value - invested_so_far
            })
        
        return jsonify({
            'success': True,
            'data': {
                'sip_details': {
                    'monthly_sip': monthly_sip,
                    'annual_return': annual_return,
                    'time_period': time_period,
                    'total_invested': total_invested,
                    'future_value': sip_future_value,
                    'total_returns': sip_returns,
                    'roi_percentage': (sip_returns / total_invested * 100) if total_invested > 0 else 0
                },
                'lump_sum_comparison': {
                    'amount': lump_sum_amount,
                    'future_value': lump_sum_future_value,
                    'total_returns': lump_sum_returns,
                    'roi_percentage': (lump_sum_returns / lump_sum_amount * 100) if lump_sum_amount > 0 else 0
                },
                'yearly_breakdown': yearly_breakdown,
                'recommendation': 'SIP' if sip_future_value > lump_sum_future_value else 'Lump Sum'
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_investment_returns(investment_type, amount, horizon_months, zone=None):
    """Calculate returns for different investment types"""
    
    # Base return rates (annual %)
    return_rates = {
        'real_estate': 12.0,
        'sip': 12.0,
        'stocks': 15.0,
        'fixed_deposit': 6.5,
        'gold': 8.0,
        'ppf': 7.1
    }
    
    # Risk levels
    risk_levels = {
        'real_estate': 'MEDIUM',
        'sip': 'MEDIUM',
        'stocks': 'HIGH',
        'fixed_deposit': 'LOW',
        'gold': 'LOW',
        'ppf': 'LOW'
    }
    
    # Liquidity ratings
    liquidity = {
        'real_estate': 'LOW',
        'sip': 'MEDIUM',
        'stocks': 'HIGH',
        'fixed_deposit': 'LOW',
        'gold': 'HIGH',
        'ppf': 'LOW'
    }
    
    base_rate = return_rates.get(investment_type, 10.0)
    
    # Adjust for zone if real estate
    if investment_type == 'real_estate' and zone:
        if zone.outlook == 'HIGH':
            base_rate += 2.0
        elif zone.outlook == 'LOW':
            base_rate -= 2.0
    
    # Calculate future value
    annual_rate = base_rate / 100
    years = horizon_months / 12
    future_value = amount * ((1 + annual_rate) ** years)
    total_returns = future_value - amount
    roi_percentage = (total_returns / amount) * 100
    
    # Calculate stress scenarios
    optimistic_rate = base_rate + 3.0
    pessimistic_rate = max(base_rate - 3.0, 1.0)
    
    optimistic_value = amount * ((1 + optimistic_rate/100) ** years)
    pessimistic_value = amount * ((1 + pessimistic_rate/100) ** years)
    
    return {
        'investment_type': investment_type,
        'display_name': investment_type.replace('_', ' ').title(),
        'amount': amount,
        'horizon_months': horizon_months,
        'annual_return_rate': base_rate,
        'future_value': future_value,
        'total_returns': total_returns,
        'roi_percentage': roi_percentage,
        'risk_level': risk_levels.get(investment_type, 'MEDIUM'),
        'liquidity': liquidity.get(investment_type, 'MEDIUM'),
        'stress_scenarios': {
            'optimistic': {
                'rate': optimistic_rate,
                'future_value': optimistic_value,
                'roi_percentage': ((optimistic_value - amount) / amount) * 100
            },
            'pessimistic': {
                'rate': pessimistic_rate,
                'future_value': pessimistic_value,
                'roi_percentage': ((pessimistic_value - amount) / amount) * 100
            }
        },
        'zone_info': zone.to_dict() if zone else None
    }

def generate_investment_recommendations(comparisons, risk_profile, time_horizon, amount):
    """Generate investment recommendations based on comparison"""
    
    recommendations = []
    
    # Filter by risk profile
    suitable_investments = []
    for comp in comparisons:
        if risk_profile == 'CONSERVATIVE' and comp['risk_level'] in ['LOW', 'MEDIUM']:
            suitable_investments.append(comp)
        elif risk_profile == 'MODERATE':
            suitable_investments.append(comp)
        elif risk_profile == 'GROWTH' and comp['risk_level'] in ['MEDIUM', 'HIGH']:
            suitable_investments.append(comp)
    
    if not suitable_investments:
        suitable_investments = comparisons
    
    # Top performer
    if suitable_investments:
        top_performer = suitable_investments[0]
        recommendations.append({
            'type': 'TOP_PERFORMER',
            'title': f'Highest Returns: {top_performer["display_name"]}',
            'description': f'Expected {top_performer["roi_percentage"]:.1f}% returns over {time_horizon} months',
            'investment_type': top_performer['investment_type'],
            'rationale': f'Best ROI potential with {top_performer["risk_level"].lower()} risk'
        })
    
    # Balanced approach
    if len(suitable_investments) >= 2:
        recommendations.append({
            'type': 'BALANCED',
            'title': 'Diversified Portfolio',
            'description': f'Split investment across {len(suitable_investments[:3])} asset classes',
            'allocation': {
                inv['investment_type']: 100 // len(suitable_investments[:3])
                for inv in suitable_investments[:3]
            },
            'rationale': 'Reduces risk through diversification'
        })
    
    # Time-based recommendation
    if time_horizon >= 60:  # 5+ years
        long_term_options = [comp for comp in suitable_investments 
                           if comp['investment_type'] in ['real_estate', 'sip', 'stocks']]
        if long_term_options:
            recommendations.append({
                'type': 'LONG_TERM',
                'title': 'Long-term Growth Strategy',
                'description': f'Focus on {long_term_options[0]["display_name"]} for long-term wealth creation',
                'investment_type': long_term_options[0]['investment_type'],
                'rationale': 'Long investment horizon allows for higher growth potential'
            })
    
    return recommendations

def generate_performance_history(plan, snapshots):
    """Generate mock performance history for portfolio"""
    history = []
    start_date = plan.created_at
    current_date = datetime.utcnow()
    
    # Generate monthly data points
    date = start_date
    initial_value = plan.current_amount or 100000
    
    while date <= current_date:
        # Simulate some growth with volatility
        months_elapsed = (date - start_date).days / 30
        base_growth = 1 + (0.12 * months_elapsed / 12)  # 12% annual growth
        volatility = 1 + (random.uniform(-0.05, 0.05))  # ±5% volatility
        
        value = initial_value * base_growth * volatility
        
        history.append({
            'date': date.isoformat(),
            'value': value,
            'returns': value - initial_value,
            'return_percentage': ((value - initial_value) / initial_value) * 100
        })
        
        # Move to next month
        if date.month == 12:
            date = date.replace(year=date.year + 1, month=1)
        else:
            date = date.replace(month=date.month + 1)
    
    return history[-12:]  # Return last 12 months

def calculate_investment_capacity(monthly_income, total_expenses, available_amount):
    """Calculate recommended investment allocation"""
    
    recommendations = []
    
    if available_amount <= 0:
        recommendations.append({
            'type': 'EXPENSE_REDUCTION',
            'title': 'Reduce Expenses First',
            'description': 'Your expenses exceed income. Focus on expense reduction before investing.',
            'priority': 'HIGH'
        })
        return recommendations
    
    investment_percentage = (available_amount / monthly_income) * 100
    
    if investment_percentage < 10:
        recommendations.append({
            'type': 'INCREASE_SAVINGS',
            'title': 'Increase Savings Rate',
            'description': f'Currently saving {investment_percentage:.1f}%. Aim for at least 20%.',
            'priority': 'HIGH'
        })
    elif investment_percentage < 20:
        recommendations.append({
            'type': 'GOOD_START',
            'title': 'Good Savings Rate',
            'description': f'Saving {investment_percentage:.1f}% is good. Consider increasing to 25-30%.',
            'priority': 'MEDIUM'
        })
    else:
        recommendations.append({
            'type': 'EXCELLENT',
            'title': 'Excellent Savings Rate',
            'description': f'Saving {investment_percentage:.1f}% is excellent. Focus on optimal allocation.',
            'priority': 'LOW'
        })
    
    # Allocation suggestions
    if available_amount >= 5000:
        recommendations.append({
            'type': 'SIP_RECOMMENDATION',
            'title': 'Start SIP Investment',
            'description': f'Start with ₹{min(available_amount * 0.7, 25000):.0f}/month in equity mutual funds',
            'amount': min(available_amount * 0.7, 25000),
            'priority': 'MEDIUM'
        })
    
    if available_amount >= 10000:
        recommendations.append({
            'type': 'EMERGENCY_FUND',
            'title': 'Build Emergency Fund',
            'description': f'Keep ₹{available_amount * 0.3:.0f}/month for emergency fund (6 months expenses)',
            'amount': available_amount * 0.3,
            'priority': 'HIGH'
        })
    
    return recommendations

def analyze_expenses(expenses, monthly_income):
    """Analyze expense patterns and provide insights"""
    
    analysis = {
        'total_expenses': sum(expenses.values()),
        'expense_ratio': (sum(expenses.values()) / monthly_income * 100) if monthly_income > 0 else 0,
        'category_analysis': [],
        'recommendations': []
    }
    
    # Recommended expense ratios
    recommended_ratios = {
        'housing': 30,
        'food': 15,
        'transportation': 15,
        'utilities': 10,
        'entertainment': 10,
        'healthcare': 5,
        'miscellaneous': 15
    }
    
    for category, amount in expenses.items():
        percentage = (amount / monthly_income * 100) if monthly_income > 0 else 0
        recommended = recommended_ratios.get(category.lower(), 10)
        
        category_info = {
            'category': category,
            'amount': amount,
            'percentage': percentage,
            'recommended_percentage': recommended,
            'status': 'OVER' if percentage > recommended else 'UNDER' if percentage < recommended * 0.5 else 'OPTIMAL'
        }
        
        analysis['category_analysis'].append(category_info)
        
        if percentage > recommended:
            analysis['recommendations'].append({
                'type': 'REDUCE_EXPENSE',
                'category': category,
                'message': f'Consider reducing {category} expenses by ₹{amount - (monthly_income * recommended / 100):.0f}'
            })
    
    return analysis

