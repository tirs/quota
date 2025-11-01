"""
Real-Time Alert System Manager
"""
from database import Database
from typing import Dict, List
from datetime import datetime, timedelta

db = Database()

class AlertManager:
    """Manages real-time alerts and notifications"""
    
    @staticmethod
    def check_high_value_quotes(threshold: float = 5000) -> List[Dict]:
        """Check for new high-value quotes and create alerts"""
        alerts_created = []
        all_quotes = db.get_all_quotes()
        
        # Get recent quotes (last hour)
        recent_quotes = [
            q for q in all_quotes 
            if q['total'] >= threshold
            and datetime.fromisoformat(q['created_at']) > datetime.now() - timedelta(hours=1)
        ]
        
        # Create alerts for admin users
        for quote in recent_quotes:
            users = db.get_all_users()
            admin_users = [u for u in users if u['role'] in ['admin', 'manager']]
            
            for user in admin_users:
                alert_id = db.create_alert(
                    user['id'],
                    'high_value_quote',
                    f"High-Value Quote Created",
                    f"Quote {quote['quote_number']} for {quote['customer']} worth {format_currency(quote['total'])} has been created!",
                    'success'
                )
                alerts_created.append(alert_id)
        
        return alerts_created

    @staticmethod
    def check_revenue_drop(threshold_percent: float = 20) -> List[Dict]:
        """Check for revenue drops and create alerts"""
        alerts_created = []
        
        all_quotes = db.get_all_quotes()
        if len(all_quotes) < 2:
            return []
        
        # Compare this month to last month
        today = datetime.now()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        
        this_month_value = sum([
            q['total'] for q in all_quotes 
            if q['status'] in ['accepted', 'sent']
            and datetime.fromisoformat(q['created_at']).date() >= this_month_start.date()
        ])
        
        last_month_value = sum([
            q['total'] for q in all_quotes 
            if q['status'] in ['accepted', 'sent']
            and last_month_start.date() <= datetime.fromisoformat(q['created_at']).date() <= last_month_end.date()
        ])
        
        if last_month_value > 0:
            drop_percent = ((last_month_value - this_month_value) / last_month_value) * 100
            if drop_percent > threshold_percent:
                users = db.get_all_users()
                for user in users:
                    if user['role'] in ['admin', 'manager']:
                        alert_id = db.create_alert(
                            user['id'],
                            'revenue_drop',
                            f"Revenue Drop Detected",
                            f"Revenue has dropped {drop_percent:.1f}% compared to last month. Please review sales strategy.",
                            'warning'
                        )
                        alerts_created.append(alert_id)
        
        return alerts_created

    @staticmethod
    def check_customer_churn_risk() -> List[Dict]:
        """Check for customers at churn risk and create alerts"""
        alerts_created = []
        
        customers = db.get_customers()
        for customer in customers:
            # Check if customer has quotes
            quotes = db.filter_quotes(customer_id=customer['id'])
            
            if not quotes:
                continue
            
            # Check recent activity
            recent_quotes = [
                q for q in quotes 
                if datetime.fromisoformat(q['created_at']) > datetime.now() - timedelta(days=90)
            ]
            
            # If no activity in 90 days, flag as churn risk
            if not recent_quotes and len(quotes) > 0:
                users = db.get_all_users()
                for user in users:
                    if user['role'] in ['admin', 'manager', 'sales_rep']:
                        alert_id = db.create_alert(
                            user['id'],
                            'churn_risk',
                            f"Customer At Risk: {customer['name']}",
                            f"Customer {customer['name']} has had no activity in 90 days. Consider outreach.",
                            'danger'
                        )
                        alerts_created.append(alert_id)
        
        return alerts_created

    @staticmethod
    def create_quote_status_alert(quote_id: int, new_status: str, user_id: int = None):
        """Create an alert when quote status changes"""
        quote = db.get_quote(quote_id)
        customer = db.get_customer_by_id(quote['customer_id'])
        
        if new_status == 'sent':
            message = f"Quote {quote['quote_number']} for {customer['name']} has been sent!"
            severity = 'info'
        elif new_status == 'accepted':
            message = f"Quote {quote['quote_number']} from {customer['name']} has been accepted!"
            severity = 'success'
        elif new_status == 'rejected':
            message = f"Quote {quote['quote_number']} from {customer['name']} has been rejected."
            severity = 'danger'
        else:
            return None
        
        # Alert all managers and admins
        users = db.get_all_users()
        for user in users:
            if user['role'] in ['admin', 'manager']:
                db.create_alert(user['id'], 'quote_status_change', f"Quote Status: {new_status.upper()}", message, severity)

    @staticmethod
    def format_currency(value: float) -> str:
        """Format value as currency"""
        return f"${value:,.2f}"

    @staticmethod
    def run_all_checks(admin_user_id: int = 1) -> Dict:
        """Run all alert checks"""
        results = {
            'high_value': AlertManager.check_high_value_quotes(),
            'revenue_drop': AlertManager.check_revenue_drop(),
            'churn_risk': AlertManager.check_customer_churn_risk(),
        }
        return results

def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"

def get_alert_color(severity: str) -> str:
    """Get color for alert severity"""
    colors = {
        'info': '#58A6FF',      # Blue
        'success': '#3FB950',   # Green
        'warning': '#FFB81C',   # Orange/Yellow
        'danger': '#FF006E'     # Pink/Red
    }
    return colors.get(severity, '#8B949E')

def get_alert_icon(alert_type: str) -> str:
    """Get icon for alert type"""
    icons = {
        'high_value_quote': '[HIGH]',
        'revenue_drop': '[DROP]',
        'churn_risk': '[RISK]',
        'quote_status_change': '[UPDATE]',
        'system': '[INFO]'
    }
    return icons.get(alert_type, '[ALERT]')