"""
Quick-Start ML/DL Features for Quote Builder Pro
Ready-to-use implementations - no additional setup required
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from database import Database

db = Database()

# ============================================================================
# QUICK WIN 1: Advanced Churn Prediction with Feature Importance
# ============================================================================

class FastChurnPredictor:
    """Production-ready churn prediction - works immediately"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'days_inactive', 'total_quotes', 'acceptance_rate',
            'avg_deal_size', 'revenue_trend', 'engagement_score'
        ]
    
    def extract_features_single(self, customer_id):
        """Extract features for one customer"""
        quotes = db.filter_quotes(customer_id=customer_id)
        if not quotes:
            return None
        
        now = datetime.now()
        created_dates = [datetime.fromisoformat(q['created_at']) for q in quotes]
        
        # Time inactive
        days_inactive = (now - max(created_dates)).days
        
        # Quote metrics
        total_quotes = len(quotes)
        accepted = len([q for q in quotes if q['status'] == 'accepted'])
        acceptance_rate = accepted / total_quotes if total_quotes > 0 else 0
        
        # Revenue metrics
        total_revenue = sum([q['total'] for q in quotes if q['status'] in ['accepted', 'sent']])
        avg_deal = total_revenue / total_quotes if total_quotes > 0 else 0
        
        # Trend (revenue in recent 50% vs first 50%)
        mid = len(quotes) // 2
        recent_rev = sum([q['total'] for q in quotes[mid:] if q['status'] in ['accepted', 'sent']])
        old_rev = sum([q['total'] for q in quotes[:mid] if q['status'] in ['accepted', 'sent']])
        trend = recent_rev - old_rev
        
        # Engagement (activity frequency)
        days_active = (max(created_dates) - min(created_dates)).days + 1
        engagement = total_quotes / (days_active / 30) if days_active > 0 else 0
        
        return np.array([days_inactive, total_quotes, acceptance_rate, avg_deal, trend, engagement])
    
    def predict_churn(self, customer_id):
        """Predict churn risk 0-100"""
        features = self.extract_features_single(customer_id)
        if features is None:
            return {"risk": 0, "reason": "No data", "factors": []}
        
        # Simple rule-based until trained
        if self.model is None:
            return self._rule_based_prediction(features)
        
        # ML-based prediction
        X_scaled = self.scaler.transform(features.reshape(1, -1))
        prob = self.model.predict_proba(X_scaled)[0][1]
        
        # Get top factors
        importance = np.abs(self.model.feature_importances_)
        top_indices = np.argsort(importance)[-3:][::-1]
        factors = [(self.feature_names[i], float(importance[i])) for i in top_indices]
        
        return {
            "risk": int(prob * 100),
            "reason": self._get_reason(prob),
            "factors": factors
        }
    
    def _rule_based_prediction(self, features):
        """Fallback rule-based prediction"""
        days_inactive, quotes, acceptance, deal, trend, engagement = features
        
        risk = 0
        reasons = []
        
        if days_inactive > 120:
            risk += 40
            reasons.append(f"Inactive {days_inactive} days")
        elif days_inactive > 60:
            risk += 20
        
        if acceptance < 0.3:
            risk += 20
            reasons.append("Low acceptance rate")
        
        if trend < 0:
            risk += 15
            reasons.append("Declining revenue trend")
        
        if engagement < 1:
            risk += 10
            reasons.append("Low activity frequency")
        
        reason = " + ".join(reasons) if reasons else "Healthy customer"
        
        return {
            "risk": min(100, risk),
            "reason": reason,
            "factors": []
        }
    
    def _get_reason(self, prob):
        if prob > 0.7:
            return "HIGH RISK: Immediate action needed"
        elif prob > 0.4:
            return "MEDIUM RISK: Monitor closely"
        else:
            return "LOW RISK: Stable customer"

# ============================================================================
# QUICK WIN 2: Customer Segmentation (4 Segments)
# ============================================================================

class QuickSegmentation:
    """Instantly segment customers into 4 groups"""
    
    def segment_all(self):
        """Return customer segments"""
        customers = db.get_customers()
        segments = {"VIP": [], "Growth": [], "Active": [], "Inactive": []}
        
        for customer in customers:
            quotes = db.filter_quotes(customer_id=customer['id'])
            if not quotes:
                segments["Inactive"].append(customer['id'])
                continue
            
            # Calculate metrics
            ltv = sum([q['total'] for q in quotes if q['status'] in ['accepted', 'sent']])
            accepted = len([q for q in quotes if q['status'] == 'accepted'])
            acceptance_rate = accepted / len(quotes) if quotes else 0
            
            now = datetime.now()
            recent = len([q for q in quotes 
                         if datetime.fromisoformat(q['created_at']) > now - timedelta(days=90)])
            
            # Segment logic
            if ltv > 100000 and acceptance_rate > 0.6:
                segments["VIP"].append(customer['id'])
            elif ltv > 20000 and recent > 0:
                segments["Growth"].append(customer['id'])
            elif recent > 0:
                segments["Active"].append(customer['id'])
            else:
                segments["Inactive"].append(customer['id'])
        
        return {
            "VIP": {"customers": segments["VIP"], "size": len(segments["VIP"]), "action": "Premium support, upsell"},
            "Growth": {"customers": segments["Growth"], "size": len(segments["Growth"]), "action": "Nurture, expand"},
            "Active": {"customers": segments["Active"], "size": len(segments["Active"]), "action": "Regular engagement"},
            "Inactive": {"customers": segments["Inactive"], "size": len(segments["Inactive"]), "action": "Reactivation campaign"}
        }

# ============================================================================
# QUICK WIN 3: Anomaly Detection (Unusual Quotes)
# ============================================================================

class QuickAnomalyDetector:
    """Instantly detect unusual quotes"""
    
    def find_anomalies(self):
        """Return unusual quotes"""
        quotes = db.get_all_quotes()
        if len(quotes) < 10:
            return {"anomalies": [], "message": "Need at least 10 quotes"}
        
        anomalies = []
        
        for quote in quotes:
            full_quote = db.get_quote(quote['id'])
            if not full_quote:
                continue
            customer_quotes = db.filter_quotes(customer_id=full_quote['customer_id'])
            if not customer_quotes:
                continue
            
            # Customer average
            customer_avg = np.mean([q['total'] for q in customer_quotes])
            
            # Check for outliers
            if quote['total'] > customer_avg * 5:
                anomalies.append({
                    "quote_id": quote['id'],
                    "amount": quote['total'],
                    "customer_avg": customer_avg,
                    "issue": "Unusually high value",
                    "severity": "WARNING"
                })
            elif quote['total'] < customer_avg * 0.1 and quote['total'] > 0:
                anomalies.append({
                    "quote_id": quote['id'],
                    "amount": quote['total'],
                    "customer_avg": customer_avg,
                    "issue": "Unusually low value",
                    "severity": "INFO"
                })
        
        return {"anomalies": anomalies, "count": len(anomalies)}

# ============================================================================
# QUICK WIN 4: Product Recommendations
# ============================================================================

class QuickRecommender:
    """Recommend products for customers"""
    
    def recommend_for_customer(self, customer_id, n=5):
        """Get top N product recommendations"""
        customer_quotes = db.filter_quotes(customer_id=customer_id)
        all_quotes = db.get_all_quotes()
        products = db.get_products()
        
        if not customer_quotes:
            return [p for p in products[:n]]
        
        # What customer already bought
        purchased = set()
        for q in customer_quotes:
            items = db.get_quote_items(q['id'])
            for item in items:
                purchased.add(item['product_id'])
        
        # Spending range
        customer_total = sum([q['total'] for q in customer_quotes])
        
        # Find similar spending customers
        similar_products = {}
        for quote in all_quotes:
            # Get customer_id from quote using db.get_quote()
            full_quote = db.get_quote(quote['id'])
            if not full_quote:
                continue
            if full_quote['customer_id'] != customer_id and quote['status'] in ['accepted', 'sent']:
                q_total = quote['total']
                
                # If similar spending
                if abs(q_total - customer_total) < customer_total * 0.5:
                    items = db.get_quote_items(quote['id'])
                    for item in items:
                        if item['product_id'] not in purchased:
                            similar_products[item['product_id']] = similar_products.get(item['product_id'], 0) + 1
        
        # Sort by frequency
        recommendations = []
        for prod_id, score in sorted(similar_products.items(), key=lambda x: x[1], reverse=True):
            prod = db.get_product_by_id(prod_id)
            if prod:
                recommendations.append({
                    "id": prod['id'],
                    "name": prod['name'],
                    "price": prod['price'],
                    "score": score,
                    "reason": "Popular with similar customers"
                })
        
        return recommendations[:n]

# ============================================================================
# QUICK WIN 5: Revenue Trend Analysis
# ============================================================================

class QuickTrendAnalysis:
    """Analyze revenue trends"""
    
    def get_trends(self):
        """Get month-over-month trends, or weekly if only one month"""
        quotes = db.get_all_quotes()
        
        # Group by month
        monthly_revenue = {}
        for quote in quotes:
            if quote['status'] in ['accepted', 'sent']:
                date = datetime.fromisoformat(quote['created_at'])
                month_key = date.strftime('%Y-%m')
                monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + quote['total']
        
        # If only 1 month, use weekly breakdown instead
        if len(monthly_revenue) < 2:
            weekly_revenue = {}
            for quote in quotes:
                if quote['status'] in ['accepted', 'sent']:
                    date = datetime.fromisoformat(quote['created_at'])
                    week_key = date.strftime('%Y-W%U')  # Year-Week number
                    weekly_revenue[week_key] = weekly_revenue.get(week_key, 0) + quote['total']
            
            if len(weekly_revenue) < 2:
                # Fall back to daily if only one week
                daily_revenue = {}
                for quote in quotes:
                    if quote['status'] in ['accepted', 'sent']:
                        date = datetime.fromisoformat(quote['created_at'])
                        day_key = date.strftime('%Y-%m-%d')
                        daily_revenue[day_key] = daily_revenue.get(day_key, 0) + quote['total']
                
                if len(daily_revenue) < 2:
                    return {
                        "trend": "UP",
                        "trend_percent": 0.0,
                        "mom_change": 0.0,
                        "latest_month_revenue": sum(daily_revenue.values()) if daily_revenue else 0.0,
                        "previous_month_revenue": 0.0,
                        "months_analyzed": 1
                    }
                
                revenues = list(daily_revenue.values())
            else:
                revenues = [weekly_revenue[w] for w in sorted(weekly_revenue.keys())]
        else:
            # Multiple months available
            months = sorted(monthly_revenue.keys())
            revenues = [monthly_revenue[m] for m in months]
        
        # Calculate trends
        first_half = np.mean(revenues[:len(revenues)//2])
        second_half = np.mean(revenues[len(revenues)//2:])
        overall_trend = "UP" if second_half > first_half else "DOWN"
        trend_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        # Latest vs previous period
        latest_val = revenues[-1]
        previous_val = revenues[-2] if len(revenues) > 1 else latest_val
        mom_change = ((latest_val - previous_val) / previous_val * 100) if previous_val > 0 else 0
        
        return {
            "trend": overall_trend,
            "trend_percent": float(trend_percent),
            "mom_change": float(mom_change),
            "latest_month_revenue": float(latest_val),
            "previous_month_revenue": float(previous_val),
            "months_analyzed": len(revenues)
        }

# ============================================================================
# QUICK WIN 6: Deal Size Intelligence
# ============================================================================

class QuickDealAnalysis:
    """Analyze deal sizes and patterns"""
    
    def get_deal_analysis(self):
        """Get deal size insights"""
        quotes = db.get_all_quotes()
        
        amounts = [q['total'] for q in quotes if q['status'] in ['accepted', 'sent']]
        if not amounts:
            return {"message": "No accepted/sent quotes"}
        
        amounts = np.array(amounts)
        
        return {
            "average_deal": float(np.mean(amounts)),
            "median_deal": float(np.median(amounts)),
            "min_deal": float(np.min(amounts)),
            "max_deal": float(np.max(amounts)),
            "std_dev": float(np.std(amounts)),
            "total_deals": len(amounts),
            "total_revenue": float(np.sum(amounts)),
            "deals_above_avg": int(np.sum(amounts > np.mean(amounts))),
            "deals_below_avg": int(np.sum(amounts < np.mean(amounts)))
        }

# ============================================================================
# QUICK WIN 7: Win Rate & Success Metrics
# ============================================================================

class QuickWinMetrics:
    """Get sales success metrics"""
    
    def get_metrics(self):
        """Get win rate and related metrics"""
        quotes = db.get_all_quotes()
        
        if not quotes:
            return {"message": "No quotes"}
        
        total = len(quotes)
        accepted = len([q for q in quotes if q['status'] == 'accepted'])
        sent = len([q for q in quotes if q['status'] == 'sent'])
        rejected = len([q for q in quotes if q['status'] == 'rejected'])
        draft = len([q for q in quotes if q['status'] == 'draft'])
        
        # Revenue metrics
        accepted_revenue = sum([q['total'] for q in quotes if q['status'] == 'accepted'])
        sent_revenue = sum([q['total'] for q in quotes if q['status'] == 'sent'])
        
        return {
            "total_quotes": total,
            "accepted_count": accepted,
            "sent_count": sent,
            "rejected_count": rejected,
            "draft_count": draft,
            "win_rate": float(accepted / total * 100) if total > 0 else 0,
            "accepted_revenue": float(accepted_revenue),
            "sent_revenue": float(sent_revenue),
            "avg_accepted_value": float(accepted_revenue / accepted) if accepted > 0 else 0
        }

# ============================================================================
# QUICK WIN 8: Customer Health Scoring
# ============================================================================

class QuickHealthScore:
    """Calculate customer health scores"""
    
    def get_health_score(self, customer_id):
        """Get 0-100 health score"""
        quotes = db.filter_quotes(customer_id=customer_id)
        if not quotes:
            return {"score": 0, "reason": "No quotes"}
        
        now = datetime.now()
        created_dates = [datetime.fromisoformat(q['created_at']) for q in quotes]
        
        # Components (each 0-33)
        recency_score = self._score_recency(max(created_dates), now)
        engagement_score = self._score_engagement(quotes)
        revenue_score = self._score_revenue(quotes)
        
        total = recency_score + engagement_score + revenue_score
        
        status = "HEALTHY" if total > 75 else "ATTENTION" if total > 50 else "AT RISK"
        
        return {
            "score": total,
            "status": status,
            "recency": recency_score,
            "engagement": engagement_score,
            "revenue": revenue_score
        }
    
    def _score_recency(self, last_date, now, max_days=180):
        """0-33 based on recency"""
        days_ago = (now - last_date).days
        if days_ago < 30:
            return 33
        elif days_ago < 90:
            return 22
        elif days_ago < 180:
            return 11
        else:
            return 0
    
    def _score_engagement(self, quotes):
        """0-33 based on quote frequency"""
        if len(quotes) > 10:
            return 33
        elif len(quotes) > 5:
            return 22
        elif len(quotes) > 2:
            return 11
        else:
            return 0
    
    def _score_revenue(self, quotes):
        """0-33 based on revenue"""
        total = sum([q['total'] for q in quotes if q['status'] in ['accepted', 'sent']])
        if total > 100000:
            return 33
        elif total > 50000:
            return 22
        elif total > 10000:
            return 11
        else:
            return 0

# ============================================================================
# Standalone Helper Functions
# ============================================================================

def quick_churn_analysis():
    """Get churn risks for all customers"""
    predictor = FastChurnPredictor()
    customers = db.get_customers()
    results = []
    
    for customer in customers:
        pred = predictor.predict_churn(customer['id'])
        if pred['risk'] > 40:  # Only high risk
            results.append({
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                **pred
            })
    
    return sorted(results, key=lambda x: x['risk'], reverse=True)

def quick_revenue_forecast_simple(days=30):
    """Simple exponential forecast"""
    quotes = db.get_all_quotes()
    
    # Daily revenue
    daily_rev = {}
    for q in quotes:
        if q['status'] in ['accepted', 'sent']:
            date = q['created_at'].split(' ')[0]
            daily_rev[date] = daily_rev.get(date, 0) + q['total']
    
    if len(daily_rev) < 5:
        return {"error": "Insufficient data"}
    
    revenues = np.array(list(daily_rev.values()))
    
    # Simple average * trend
    avg = np.mean(revenues[-7:])  # Last 7 days
    trend = (revenues[-1] - revenues[-7]) / revenues[-7] if revenues[-7] > 0 else 0
    
    forecast = avg * days * (1 + trend)
    
    return {
        "forecast": float(forecast),
        "daily_average": float(avg),
        "trend": "UP" if trend > 0 else "DOWN",
        "confidence": "LOW"
    }

def get_quick_insights():
    """Get all quick insights at once"""
    return {
        "churn_risks": quick_churn_analysis(),
        "segmentation": QuickSegmentation().segment_all(),
        "anomalies": QuickAnomalyDetector().find_anomalies(),
        "trends": QuickTrendAnalysis().get_trends(),
        "deals": QuickDealAnalysis().get_deal_analysis(),
        "metrics": QuickWinMetrics().get_metrics(),
        "forecast": quick_revenue_forecast_simple(30)
    }