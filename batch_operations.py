"""
Batch Operations Engine for bulk imports and operations
"""
import pandas as pd
import io
from typing import List, Dict, Tuple
from database import Database

db = Database()

def batch_import_quotes_from_csv(csv_content: str) -> Tuple[int, List[str]]:
    """
    Import quotes from CSV.
    Expected columns: customer_name, product_name, quantity, notes (optional)
    Returns: (success_count, errors)
    """
    success_count = 0
    errors = []
    
    try:
        df = pd.read_csv(io.StringIO(csv_content))
    except Exception as e:
        return 0, [f"CSV parsing error: {str(e)}"]
    
    # Validate columns
    required_columns = ['customer_name', 'product_name', 'quantity']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, [f"Missing columns: {', '.join(missing_cols)}"]
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            customer_name = str(row['customer_name']).strip()
            product_name = str(row['product_name']).strip()
            quantity = int(row['quantity'])
            notes = str(row.get('notes', '')) if 'notes' in df.columns else ""
            
            # Validate
            if not customer_name or not product_name or quantity < 1:
                errors.append(f"Row {idx + 2}: Invalid data")
                continue
            
            # Find customer
            customers = db.get_customers()
            customer = next((c for c in customers if c['name'].lower() == customer_name.lower()), None)
            if not customer:
                errors.append(f"Row {idx + 2}: Customer '{customer_name}' not found")
                continue
            
            # Find product
            products = db.get_products()
            product = next((p for p in products if p['name'].lower() == product_name.lower()), None)
            if not product:
                errors.append(f"Row {idx + 2}: Product '{product_name}' not found")
                continue
            
            # Create quote
            quote_id = db.create_quote(customer['id'], notes)
            db.add_quote_item(quote_id, product['id'], quantity, product['price'])
            
            success_count += 1
        
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    return success_count, errors

def batch_send_quotes(quote_ids: List[int]) -> Tuple[int, int]:
    """
    Batch update quotes to 'sent' status
    Returns: (success_count, failed_count)
    """
    success_count = 0
    failed_count = 0
    
    for quote_id in quote_ids:
        try:
            quote = db.get_quote(quote_id)
            if quote and quote['status'] in ['draft', 'draft']:
                db.update_quote_status(quote_id, 'sent')
                success_count += 1
            else:
                failed_count += 1
        except:
            failed_count += 1
    
    return success_count, failed_count

def batch_update_status(quote_ids: List[int], new_status: str) -> Tuple[int, int]:
    """
    Batch update quotes to a new status
    Returns: (success_count, failed_count)
    """
    success_count = 0
    failed_count = 0
    
    valid_statuses = ['draft', 'sent', 'accepted', 'rejected']
    if new_status not in valid_statuses:
        return 0, len(quote_ids)
    
    for quote_id in quote_ids:
        try:
            quote = db.get_quote(quote_id)
            if quote:
                db.update_quote_status(quote_id, new_status)
                success_count += 1
            else:
                failed_count += 1
        except:
            failed_count += 1
    
    return success_count, failed_count

def batch_delete_quotes(quote_ids: List[int]) -> Tuple[int, int]:
    """
    Batch delete quotes
    Returns: (success_count, failed_count)
    """
    success_count = 0
    failed_count = 0
    
    for quote_id in quote_ids:
        try:
            db.delete_quote(quote_id)
            success_count += 1
        except:
            failed_count += 1
    
    return success_count, failed_count

def batch_create_customers_from_csv(csv_content: str) -> Tuple[int, List[str]]:
    """
    Batch create customers from CSV.
    Expected columns: name, email, phone (optional), company (optional)
    Returns: (success_count, errors)
    """
    success_count = 0
    errors = []
    
    try:
        df = pd.read_csv(io.StringIO(csv_content))
    except Exception as e:
        return 0, [f"CSV parsing error: {str(e)}"]
    
    required_columns = ['name', 'email']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, [f"Missing columns: {', '.join(missing_cols)}"]
    
    for idx, row in df.iterrows():
        try:
            name = str(row['name']).strip()
            email = str(row['email']).strip()
            phone = str(row.get('phone', '')) if 'phone' in df.columns else ""
            company = str(row.get('company', '')) if 'company' in df.columns else ""
            
            if not name or not email:
                errors.append(f"Row {idx + 2}: Name and email required")
                continue
            
            # Check if customer exists
            existing = next((c for c in db.get_customers() if c['name'].lower() == name.lower()), None)
            if existing:
                errors.append(f"Row {idx + 2}: Customer '{name}' already exists")
                continue
            
            db.create_customer(name, email, phone, company)
            success_count += 1
        
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    return success_count, errors

def batch_create_products_from_csv(csv_content: str) -> Tuple[int, List[str]]:
    """
    Batch create products from CSV.
    Expected columns: name, price, category (optional), description (optional)
    Returns: (success_count, errors)
    """
    success_count = 0
    errors = []
    
    try:
        df = pd.read_csv(io.StringIO(csv_content))
    except Exception as e:
        return 0, [f"CSV parsing error: {str(e)}"]
    
    required_columns = ['name', 'price']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, [f"Missing columns: {', '.join(missing_cols)}"]
    
    for idx, row in df.iterrows():
        try:
            name = str(row['name']).strip()
            price = float(row['price'])
            category = str(row.get('category', 'General')) if 'category' in df.columns else "General"
            description = str(row.get('description', '')) if 'description' in df.columns else ""
            
            if not name or price < 0:
                errors.append(f"Row {idx + 2}: Invalid data")
                continue
            
            # Check if product exists
            existing = next((p for p in db.get_products() if p['name'].lower() == name.lower()), None)
            if existing:
                errors.append(f"Row {idx + 2}: Product '{name}' already exists")
                continue
            
            db.create_product(name, description, price, category)
            success_count += 1
        
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    return success_count, errors

def export_template_quotes_csv() -> str:
    """Export CSV template for batch quote creation"""
    template = "customer_name,product_name,quantity,notes\n"
    template += "Acme Corporation,Enterprise Software License (Per Year),1,Demo quote\n"
    template += "TechStart Inc,Cloud Storage (5TB/Month),2,\n"
    return template

def export_template_customers_csv() -> str:
    """Export CSV template for batch customer creation"""
    template = "name,email,phone,company\n"
    template += "New Customer Inc,contact@newcustomer.com,+1-555-9999,New Customer\n"
    return template

def export_template_products_csv() -> str:
    """Export CSV template for batch product creation"""
    template = "name,price,category,description\n"
    template += "New Software License,999.00,Software,Annual license for new product\n"
    return template