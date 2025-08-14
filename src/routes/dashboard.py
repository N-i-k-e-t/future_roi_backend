from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.investment import Product, Goal, Plan, Projection, AssetSnapshot
from src.models.zone import Zone, Event
import json
from datetime import datetime, timedelta
import random
import math

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get comprehensive dashboard overview with key metrics"""
    try:
        user_id = request.args.get('user_id', 1)
        
        # Get user's portfolios
        portfolios = Plan.query.filter_by(user_id=user_id).all()
        
        # Calculate total portfolio value
        total_portfolio_value = 0
        total_invested = 0
        portfolio_performance = []
        
        for portfolio in portfolios:
            snapshots = AssetSnapshot.query.filter_by(plan_id=portfolio.id).all()
            current_value = sum(s.amount for s in snapshots)
            initial_value = portfolio.current_amount or 0
            
            total_portfolio_value += current_value
            total_invested += initial_value
            
            if initial_value > 0:
                returns = ((current_value - initial_value) / initial_value) * 100
            else:
                returns = 0
                
            portfolio_performance.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'current_value': current_value,
                'initial_value': initial_value,
                'returns': returns,
                'status': portfolio.status
            })
        
        # Market overview
        market_overview = get_market_overview()
        
        # Top performing zones
        top_zones = Zone.query.order_by(Zone.rank.asc()).limit(5).all()
        
        # Recent activities (mock data)
        recent_activities = generate_recent_activities()
        
        # Performance metrics
        total_returns = total_portfolio_value - total_invested
        total_return_percentage = (total_returns / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio_summary': {
                    'total_value': total_portfolio_value,
                    'total_invested': total_invested,
                    'total_returns': total_returns,
                    'return_percentage': total_return_percentage,
                    'portfolio_count': len(portfolios)
                },
                'portfolio_performance': portfolio_performance,
                'market_overview': market_overview,
                'top_zones': [zone.to_dict() for zone in top_zones],
                'recent_activities': recent_activities,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/dashboard/performance-chart', methods=['GET'])
def get_performance_chart():
    """Get performance chart data for portfolio tracking"""
    try:
        user_id = request.args.get('user_id', 1)
        period = request.args.get('period', '1Y')  # 1M, 3M, 6M, 1Y, 2Y, 5Y
        
        # Generate performance data based on period
        chart_data = generate_performance_chart_data(user_id, period)
        
        return jsonify({
            'success': True,
            'data': {
                'chart_data': chart_data,
                'period': period,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/dashboard/predictions', methods=['GET'])
def get_investment_predictions():
    """Get AI-powered investment predictions and forecasts"""
    try:
        user_id = request.args.get('user_id', 1)
        horizon = int(request.args.get('horizon', 12))  # months
        
        # Get user's current portfolio
        portfolios = Plan.query.filter_by(user_id=user_id).all()
        
        predictions = []
        
        for portfolio in portfolios:
            snapshots = AssetSnapshot.query.filter_by(plan_id=portfolio.id).all()
            current_value = sum(s.amount for s in snapshots)
            
            # Generate predictions for this portfolio
            portfolio_predictions = generate_portfolio_predictions(
                portfolio, current_value, horizon
            )
            predictions.append(portfolio_predictions)
        
        # Market predictions
        market_predictions = generate_market_predictions(horizon)
        
        # Zone-specific predictions
        zone_predictions = generate_zone_predictions(horizon)
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio_predictions': predictions,
                'market_predictions': market_predictions,
                'zone_predictions': zone_predictions,
                'horizon_months': horizon,
                'confidence_level': 'MEDIUM',
                'generated_at': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/dashboard/market-trends', methods=['GET'])
def get_market_trends():
    """Get comprehensive market trends and analysis"""
    try:
        # Real estate market trends
        real_estate_trends = {
            'price_index': generate_trend_data('price_index', 24),
            'demand_supply': generate_trend_data('demand_supply', 24),
            'rental_yields': generate_trend_data('rental_yields', 24),
            'construction_activity': generate_trend_data('construction', 24)
        }
        
        # Economic indicators
        economic_indicators = {
            'interest_rates': generate_trend_data('interest_rates', 24),
            'inflation': generate_trend_data('inflation', 24),
            'gdp_growth': generate_trend_data('gdp_growth', 24),
            'employment': generate_trend_data('employment', 24)
        }
        
        # Investment trends
        investment_trends = {
            'mutual_funds': generate_trend_data('mutual_funds', 24),
            'stock_market': generate_trend_data('stock_market', 24),
            'gold_prices': generate_trend_data('gold_prices', 24),
            'crypto': generate_trend_data('crypto', 24)
        }
        
        # Trend analysis
        trend_analysis = analyze_trends(real_estate_trends, economic_indicators)
        
        return jsonify({
            'success': True,
            'data': {
                'real_estate_trends': real_estate_trends,
                'economic_indicators': economic_indicators,
                'investment_trends': investment_trends,
                'trend_analysis': trend_analysis,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/dashboard/risk-analysis', methods=['GET'])
def get_risk_analysis():
    """Get comprehensive risk analysis for user's portfolio"""
    try:
        user_id = request.args.get('user_id', 1)
        
        # Get user's portfolios
        portfolios = Plan.query.filter_by(user_id=user_id).all()
        
        risk_metrics = []
        overall_risk = {
            'score': 0,
            'level': 'MEDIUM',
            'factors': []
        }
        
        for portfolio in portfolios:
            snapshots = AssetSnapshot.query.filter_by(plan_id=portfolio.id).all()
            
            # Calculate risk metrics for this portfolio
            portfolio_risk = calculate_portfolio_risk(portfolio, snapshots)
            risk_metrics.append(portfolio_risk)
        
        # Calculate overall risk
        if risk_metrics:
            avg_risk_score = sum(r['risk_score'] for r in risk_metrics) / len(risk_metrics)
            overall_risk['score'] = avg_risk_score
            
            if avg_risk_score < 30:
                overall_risk['level'] = 'LOW'
            elif avg_risk_score < 70:
                overall_risk['level'] = 'MEDIUM'
            else:
                overall_risk['level'] = 'HIGH'
        
        # Risk factors
        risk_factors = analyze_risk_factors(portfolios)
        overall_risk['factors'] = risk_factors
        
        # Risk recommendations
        risk_recommendations = generate_risk_recommendations(overall_risk, risk_metrics)
        
        return jsonify({
            'success': True,
            'data': {
                'overall_risk': overall_risk,
                'portfolio_risks': risk_metrics,
                'risk_factors': risk_factors,
                'recommendations': risk_recommendations,
                'analysis_date': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/dashboard/news-sentiment', methods=['GET'])
def get_news_sentiment():
    """Get news sentiment analysis for real estate and investment markets"""
    try:
        # Mock news sentiment data
        news_sentiment = {
            'overall_sentiment': 'POSITIVE',
            'sentiment_score': 0.65,  # -1 to 1 scale
            'news_categories': {
                'real_estate': {
                    'sentiment': 'POSITIVE',
                    'score': 0.7,
                    'article_count': 45,
                    'key_topics': ['infrastructure development', 'policy reforms', 'market growth']
                },
                'economy': {
                    'sentiment': 'NEUTRAL',
                    'score': 0.1,
                    'article_count': 32,
                    'key_topics': ['inflation concerns', 'interest rates', 'gdp growth']
                },
                'investments': {
                    'sentiment': 'POSITIVE',
                    'score': 0.6,
                    'article_count': 28,
                    'key_topics': ['mutual fund growth', 'sip popularity', 'market rally']
                }
            },
            'trending_topics': [
                {
                    'topic': 'Smart City Development',
                    'sentiment': 'POSITIVE',
                    'relevance': 0.9,
                    'impact': 'HIGH'
                },
                {
                    'topic': 'Interest Rate Changes',
                    'sentiment': 'NEUTRAL',
                    'relevance': 0.8,
                    'impact': 'MEDIUM'
                },
                {
                    'topic': 'RERA Implementation',
                    'sentiment': 'POSITIVE',
                    'relevance': 0.7,
                    'impact': 'HIGH'
                }
            ],
            'sentiment_history': generate_sentiment_history(30)
        }
        
        return jsonify({
            'success': True,
            'data': news_sentiment
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_market_overview():
    """Generate market overview data"""
    return {
        'real_estate_index': {
            'current': 1245.67,
            'change': 2.34,
            'change_percent': 0.19
        },
        'interest_rates': {
            'current': 8.5,
            'change': -0.25,
            'trend': 'DECREASING'
        },
        'market_sentiment': 'POSITIVE',
        'active_projects': 1247,
        'avg_price_per_sqft': 8950,
        'rental_yield': 3.2
    }

def generate_recent_activities():
    """Generate recent portfolio activities"""
    activities = [
        {
            'id': 1,
            'type': 'INVESTMENT',
            'description': 'Added ₹50,000 to SIP portfolio',
            'amount': 50000,
            'date': (datetime.utcnow() - timedelta(days=1)).isoformat(),
            'status': 'COMPLETED'
        },
        {
            'id': 2,
            'type': 'ROI_UPDATE',
            'description': 'Mumbai zone ROI updated to 14.2%',
            'zone': 'Mumbai',
            'date': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'status': 'INFO'
        },
        {
            'id': 3,
            'type': 'REBALANCE',
            'description': 'Portfolio rebalanced - increased equity allocation',
            'date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'status': 'COMPLETED'
        }
    ]
    return activities

def generate_performance_chart_data(user_id, period):
    """Generate performance chart data for specified period"""
    
    # Determine number of data points based on period
    periods = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365,
        '2Y': 730,
        '5Y': 1825
    }
    
    days = periods.get(period, 365)
    data_points = min(days, 100)  # Limit to 100 points for performance
    
    chart_data = []
    base_value = 1000000  # Starting portfolio value
    
    for i in range(data_points):
        date = datetime.utcnow() - timedelta(days=days - i * (days // data_points))
        
        # Simulate portfolio growth with some volatility
        growth_factor = 1 + (0.12 * (i / data_points))  # 12% annual growth
        volatility = 1 + (random.uniform(-0.05, 0.05))  # ±5% volatility
        
        portfolio_value = base_value * growth_factor * volatility
        
        # Add some market events
        if i % 20 == 0:  # Market correction every 20 points
            portfolio_value *= 0.95
        
        chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'portfolio_value': round(portfolio_value, 2),
            'benchmark': round(base_value * (1 + 0.10 * (i / data_points)), 2),  # 10% benchmark
            'real_estate': round(base_value * (1 + 0.08 * (i / data_points)) * volatility, 2),
            'sip': round(base_value * (1 + 0.12 * (i / data_points)) * volatility, 2),
            'stocks': round(base_value * (1 + 0.15 * (i / data_points)) * volatility * 1.1, 2)
        })
    
    return chart_data

def generate_portfolio_predictions(portfolio, current_value, horizon_months):
    """Generate predictions for a specific portfolio"""
    
    # Base growth rates by asset type
    growth_rates = {
        'real_estate': 0.12,
        'sip': 0.12,
        'stocks': 0.15,
        'fixed_deposit': 0.065,
        'gold': 0.08,
        'ppf': 0.071
    }
    
    predictions = []
    
    for month in range(1, horizon_months + 1):
        # Simulate growth with some uncertainty
        base_growth = 1 + (0.12 * (month / 12))  # 12% annual growth
        uncertainty = random.uniform(0.9, 1.1)  # ±10% uncertainty
        
        predicted_value = current_value * base_growth * uncertainty
        
        predictions.append({
            'month': month,
            'predicted_value': round(predicted_value, 2),
            'confidence': max(0.9 - (month * 0.02), 0.5),  # Decreasing confidence
            'scenario': 'BASE'
        })
    
    return {
        'portfolio_id': portfolio.id,
        'portfolio_name': portfolio.name,
        'current_value': current_value,
        'predictions': predictions,
        'expected_annual_return': 12.0,
        'risk_level': portfolio.risk_profile or 'MEDIUM'
    }

def generate_market_predictions(horizon_months):
    """Generate market-wide predictions"""
    
    predictions = {
        'real_estate_market': {
            'price_growth': [
                {'month': i, 'growth_rate': 8 + random.uniform(-2, 3)}
                for i in range(1, horizon_months + 1)
            ],
            'demand_outlook': 'STRONG',
            'supply_constraints': 'MODERATE'
        },
        'interest_rates': {
            'forecast': [
                {'month': i, 'rate': 8.5 + random.uniform(-0.5, 0.5)}
                for i in range(1, horizon_months + 1)
            ],
            'trend': 'STABLE',
            'policy_impact': 'NEUTRAL'
        },
        'economic_indicators': {
            'gdp_growth': 6.5,
            'inflation': 4.2,
            'employment': 'IMPROVING'
        }
    }
    
    return predictions

def generate_zone_predictions(horizon_months):
    """Generate zone-specific predictions"""
    
    zones = Zone.query.limit(5).all()
    zone_predictions = []
    
    for zone in zones:
        prediction = {
            'zone_id': zone.id,
            'zone_name': zone.name,
            'current_rank': zone.rank,
            'predicted_growth': random.uniform(8, 15),
            'risk_factors': [
                'Infrastructure development',
                'Policy changes',
                'Market demand'
            ],
            'opportunities': [
                'Metro connectivity',
                'IT hub expansion',
                'Smart city initiatives'
            ],
            'forecast': [
                {
                    'month': i,
                    'roi_prediction': 12 + random.uniform(-2, 4),
                    'confidence': max(0.8 - (i * 0.01), 0.5)
                }
                for i in range(1, min(horizon_months + 1, 13))
            ]
        }
        zone_predictions.append(prediction)
    
    return zone_predictions

def generate_trend_data(trend_type, months):
    """Generate trend data for various metrics"""
    
    base_values = {
        'price_index': 100,
        'demand_supply': 1.2,
        'rental_yields': 3.5,
        'construction': 85,
        'interest_rates': 8.5,
        'inflation': 4.0,
        'gdp_growth': 6.5,
        'employment': 92,
        'mutual_funds': 15,
        'stock_market': 12,
        'gold_prices': 8,
        'crypto': 25
    }
    
    base_value = base_values.get(trend_type, 100)
    trend_data = []
    
    for i in range(months):
        date = datetime.utcnow() - timedelta(days=30 * (months - i))
        
        # Add trend and seasonality
        trend = base_value * (1 + 0.005 * i)  # Small upward trend
        seasonal = math.sin(2 * math.pi * i / 12) * 0.1 * base_value  # Seasonal variation
        noise = random.uniform(-0.05, 0.05) * base_value  # Random noise
        
        value = trend + seasonal + noise
        
        trend_data.append({
            'date': date.strftime('%Y-%m'),
            'value': round(value, 2)
        })
    
    return trend_data

def analyze_trends(real_estate_trends, economic_indicators):
    """Analyze trends and provide insights"""
    
    analysis = {
        'key_insights': [
            'Real estate prices showing steady growth of 8-12% annually',
            'Interest rates remain stable, supporting investment demand',
            'Infrastructure development driving tier-2 city growth',
            'Rental yields improving in metro cities'
        ],
        'market_outlook': 'POSITIVE',
        'risk_factors': [
            'Global economic uncertainty',
            'Policy changes impact',
            'Supply chain disruptions'
        ],
        'opportunities': [
            'Affordable housing segment growth',
            'Commercial real estate recovery',
            'REITs gaining popularity'
        ],
        'recommendations': [
            'Diversify across multiple zones',
            'Consider long-term investment horizon',
            'Monitor interest rate changes',
            'Focus on infrastructure-linked areas'
        ]
    }
    
    return analysis

def calculate_portfolio_risk(portfolio, snapshots):
    """Calculate risk metrics for a portfolio"""
    
    # Asset allocation analysis
    total_value = sum(s.amount for s in snapshots)
    asset_allocation = {}
    
    for snapshot in snapshots:
        asset_type = snapshot.asset_type
        percentage = (snapshot.amount / total_value * 100) if total_value > 0 else 0
        asset_allocation[asset_type] = percentage
    
    # Risk scoring based on asset allocation
    risk_weights = {
        'real_estate': 0.6,
        'stocks': 0.8,
        'sip': 0.5,
        'fixed_deposit': 0.1,
        'gold': 0.3,
        'ppf': 0.1
    }
    
    risk_score = 0
    for asset_type, percentage in asset_allocation.items():
        weight = risk_weights.get(asset_type, 0.5)
        risk_score += (percentage / 100) * weight * 100
    
    return {
        'portfolio_id': portfolio.id,
        'portfolio_name': portfolio.name,
        'risk_score': round(risk_score, 2),
        'risk_level': 'HIGH' if risk_score > 70 else 'MEDIUM' if risk_score > 30 else 'LOW',
        'asset_allocation': asset_allocation,
        'diversification_score': calculate_diversification_score(asset_allocation),
        'volatility_estimate': round(risk_score * 0.3, 2)  # Simplified volatility
    }

def calculate_diversification_score(asset_allocation):
    """Calculate diversification score (0-100)"""
    
    if not asset_allocation:
        return 0
    
    # Higher score for more balanced allocation
    num_assets = len(asset_allocation)
    if num_assets == 1:
        return 20
    elif num_assets == 2:
        return 40
    elif num_assets >= 5:
        return 90
    else:
        return 60

def analyze_risk_factors(portfolios):
    """Analyze overall risk factors"""
    
    risk_factors = [
        {
            'factor': 'Market Volatility',
            'impact': 'MEDIUM',
            'probability': 0.6,
            'description': 'Market fluctuations may affect portfolio value'
        },
        {
            'factor': 'Interest Rate Risk',
            'impact': 'HIGH',
            'probability': 0.4,
            'description': 'Rising interest rates may impact real estate returns'
        },
        {
            'factor': 'Liquidity Risk',
            'impact': 'MEDIUM',
            'probability': 0.3,
            'description': 'Real estate investments may have limited liquidity'
        },
        {
            'factor': 'Regulatory Risk',
            'impact': 'LOW',
            'probability': 0.2,
            'description': 'Policy changes may affect investment landscape'
        }
    ]
    
    return risk_factors

def generate_risk_recommendations(overall_risk, portfolio_risks):
    """Generate risk management recommendations"""
    
    recommendations = []
    
    if overall_risk['score'] > 70:
        recommendations.append({
            'type': 'REDUCE_RISK',
            'title': 'Consider Risk Reduction',
            'description': 'Your portfolio has high risk. Consider adding low-risk assets like FDs or PPF.',
            'priority': 'HIGH'
        })
    
    if overall_risk['score'] < 30:
        recommendations.append({
            'type': 'INCREASE_RETURNS',
            'title': 'Consider Higher Returns',
            'description': 'Your portfolio is very conservative. Consider adding growth assets for better returns.',
            'priority': 'MEDIUM'
        })
    
    # Check diversification
    for portfolio_risk in portfolio_risks:
        if portfolio_risk['diversification_score'] < 50:
            recommendations.append({
                'type': 'DIVERSIFY',
                'title': f'Diversify {portfolio_risk["portfolio_name"]}',
                'description': 'Add more asset classes to reduce concentration risk.',
                'priority': 'MEDIUM'
            })
    
    return recommendations

def generate_sentiment_history(days):
    """Generate sentiment history data"""
    
    history = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i)
        
        # Simulate sentiment with some trends
        base_sentiment = 0.3 + 0.4 * math.sin(2 * math.pi * i / 30)  # Monthly cycle
        noise = random.uniform(-0.2, 0.2)
        sentiment = max(-1, min(1, base_sentiment + noise))
        
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'sentiment_score': round(sentiment, 3),
            'sentiment_label': 'POSITIVE' if sentiment > 0.2 else 'NEGATIVE' if sentiment < -0.2 else 'NEUTRAL'
        })
    
    return history

