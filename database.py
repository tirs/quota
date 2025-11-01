import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import uuid
import time

DB_PATH = "quotes.db"

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                phone TEXT,
                company TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                status TEXT DEFAULT 'draft',
                subtotal REAL DEFAULT 0,
                tax_rate REAL DEFAULT 0.1,
                tax_amount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (quote_id) REFERENCES quotes (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'sales_rep',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                theme TEXT DEFAULT 'dark',
                alerts_enabled BOOLEAN DEFAULT 1,
                email_notifications BOOLEAN DEFAULT 1,
                saved_filters TEXT,
                saved_dashboards TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                alert_type TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_health_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL UNIQUE,
                engagement_score REAL DEFAULT 0,
                spend_score REAL DEFAULT 0,
                growth_score REAL DEFAULT 0,
                health_score REAL DEFAULT 0,
                risk_level TEXT DEFAULT 'LOW',
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')

        conn.commit()
        conn.close()
        self._seed_initial_data()

    def _seed_initial_data(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] == 0:
                customers = [
                    ("Acme Corporation", "john.smith@acme.com", "+1-555-0100", "Acme Corp"),
                    ("TechStart Inc", "contact@techstart.com", "+1-555-0101", "TechStart"),
                    ("Global Solutions Ltd", "info@globalsol.com", "+1-555-0102", "Global Solutions"),
                    ("Innovation Hub", "sales@innovhub.com", "+1-555-0103", "Innovation Hub"),
                    ("CloudFirst Industries", "contact@cloudfirst.com", "+1-555-0104", "CloudFirst"),
                    ("DataStream Analytics", "david@datastream.com", "+1-555-0105", "DataStream"),
                    ("SecureNet Systems", "admin@securenet.com", "+1-555-0106", "SecureNet"),
                    ("FinanceFlow Corp", "procurement@financeflow.com", "+1-555-0107", "FinanceFlow"),
                    ("RetailMax Solutions", "vendor@retailmax.com", "+1-555-0108", "RetailMax"),
                    ("MediTech Health", "it@meditech.com", "+1-555-0109", "MediTech"),
                    ("EduLearn Platform", "integration@edulearn.com", "+1-555-0110", "EduLearn"),
                    ("TransLogic Shipping", "tech@translogic.com", "+1-555-0111", "TransLogic"),
                    ("GreenEnergy Solutions", "ops@greenenergy.com", "+1-555-0112", "GreenEnergy"),
                    ("ManufacturePro Industries", "purchase@mfgpro.com", "+1-555-0113", "ManufacturePro"),
                    ("CloudVault Storage", "sales@cloudvault.com", "+1-555-0114", "CloudVault"),
                    ("ByteForce Development", "contact@byteforce.com", "+1-555-0115", "ByteForce"),
                    ("StrategyCore Consulting", "proposals@strategycore.com", "+1-555-0116", "StrategyCore"),
                    ("NetLink Communications", "business@netlink.com", "+1-555-0117", "NetLink"),
                    ("PixelStudio Creative", "projects@pixelstudio.com", "+1-555-0118", "PixelStudio"),
                    ("DataGuard Security", "enterprise@dataguard.com", "+1-555-0119", "DataGuard"),
                    ("CloudScale Hosting", "support@cloudscale.com", "+1-555-0120", "CloudScale"),
                    ("AutoFlow Systems", "vendor@autoflow.com", "+1-555-0121", "AutoFlow"),
                    ("SmartCity Tech", "procurement@smartcity.com", "+1-555-0122", "SmartCity"),
                    ("VisionAI Research", "partnerships@visionai.com", "+1-555-0123", "VisionAI"),
                    ("FutureBuild Construction", "it@futurebuild.com", "+1-555-0124", "FutureBuild"),
                    ("PulseMetrics Analytics", "sales@pulsemetrics.com", "+1-555-0125", "PulseMetrics"),
                    ("SwiftDeploy Services", "operations@swiftdeploy.com", "+1-555-0126", "SwiftDeploy"),
                    ("ZenithCloud Platform", "enterprise@zenithcloud.com", "+1-555-0127", "ZenithCloud"),
                    ("ProActive Solutions", "contact@proactive.com", "+1-555-0128", "ProActive"),
                    ("VectorPoint Systems", "business@vectorpoint.com", "+1-555-0129", "VectorPoint"),
                ]
                for customer in customers:
                    cursor.execute(
                        "INSERT INTO customers (name, email, phone, company) VALUES (?, ?, ?, ?)",
                        customer
                    )

            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                products = [
                    ("Enterprise Software License (Per Year)", "Enterprise software license with full support and updates", 2999.00, "Software"),
                    ("Professional Software License (Per Year)", "Professional tier with business hours support", 1499.00, "Software"),
                    ("Standard Software License (Per Year)", "Basic tier with community support", 799.00, "Software"),
                    ("Cloud Storage (1TB/Month)", "1TB monthly cloud storage with automatic backups", 49.99, "Cloud Storage"),
                    ("Cloud Storage (5TB/Month)", "5TB monthly cloud storage with redundancy", 199.99, "Cloud Storage"),
                    ("Cloud Storage (20TB/Month)", "20TB enterprise cloud storage with dedicated support", 649.99, "Cloud Storage"),
                    ("API Access (Standard Tier)", "Standard API tier with 1M requests/month", 199.00, "API"),
                    ("API Access (Professional Tier)", "Professional tier with 10M requests/month", 499.00, "API"),
                    ("API Access (Enterprise Tier)", "Enterprise tier with unlimited requests", 1999.00, "API"),
                    ("24/7 Premium Support", "Round-the-clock premium technical support package", 499.00, "Support"),
                    ("Business Hours Support", "Support during business hours (9AM-6PM EST)", 299.00, "Support"),
                    ("Email Support Only", "Email-based support with 24-hour response time", 99.00, "Support"),
                    ("Consulting Services (Hourly)", "Expert consulting services by senior architects", 150.00, "Consulting"),
                    ("Senior Architect Consulting (Hourly)", "Enterprise architecture consulting", 250.00, "Consulting"),
                    ("Full Data Migration Service", "Complete data migration with validation", 5000.00, "Services"),
                    ("Partial Data Migration (Per GB)", "Migrate specific data with transformation", 10.00, "Services"),
                    ("Comprehensive Security Audit", "Full security assessment and vulnerability analysis", 3500.00, "Security"),
                    ("Quick Security Scan", "Rapid security vulnerability scan", 1200.00, "Security"),
                    ("Custom Development (Per Hour)", "Bespoke software development services", 125.00, "Development"),
                    ("Full Stack Development (Per Hour)", "Complete application development", 175.00, "Development"),
                    ("Cloud Infrastructure Setup", "Complete cloud infrastructure provisioning and configuration", 2500.00, "Infrastructure"),
                    ("Infrastructure Optimization", "Optimize existing cloud infrastructure for performance", 1800.00, "Infrastructure"),
                    ("Team Training Program (Per Day)", "Comprehensive team training program", 1500.00, "Training"),
                    ("Online Training Course", "Self-paced online training with certification", 499.00, "Training"),
                    ("Database Setup & Configuration", "Professional database installation and tuning", 2000.00, "Database"),
                    ("Database Performance Optimization", "Optimize database for speed and efficiency", 2800.00, "Database"),
                    ("AI/ML Implementation Service", "Custom AI/ML solution implementation", 8500.00, "AI/ML"),
                    ("Machine Learning Model Development", "Build custom ML models for your data", 5500.00, "AI/ML"),
                    ("DevOps Pipeline Setup", "Complete CI/CD pipeline implementation", 4500.00, "DevOps"),
                    ("Monitoring & Analytics Setup", "Real-time monitoring and analytics dashboard", 2200.00, "DevOps"),
                    ("Mobile App Development (Per Platform)", "Native mobile application development", 3500.00, "Development"),
                    ("Web Application Development", "Full-stack web application development", 4200.00, "Development"),
                    ("UI/UX Design Service", "Professional user interface and experience design", 1800.00, "Design"),
                    ("Brand Identity Design", "Complete brand identity and design system", 2500.00, "Design"),
                    ("Technical Documentation Service", "Comprehensive API and system documentation", 1200.00, "Documentation"),
                    ("API Documentation (Per Endpoint)", "Detailed documentation for API endpoints", 50.00, "Documentation"),
                    ("Disaster Recovery Planning", "Complete disaster recovery strategy and implementation", 3200.00, "Services"),
                    ("Backup & Recovery Solution", "Automated backup and disaster recovery setup", 1600.00, "Services"),
                    ("Compliance Audit (SOC2/HIPAA)", "Full compliance audit and certification support", 4500.00, "Compliance"),
                    ("GDPR Compliance Review", "GDPR compliance assessment and recommendations", 2000.00, "Compliance"),
                ]
                for product in products:
                    cursor.execute(
                        "INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)",
                        product
                    )

            cursor.execute("SELECT COUNT(*) FROM quotes")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT id FROM customers ORDER BY id LIMIT 30")
                customer_ids = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT id, price FROM products ORDER BY id")
                products_data = cursor.fetchall()
                
                quote_configs = [
                    {"customer_id": customer_ids[0], "status": "accepted", "tax_rate": 0.08, "items": [(0, 1), (7, 2), (12, 5)]},
                    {"customer_id": customer_ids[1], "status": "sent", "tax_rate": 0.10, "items": [(2, 2), (10, 1)]},
                    {"customer_id": customer_ids[2], "status": "accepted", "tax_rate": 0.08, "items": [(1, 3), (14, 1), (20, 2)]},
                    {"customer_id": customer_ids[3], "status": "draft", "tax_rate": 0.10, "items": [(15, 1)]},
                    {"customer_id": customer_ids[4], "status": "rejected", "tax_rate": 0.08, "items": [(4, 1), (9, 2)]},
                    {"customer_id": customer_ids[5], "status": "sent", "tax_rate": 0.10, "items": [(3, 3), (11, 1), (19, 2)]},
                    {"customer_id": customer_ids[6], "status": "accepted", "tax_rate": 0.08, "items": [(5, 1), (13, 4)]},
                    {"customer_id": customer_ids[7], "status": "draft", "tax_rate": 0.10, "items": [(6, 2), (21, 1)]},
                    {"customer_id": customer_ids[8], "status": "accepted", "tax_rate": 0.08, "items": [(8, 3), (16, 1), (25, 2)]},
                    {"customer_id": customer_ids[9], "status": "sent", "tax_rate": 0.10, "items": [(0, 1), (10, 2), (23, 1)]},
                    {"customer_id": customer_ids[10], "status": "draft", "tax_rate": 0.08, "items": [(12, 1)]},
                    {"customer_id": customer_ids[11], "status": "accepted", "tax_rate": 0.10, "items": [(1, 2), (14, 1), (28, 1)]},
                    {"customer_id": customer_ids[12], "status": "sent", "tax_rate": 0.08, "items": [(4, 3), (9, 1)]},
                    {"customer_id": customer_ids[13], "status": "draft", "tax_rate": 0.10, "items": [(2, 1), (7, 2)]},
                    {"customer_id": customer_ids[14], "status": "accepted", "tax_rate": 0.08, "items": [(15, 2), (20, 1), (26, 1)]},
                    {"customer_id": customer_ids[15], "status": "sent", "tax_rate": 0.10, "items": [(3, 1), (11, 3), (19, 2)]},
                    {"customer_id": customer_ids[16], "status": "rejected", "tax_rate": 0.08, "items": [(5, 1)]},
                    {"customer_id": customer_ids[17], "status": "accepted", "tax_rate": 0.10, "items": [(8, 2), (16, 1), (22, 2)]},
                    {"customer_id": customer_ids[18], "status": "draft", "tax_rate": 0.08, "items": [(0, 1), (6, 1)]},
                    {"customer_id": customer_ids[19], "status": "sent", "tax_rate": 0.10, "items": [(13, 2), (21, 1), (27, 1)]},
                    {"customer_id": customer_ids[20], "status": "accepted", "tax_rate": 0.08, "items": [(4, 1), (10, 2), (25, 1)]},
                    {"customer_id": customer_ids[21], "status": "draft", "tax_rate": 0.10, "items": [(1, 3)]},
                    {"customer_id": customer_ids[22], "status": "accepted", "tax_rate": 0.08, "items": [(7, 2), (14, 1), (29, 1)]},
                    {"customer_id": customer_ids[23], "status": "sent", "tax_rate": 0.10, "items": [(2, 1), (9, 2), (18, 1)]},
                    {"customer_id": customer_ids[24], "status": "draft", "tax_rate": 0.08, "items": [(3, 1), (11, 1)]},
                ]
                
                for config in quote_configs:
                    quote_number = f"QT-{datetime.now().strftime('%Y%m%d')}{config['customer_id']:04d}"
                    cursor.execute(
                        "INSERT INTO quotes (quote_number, customer_id, status, tax_rate, notes) VALUES (?, ?, ?, ?, ?)",
                        (quote_number, config['customer_id'], config['status'], config['tax_rate'], f"Quote for {config['customer_id']}")
                    )
                    quote_id = cursor.lastrowid
                    
                    subtotal = 0
                    for product_idx, quantity in config['items']:
                        product_id, price = products_data[product_idx]
                        line_total = quantity * price
                        subtotal += line_total
                        
                        cursor.execute(
                            "INSERT INTO quote_items (quote_id, product_id, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?)",
                            (quote_id, product_id, quantity, price, line_total)
                        )
                    
                    tax_amount = subtotal * config['tax_rate']
                    total = subtotal + tax_amount
                    
                    cursor.execute(
                        "UPDATE quotes SET subtotal = ?, tax_amount = ?, total = ? WHERE id = ?",
                        (subtotal, tax_amount, total, quote_id)
                    )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Seeding error: {e}")
            conn.close()

    def add_customer(self, name: str, email: str, phone: str, company: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (name, email, phone, company) VALUES (?, ?, ?, ?)",
                (name, email, phone, company)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_customers(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, phone, company FROM customers ORDER BY name")
        customers = [
            {"id": row[0], "name": row[1], "email": row[2], "phone": row[3], "company": row[4]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return customers

    def get_products(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, description, category FROM products ORDER BY category, name")
        products = [
            {"id": row[0], "name": row[1], "price": row[2], "description": row[3], "category": row[4]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return products

    def create_quote(self, customer_id: int, notes: str = "") -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate unique quote number with timestamp + short uuid
        now = datetime.now()
        unique_suffix = str(uuid.uuid4())[:8].upper()
        quote_number = f"QT-{now.strftime('%Y%m%d%H%M%S')}-{unique_suffix}"
        
        # Ensure uniqueness by checking if it exists
        max_retries = 5
        retry = 0
        while retry < max_retries:
            try:
                cursor.execute(
                    "INSERT INTO quotes (quote_number, customer_id, notes) VALUES (?, ?, ?)",
                    (quote_number, customer_id, notes)
                )
                quote_id = cursor.lastrowid
                conn.commit()
                conn.close()
                return quote_id
            except sqlite3.IntegrityError:
                retry += 1
                time.sleep(0.01)  # Small delay
                unique_suffix = str(uuid.uuid4())[:8].upper()
                quote_number = f"QT-{now.strftime('%Y%m%d%H%M%S')}-{unique_suffix}"
        
        conn.close()
        raise Exception("Failed to create unique quote number after retries")

    def add_quote_item(self, quote_id: int, product_id: int, quantity: int, unit_price: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        line_total = quantity * unit_price
        cursor.execute(
            "INSERT INTO quote_items (quote_id, product_id, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?)",
            (quote_id, product_id, quantity, unit_price, line_total)
        )
        conn.commit()
        self._update_quote_totals(quote_id, cursor)
        conn.close()

    def _update_quote_totals(self, quote_id: int, cursor=None):
        close_conn = False
        if cursor is None:
            conn = self.get_connection()
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("SELECT SUM(line_total) FROM quote_items WHERE quote_id = ?", (quote_id,))
        subtotal = cursor.fetchone()[0] or 0

        cursor.execute("SELECT tax_rate FROM quotes WHERE id = ?", (quote_id,))
        tax_rate = cursor.fetchone()[0]

        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        cursor.execute(
            "UPDATE quotes SET subtotal = ?, tax_amount = ?, total = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (subtotal, tax_amount, total, quote_id)
        )
        if close_conn:
            cursor.connection.commit()
            cursor.connection.close()
        else:
            cursor.connection.commit()

    def get_quote(self, quote_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id, q.quote_number, q.customer_id, q.status, q.subtotal, 
                   q.tax_rate, q.tax_amount, q.total, q.notes, q.created_at, q.updated_at
            FROM quotes q WHERE q.id = ?
        """, (quote_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0], "quote_number": row[1], "customer_id": row[2], "status": row[3],
            "subtotal": row[4], "tax_rate": row[5], "tax_amount": row[6], "total": row[7],
            "notes": row[8], "created_at": row[9], "updated_at": row[10]
        }

    def get_quote_items(self, quote_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT qi.id, p.name, qi.quantity, qi.unit_price, qi.line_total, qi.product_id
            FROM quote_items qi
            JOIN products p ON qi.product_id = p.id
            WHERE qi.quote_id = ?
        """, (quote_id,))
        items = [
            {"id": row[0], "name": row[1], "quantity": row[2], "unit_price": row[3], "line_total": row[4], "product_id": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return items

    def get_all_quotes(self, status: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT q.id, q.quote_number, c.name, q.status, q.total, q.created_at
                FROM quotes q
                JOIN customers c ON q.customer_id = c.id
                WHERE q.status = ?
                ORDER BY q.created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT q.id, q.quote_number, c.name, q.status, q.total, q.created_at
                FROM quotes q
                JOIN customers c ON q.customer_id = c.id
                ORDER BY q.created_at DESC
            """)
        quotes = [
            {"id": row[0], "quote_number": row[1], "customer": row[2], "status": row[3], "total": row[4], "created_at": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return quotes

    def update_quote_status(self, quote_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE quotes SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, quote_id)
        )
        conn.commit()
        conn.close()

    def update_quote_tax(self, quote_id: int, tax_rate: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE quotes SET tax_rate = ? WHERE id = ?", (tax_rate, quote_id))
        conn.commit()
        self._update_quote_totals(quote_id, cursor)
        conn.close()

    def delete_quote_item(self, item_id: int, quote_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quote_items WHERE id = ?", (item_id,))
        conn.commit()
        self._update_quote_totals(quote_id, cursor)
        conn.close()

    def delete_quote(self, quote_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quote_items WHERE quote_id = ?", (quote_id,))
        cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
        conn.commit()
        conn.close()

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, phone, company FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "email": row[2], "phone": row[3], "company": row[4]}

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "price": row[2]}

    # User Management Methods
    def create_user(self, username: str, email: str, password_hash: str, role: str = 'sales_rep') -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO user_preferences (user_id, theme) VALUES (?, ?)",
            (user_id, 'dark')
        )
        conn.commit()
        conn.close()
        return user_id

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "username": row[1], "email": row[2], "role": row[3]}

    def get_all_users(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, role FROM users ORDER BY username")
        users = [{"id": row[0], "username": row[1], "email": row[2], "role": row[3]} for row in cursor.fetchall()]
        conn.close()
        return users

    def update_user_role(self, user_id: int, role: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
        conn.close()

    # User Preferences
    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, theme, alerts_enabled, email_notifications, saved_filters, saved_dashboards FROM user_preferences WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "theme": row[1], "alerts_enabled": row[2], 
            "email_notifications": row[3], "saved_filters": row[4], "saved_dashboards": row[5]
        }

    def update_user_preferences(self, user_id: int, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in ['theme', 'alerts_enabled', 'email_notifications', 'saved_filters', 'saved_dashboards']:
                updates.append(f"{key} = ?")
                values.append(value)
        if updates:
            values.append(user_id)
            cursor.execute(f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_id = ?", values)
            conn.commit()
        conn.close()

    # Alert Management
    def create_alert(self, user_id: int, alert_type: str, title: str, message: str, severity: str = 'info') -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (user_id, alert_type, title, message, severity) VALUES (?, ?, ?, ?, ?)",
            (user_id, alert_type, title, message, severity)
        )
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id

    def get_unread_alerts(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, alert_type, title, message, severity, created_at FROM alerts WHERE user_id = ? AND read = 0 ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        alerts = [
            {"id": row[0], "alert_type": row[1], "title": row[2], "message": row[3], "severity": row[4], "created_at": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return alerts

    def mark_alert_as_read(self, alert_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET read = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()

    # Audit Logging
    def log_action(self, user_id: int, action: str, entity_type: str = None, entity_id: int = None, details: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, entity_type, entity_id, details)
        )
        conn.commit()
        conn.close()

    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT al.id, u.username, al.action, al.entity_type, al.entity_id, al.details, al.created_at 
               FROM audit_logs al 
               LEFT JOIN users u ON al.user_id = u.id
               ORDER BY al.created_at DESC LIMIT ?""",
            (limit,)
        )
        logs = [
            {"id": row[0], "user": row[1], "action": row[2], "entity_type": row[3], "entity_id": row[4], "details": row[5], "created_at": row[6]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return logs

    # Customer Health Scores
    def calculate_customer_health_scores(self, customer_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate engagement score (based on number of quotes)
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE customer_id = ?", (customer_id,))
        quote_count = cursor.fetchone()[0]
        engagement_score = min(quote_count * 20, 100)
        
        # Calculate spend score (based on total spend)
        cursor.execute("SELECT SUM(total) FROM quotes WHERE customer_id = ? AND status IN ('accepted', 'sent')", (customer_id,))
        total_spend = cursor.fetchone()[0] or 0
        spend_score = min((total_spend / 50000) * 100, 100)
        
        # Calculate growth score (based on recent trends)
        cursor.execute("""
            SELECT SUM(total) FROM quotes 
            WHERE customer_id = ? AND status IN ('accepted', 'sent')
            AND created_at > datetime('now', '-90 days')
        """, (customer_id,))
        recent_spend = cursor.fetchone()[0] or 0
        growth_score = min((recent_spend / (total_spend + 1)) * 100, 100)
        
        # Overall health score (weighted average)
        health_score = (engagement_score * 0.3 + spend_score * 0.5 + growth_score * 0.2)
        
        # Determine risk level
        if health_score >= 75:
            risk_level = "LOW"
        elif health_score >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Update or insert
        cursor.execute(
            "SELECT id FROM customer_health_scores WHERE customer_id = ?",
            (customer_id,)
        )
        if cursor.fetchone():
            cursor.execute(
                """UPDATE customer_health_scores 
                   SET engagement_score = ?, spend_score = ?, growth_score = ?, health_score = ?, risk_level = ?, last_calculated = CURRENT_TIMESTAMP
                   WHERE customer_id = ?""",
                (engagement_score, spend_score, growth_score, health_score, risk_level, customer_id)
            )
        else:
            cursor.execute(
                """INSERT INTO customer_health_scores (customer_id, engagement_score, spend_score, growth_score, health_score, risk_level)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (customer_id, engagement_score, spend_score, growth_score, health_score, risk_level)
            )
        
        conn.commit()
        conn.close()

    def get_customer_health_score(self, customer_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, engagement_score, spend_score, growth_score, health_score, risk_level FROM customer_health_scores WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "engagement_score": row[1], "spend_score": row[2], 
            "growth_score": row[3], "health_score": row[4], "risk_level": row[5]
        }

    def get_all_customer_health_scores(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT chs.customer_id, c.name, chs.engagement_score, chs.spend_score, 
                      chs.growth_score, chs.health_score, chs.risk_level
               FROM customer_health_scores chs
               JOIN customers c ON chs.customer_id = c.id
               ORDER BY chs.health_score DESC"""
        )
        scores = [
            {"customer_id": row[0], "name": row[1], "engagement_score": row[2], "spend_score": row[3],
             "growth_score": row[4], "health_score": row[5], "risk_level": row[6]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return scores

    # Search and Filter
    def search_quotes(self, search_term: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT DISTINCT q.id, q.quote_number, c.name, q.status, q.total, q.created_at
            FROM quotes q
            JOIN customers c ON q.customer_id = c.id
            WHERE q.quote_number LIKE ? OR c.name LIKE ? OR c.email LIKE ?
            ORDER BY q.created_at DESC
        """, (search_pattern, search_pattern, search_pattern))
        quotes = [
            {"id": row[0], "quote_number": row[1], "customer": row[2], "status": row[3], "total": row[4], "created_at": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return quotes

    def filter_quotes(self, status: str = None, min_amount: float = None, max_amount: float = None, 
                     customer_id: int = None, days_back: int = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT q.id, q.quote_number, c.name, q.status, q.total, q.created_at
            FROM quotes q
            JOIN customers c ON q.customer_id = c.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND q.status = ?"
            params.append(status)
        if min_amount is not None:
            query += " AND q.total >= ?"
            params.append(min_amount)
        if max_amount is not None:
            query += " AND q.total <= ?"
            params.append(max_amount)
        if customer_id:
            query += " AND q.customer_id = ?"
            params.append(customer_id)
        if days_back:
            query += f" AND q.created_at > datetime('now', '-{days_back} days')"
        
        query += " ORDER BY q.created_at DESC"
        
        cursor.execute(query, params)
        quotes = [
            {"id": row[0], "quote_number": row[1], "customer": row[2], "status": row[3], "total": row[4], "created_at": row[5]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return quotes