"""
Advanced Analytics & AI Features
"""
import numpy as np
from datetime import datetime, timedelta
from database import Database
from typing import List, Dict, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler

db = Database()

def calculate_clv(customer_id: int) -> float:
    """Calculate Customer Lifetime Value"""
    quotes = db.filter_quotes(customer_id=customer_id)
    if not quotes:
        return 0.0
    
    # Get total accepted/sent value
    total_value = sum([q['total'] for q in quotes if q['status'] in ['accepted', 'sent']])
    
    # Project future value (simplified: assume 30% yearly growth)
    avg_quarterly = total_value / max((len(quotes) / 4), 1)
    clv = total_value + (avg_quarterly * 4 * 3)  # 3 years projection
    
    return clv

def predict_churn_risk(customer_id: int) -> Dict:
    """Predict customer churn risk (0-100%, 0=safe, 100=high risk)"""
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        return {"risk": 0, "reason": "Customer not found"}
    
    quotes = db.filter_quotes(customer_id=customer_id)
    if len(quotes) < 2:
        return {"risk": 30, "reason": "New customer - limited history"}
    
    # Analyze recency
    recent_quotes = [q for q in quotes if datetime.fromisoformat(q['created_at']) > 
                     datetime.now() - timedelta(days=90)]
    
    if not recent_quotes:
        return {"risk": 85, "reason": "No activity in 90 days"}
    
    # Analyze trend
    recent_total = sum([q['total'] for q in recent_quotes])
    all_total = sum([q['total'] for q in quotes])
    
    trend_ratio = recent_total / (all_total + 1)
    
    if trend_ratio < 0.2:
        risk = 60
        reason = "Declining engagement"
    elif trend_ratio < 0.5:
        risk = 40
        reason = "Moderate activity"
    else:
        risk = 15
        reason = "Strong engagement"
    
    return {"risk": int(risk), "reason": reason}

def forecast_revenue(days: int = 90) -> Dict:
    """Forecast revenue for next N days using linear regression"""
    quotes = db.get_all_quotes()
    
    if len(quotes) < 5:
        return {"forecast": 0, "daily_average": 0, "confidence": "Low", "trend": "Unknown"}
    
    # Prepare data (group by day)
    daily_revenue = {}
    for quote in quotes:
        if quote['status'] in ['accepted', 'sent']:
            date = quote['created_at'].split(' ')[0]
            daily_revenue[date] = daily_revenue.get(date, 0) + quote['total']
    
    if len(daily_revenue) < 5:
        return {"forecast": 0, "daily_average": 0, "confidence": "Low", "trend": "Unknown"}
    
    # Convert to arrays
    dates = sorted(daily_revenue.keys())
    revenues = [daily_revenue[d] for d in dates]
    X = np.arange(len(revenues)).reshape(-1, 1)
    y = np.array(revenues)
    
    # Fit model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict
    future_X = np.arange(len(revenues), len(revenues) + days).reshape(-1, 1)
    predictions = model.predict(future_X)
    
    total_forecast = max(0, sum(predictions))
    daily_avg = total_forecast / days
    
    # Calculate confidence (R-squared score)
    score = model.score(X, y)
    confidence = "High" if score > 0.7 else "Medium" if score > 0.3 else "Low"
    
    return {
        "forecast": float(total_forecast),
        "daily_average": float(daily_avg),
        "confidence": confidence,
        "trend": "Positive" if model.coef_[0] > 0 else "Negative"
    }

def get_product_recommendations(customer_id: int) -> List[Dict]:
    """Recommend products based on customer's purchase history"""
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        return []
    
    # Get all products
    all_products = db.get_products()
    
    # Get customer's purchased products
    quotes = db.filter_quotes(customer_id=customer_id)
    purchased_ids = set()
    for quote in quotes:
        items = db.get_quote_items(quote['id'])
        for item in items:
            purchased_ids.add(item['product_id'])
    
    # Get customers in same spending range
    all_quotes = db.get_all_quotes()
    customer_total = sum([q['total'] for q in quotes])
    similar_customers = set()
    for quote in all_quotes:
        if quote['status'] in ['accepted', 'sent']:
            q_total = sum([db.get_all_quotes(q['id']) for q in db.get_all_quotes()])
            if abs(q_total - customer_total) < customer_total * 0.5:
                similar_customers.add(quote['id'])
    
    # Find popular products among similar customers
    product_scores = {}
    for product_id, product in enumerate(all_products):
        if product_id not in purchased_ids:
            # Score: frequency in similar customers * average price
            score = (len([c for c in similar_customers if product_id in c]) + 1) * product['price'] / 1000
            product_scores[product_id] = score
    
    # Sort and return top 5
    top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    recommendations = []
    for prod_id, score in top_products:
        if prod_id < len(all_products):
            product = all_products[prod_id]
            recommendations.append({
                "id": product['id'],
                "name": product['name'],
                "price": product['price'],
                "reason": f"Popular with similar customers",
                "score": float(score)
            })
    
    return recommendations

def get_sales_intelligence() -> Dict:
    """Get overall sales intelligence metrics"""
    all_customers = db.get_customers()
    all_quotes = db.get_all_quotes()
    
    # Calculate metrics
    total_customers = len(all_customers)
    total_quotes = len(all_quotes)
    total_value = sum([q['total'] for q in all_quotes if q['status'] in ['accepted', 'sent']])
    
    # Win rate (accepted / total)
    accepted = len([q for q in all_quotes if q['status'] == 'accepted'])
    win_rate = (accepted / total_quotes * 100) if total_quotes > 0 else 0
    
    # Average deal size
    avg_deal = total_value / max(accepted, 1)
    
    # Top customers
    customer_totals = {}
    for quote in all_quotes:
        if quote['status'] in ['accepted', 'sent']:
            cid = quote.get('customer_id', 0)
            customer_totals[cid] = customer_totals.get(cid, 0) + quote['total']
    
    top_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Recent trend (last 30 days)
    recent_quotes = [q for q in all_quotes if 
                    datetime.fromisoformat(q['created_at']) > datetime.now() - timedelta(days=30)]
    recent_value = sum([q['total'] for q in recent_quotes if q['status'] in ['accepted', 'sent']])
    
    return {
        "total_customers": total_customers,
        "total_quotes": total_quotes,
        "total_value": float(total_value),
        "win_rate": float(win_rate),
        "average_deal_size": float(avg_deal),
        "recent_30_day_value": float(recent_value),
        "top_customers": top_customers,
        "forecast": forecast_revenue(30)
    }

def calculate_health_scores_batch():
    """Calculate health scores for all customers"""
    customers = db.get_customers()
    for customer in customers:
        db.calculate_customer_health_scores(customer['id'])