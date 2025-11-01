import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
from database import Database
from utils import (
    apply_dark_theme, render_header, format_currency, format_date,
    generate_pdf_quote, status_badge, get_theme_colors
)
from analytics import (
    calculate_clv, predict_churn_risk, forecast_revenue, 
    get_product_recommendations, get_sales_intelligence, 
    calculate_health_scores_batch
)
from export_utils import (
    export_quotes_to_excel, export_quotes_to_detailed_excel, 
    export_analytics_report_to_excel, export_customer_health_report,
    export_audit_log_to_csv
)
from batch_operations import (
    batch_import_quotes_from_csv, batch_create_customers_from_csv,
    batch_create_products_from_csv, batch_update_status, batch_delete_quotes,
    export_template_quotes_csv, export_template_customers_csv, export_template_products_csv
)
from alerts_manager import AlertManager, get_alert_color, get_alert_icon

apply_dark_theme()
db = Database()

# Color palette
COLOR_PALETTE = ["#00D9FF", "#3FB950", "#FF006E", "#58A6FF", "#FFB81C", "#8E44AD", "#F39C12", "#E74C3C"]

def initialize_session_state():
    if 'current_quote_id' not in st.session_state:
        st.session_state.current_quote_id = None
    if 'current_customer_id' not in st.session_state:
        st.session_state.current_customer_id = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'current_user_id' not in st.session_state:
        st.session_state.current_user_id = 1  # Default user
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'admin'
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'

initialize_session_state()

# ===========================
# SIDEBAR & NAVIGATION
# ===========================

st.sidebar.markdown("### Settings")

# Theme Toggle
col1, col2 = st.sidebar.columns(2)
with col1:
    st.write("**Theme:**")
with col2:
    theme = st.selectbox("Theme", ["Dark", "Light"], label_visibility="collapsed", key="theme_select")
    st.session_state.theme = theme.lower()

# User info
st.sidebar.markdown("---")
st.sidebar.markdown("### User")
st.sidebar.write(f"**Role:** {st.session_state.user_role.replace('_', ' ').title()}")

# Alerts summary
unread_alerts = db.get_unread_alerts(st.session_state.current_user_id)
if unread_alerts:
    st.sidebar.warning(f"**{len(unread_alerts)} Unread Alerts**")

st.sidebar.markdown("---")

# Main navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Create Quote",
        "Manage Quotes",
        "Quote Details",
        "Reports & Analytics",
        "Customer Health",
        "Batch Operations",
        "Advanced Search",
        "Export Center",
        "Alerts",
        "Admin Panel",
        "Settings"
    ]
)

# ===========================
# PAGE FUNCTIONS
# ===========================

def page_dashboard():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Dashboard</h2>", unsafe_allow_html=True)
    
    all_quotes = db.get_all_quotes()
    customers = db.get_customers()
    
    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #00D9FF;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Quotes</p>"
            f"<h2 style='color: #00D9FF; margin: 10px 0 0 0;'>{len(all_quotes)}</h2>"
            f"</div>", unsafe_allow_html=True
        )
    
    with col2:
        draft_count = len([q for q in all_quotes if q['status'] == 'draft'])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #8B949E;'>"
            f"<p style='color: #8B949E; margin: 0;'>Draft</p>"
            f"<h2 style='color: #8B949E; margin: 10px 0 0 0;'>{draft_count}</h2>"
            f"</div>", unsafe_allow_html=True
        )
    
    with col3:
        sent_count = len([q for q in all_quotes if q['status'] == 'sent'])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #3FB950;'>"
            f"<p style='color: #8B949E; margin: 0;'>Sent</p>"
            f"<h2 style='color: #3FB950; margin: 10px 0 0 0;'>{sent_count}</h2>"
            f"</div>", unsafe_allow_html=True
        )
    
    with col4:
        accepted_count = len([q for q in all_quotes if q['status'] == 'accepted'])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #00D9FF;'>"
            f"<p style='color: #8B949E; margin: 0;'>Accepted</p>"
            f"<h2 style='color: #00D9FF; margin: 10px 0 0 0;'>{accepted_count}</h2>"
            f"</div>", unsafe_allow_html=True
        )
    
    with col5:
        total_value = sum([q['total'] for q in all_quotes if q['status'] in ['sent', 'accepted']])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #FF006E;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Value</p>"
            f"<h2 style='color: #FF006E; margin: 10px 0 0 0;'>{format_currency(total_value)}</h2>"
            f"</div>", unsafe_allow_html=True
        )
    
    st.markdown("<hr style='border: 1px solid #30363D; margin: 30px 0;'>", unsafe_allow_html=True)
    
    # Sales Intelligence & Revenue Forecast - Combined Table
    st.markdown("<h3 style='color: #00D9FF;'>Sales Intelligence & Revenue Forecast</h3>", unsafe_allow_html=True)
    
    intelligence = get_sales_intelligence()
    forecast = forecast_revenue(30)
    
    # Create table data
    table_data = {
        "Metric": [
            "Total Revenue",
            "Win Rate",
            "Average Deal Size",
            "30-Day Revenue",
            "30-Day Forecast",
            "Daily Average",
            "Confidence Level",
            "Trend Direction"
        ],
        "Value": [
            format_currency(intelligence['total_value']),
            f"{intelligence['win_rate']:.1f}%",
            format_currency(intelligence['average_deal_size']),
            format_currency(intelligence['recent_30_day_value']),
            format_currency(forecast['forecast']),
            format_currency(forecast['daily_average']),
            forecast['confidence'],
            forecast['trend']
        ]
    }
    
    df_table = pd.DataFrame(table_data)
    
    # Style the dataframe
    def style_table(val):
        if isinstance(val, str) and val.startswith('$'):
            return 'color: #3FB950; font-weight: bold;'
        elif isinstance(val, str) and '%' in val:
            return 'color: #00D9FF; font-weight: bold;'
        elif isinstance(val, str) and val in ['High', 'Positive', 'Strong']:
            return 'color: #3FB950; font-weight: bold;'
        elif isinstance(val, str) and val in ['Low', 'Negative']:
            return 'color: #FF006E; font-weight: bold;'
        elif isinstance(val, str) and val == 'Medium':
            return 'color: #FFA500; font-weight: bold;'
        return 'color: #C9D1D9;'
    
    styled_df = df_table.style.map(style_table, subset=['Value'])
    styled_df = styled_df.set_properties(**{'text-align': 'left', 'background-color': '#0D1117'})
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    st.markdown("<hr style='border: 1px solid #30363D; margin: 30px 0;'>", unsafe_allow_html=True)
    
    # Recent Quotes
    st.markdown("<h3 style='color: #00D9FF;'>Recent Quotes</h3>", unsafe_allow_html=True)
    if all_quotes:
        quote_df = pd.DataFrame(all_quotes[:10])
        quote_df = quote_df[['quote_number', 'customer', 'status', 'total', 'created_at']]
        quote_df.columns = ['Quote #', 'Customer', 'Status', 'Amount', 'Created']
        quote_df['Created'] = quote_df['Created'].apply(format_date)
        quote_df['Amount'] = quote_df['Amount'].apply(format_currency)
        quote_df['Status'] = quote_df['Status'].apply(lambda x: x.upper())
        st.dataframe(quote_df, use_container_width=True, hide_index=True)

def page_create_quote():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Create New Quote</h2>", unsafe_allow_html=True)
    
    customers = db.get_customers()
    products = db.get_products()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        customer_names = [c['name'] for c in customers]
        customer_dict = {c['name']: c['id'] for c in customers}
        
        selected_customer = st.selectbox("Select Customer", options=customer_names, key="create_quote_customer")
        
        if selected_customer:
            customer_id = customer_dict[selected_customer]
            st.session_state.current_customer_id = customer_id
            
            st.markdown("---")
            
            product_names = [f"{p['name']} - {format_currency(p['price'])}" for p in products]
            product_dict = {f"{p['name']} - {format_currency(p['price'])}": p['id'] for p in products}
            
            selected_product = st.selectbox(
                "Add Product to Quote",
                options=["-- Select a product --"] + product_names,
                key=f"add_product_{customer_id}"
            )
            
            if selected_product and selected_product != "-- Select a product --":
                col_qty, col_btn = st.columns([3, 1])
                
                with col_qty:
                    quantity = st.number_input("Quantity", min_value=1, value=1, step=1, key=f"qty_{customer_id}")
                
                with col_btn:
                    st.write("")
                    if st.button("Add Item", key=f"add_item_btn_{customer_id}"):
                        quote_id = db.create_quote(customer_id, "")
                        st.session_state.current_quote_id = quote_id
                        
                        product_id = product_dict[selected_product]
                        product = [p for p in products if p['id'] == product_id][0]
                        unit_price = product['price']
                        
                        db.add_quote_item(quote_id, product_id, quantity, unit_price)
                        st.success(f"Quote created with {quantity} item(s)!")
                        st.rerun()
    
    with col2:
        st.markdown("### Quick Info")
        st.info(f"Total Customers: {len(customers)}\n\nTotal Products: {len(products)}")

def page_manage_quotes():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Manage Quotes</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["All Quotes", "Draft", "Sent", "Accepted/Rejected"])
    
    def display_quotes_table(quotes, tab_key):
        if not quotes:
            st.info("No quotes found.")
            return
        
        quote_df = pd.DataFrame(quotes)
        quote_df = quote_df[['quote_number', 'customer', 'status', 'total', 'created_at']]
        quote_df.columns = ['Quote #', 'Customer', 'Status', 'Amount', 'Created']
        quote_df['Created'] = quote_df['Created'].apply(format_date)
        quote_df['Amount'] = quote_df['Amount'].apply(format_currency)
        quote_df['Status'] = quote_df['Status'].apply(lambda x: x.upper())
        
        st.dataframe(quote_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### Quick View")
        
        for idx, quote in enumerate(quotes[:5]):
            full_quote = db.get_quote(quote['id'])
            customer = db.get_customer_by_id(full_quote['customer_id'])
            items = db.get_quote_items(quote['id'])
            
            with st.expander(f"{quote['quote_number']} - {quote['customer']} ({format_currency(quote['total'])})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Status:** {quote['status'].upper()}")
                    st.write(f"**Created:** {format_date(quote['created_at'])}")
                    st.write(f"**Amount:** {format_currency(quote['total'])}")
                
                with col2:
                    st.write(f"**Customer:** {customer['name']}")
                    st.write(f"**Email:** {customer['email']}")
                    st.write(f"**Phone:** {customer['phone']}")
                
                st.markdown("---")
                
                if items:
                    st.write("**Line Items:**")
                    items_df = pd.DataFrame(items)
                    items_df = items_df[['name', 'quantity', 'unit_price', 'line_total']]
                    items_df.columns = ['Product', 'Qty', 'Unit Price', 'Line Total']
                    items_df['Unit Price'] = items_df['Unit Price'].apply(format_currency)
                    items_df['Line Total'] = items_df['Line Total'].apply(format_currency)
                    st.dataframe(items_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Full Details", key=f"view_detail_{tab_key}_{idx}"):
                        st.session_state.current_quote_id = quote['id']
                        st.rerun()
                
                with col2:
                    pdf_buffer = generate_pdf_quote(full_quote, customer, items, {})
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name=f"Quote_{quote['quote_number']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{tab_key}_{idx}"
                    )
                
                with col3:
                    csv_data = pd.DataFrame(items).to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"Quote_{quote['quote_number']}_items.csv",
                        mime="text/csv",
                        key=f"csv_{tab_key}_{idx}"
                    )
    
    with tab1:
        quotes = db.get_all_quotes()
        display_quotes_table(quotes, "all")
    
    with tab2:
        draft_quotes = db.get_all_quotes("draft")
        display_quotes_table(draft_quotes, "draft")
    
    with tab3:
        sent_quotes = [q for q in db.get_all_quotes() if q['status'] == 'sent']
        display_quotes_table(sent_quotes, "sent")
    
    with tab4:
        final_quotes = [q for q in db.get_all_quotes() if q['status'] in ['accepted', 'rejected']]
        display_quotes_table(final_quotes, "final")

def page_quote_detail():
    render_header()
    
    if not st.session_state.current_quote_id:
        st.markdown("<h2 style='color: #00D9FF;'>Quote Details</h2>", unsafe_allow_html=True)
        all_quotes = db.get_all_quotes()
        
        if not all_quotes:
            st.info("No quotes available. Create a quote from 'Create Quote' page.")
            return
        
        quote_options = {f"{q['quote_number']} - {q['customer']}" : q['id'] for q in all_quotes}
        selected_quote_display = st.selectbox("Select a Quote", options=quote_options.keys())
        
        if st.button("Load Quote"):
            st.session_state.current_quote_id = quote_options[selected_quote_display]
            st.rerun()
        return
    
    quote_id = st.session_state.current_quote_id
    quote = db.get_quote(quote_id)
    customer = db.get_customer_by_id(quote['customer_id'])
    items = db.get_quote_items(quote_id)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"<h2 style='color: #00D9FF;'>Quote #{quote['quote_number']}</h2>", unsafe_allow_html=True)
    
    with col2:
        new_status = st.selectbox(
            "Status",
            options=["draft", "sent", "accepted", "rejected"],
            index=["draft", "sent", "accepted", "rejected"].index(quote['status']),
            key="status_select"
        )
        if new_status != quote['status']:
            db.update_quote_status(quote_id, new_status)
            AlertManager.create_quote_status_alert(quote_id, new_status)
            st.success(f"Status updated to {new_status}")
            st.rerun()
    
    with col3:
        if st.button("Delete Quote"):
            db.delete_quote(quote_id)
            st.success("Quote deleted!")
            st.session_state.current_quote_id = None
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Customer Info")
        st.write(f"**Name:** {customer['name']}")
        st.write(f"**Email:** {customer['email']}")
        st.write(f"**Phone:** {customer['phone']}")
        st.write(f"**Company:** {customer['company']}")
    
    with col2:
        st.markdown("### Quote Info")
        st.write(f"**Created:** {format_date(quote['created_at'])}")
        st.write(f"**Updated:** {format_date(quote['updated_at'])}")
    
    st.markdown("---")
    
    st.markdown("### Line Items")
    
    if items:
        for item in items:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 0.5])
            
            with col1:
                st.write(item['name'])
            
            with col2:
                st.write(f"Qty: {item['quantity']}")
            
            with col3:
                st.write(f"{format_currency(item['unit_price'])} -> {format_currency(item['line_total'])}")
            
            with col4:
                if st.button("Delete", key=f"delete_item_{item['id']}"):
                    db.delete_quote_item(item['id'], quote_id)
                    st.rerun()
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Subtotal:** {format_currency(quote['subtotal'])}")
        
        with col2:
            st.markdown(f"**Tax ({int(quote['tax_rate'] * 100)}%):** {format_currency(quote['tax_amount'])}")
        
        with col3:
            st.markdown(f"**Total:** {format_currency(quote['total'])}")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Send Quote"):
                db.update_quote_status(quote_id, 'sent')
                AlertManager.create_quote_status_alert(quote_id, 'sent')
                st.success("Quote marked as sent!")
                st.rerun()
        
        with col2:
            pdf_buffer = generate_pdf_quote(quote, customer, items, {})
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=f"Quote_{quote['quote_number']}.pdf",
                mime="application/pdf"
            )
        
        with col3:
            csv_data = pd.DataFrame(items).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"Quote_{quote['quote_number']}_items.csv",
                mime="text/csv"
            )

def page_reports_analytics():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Reports & Analytics</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Sales Intelligence", "Revenue Forecast", "Top Customers", "Product Analysis"])
    
    intelligence = get_sales_intelligence()
    all_quotes = db.get_all_quotes()
    
    with tab1:
        st.markdown("### Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Revenue", format_currency(intelligence['total_value']), border=True)
        with col2:
            st.metric("Total Quotes", intelligence['total_quotes'], border=True)
        with col3:
            st.metric("Win Rate", f"{intelligence['win_rate']:.1f}%", border=True)
        with col4:
            st.metric("Avg Deal Size", format_currency(intelligence['average_deal_size']), border=True)
        
        st.markdown("---")
        
        # Revenue trend chart
        st.markdown("### Revenue Trend - Last 30 Days")
        
        # Prepare data for last 30 days
        revenue_by_date = {}
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
        
        for quote in all_quotes:
            if quote['status'] in ['accepted', 'sent']:
                try:
                    quote_date = datetime.fromisoformat(quote['created_at']).date()
                    if quote_date >= thirty_days_ago:
                        date_str = quote_date.strftime('%Y-%m-%d')
                        revenue_by_date[date_str] = revenue_by_date.get(date_str, 0) + quote['total']
                except:
                    pass
        
        if revenue_by_date:
            chart_data = pd.DataFrame({
                'Date': sorted(revenue_by_date.keys()),
                'Revenue': [revenue_by_date[d] for d in sorted(revenue_by_date.keys())]
            })
            
            chart = alt.Chart(chart_data).mark_line(point=True, color='#00D9FF', size=3).encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Revenue:Q', title='Revenue ($)'),
                tooltip=['Date:T', alt.Tooltip('Revenue:Q', format='$,.0f')]
            ).interactive().properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No revenue data available for the last 30 days")
        
        # Quote status breakdown
        st.markdown("### Quote Status Breakdown")
        status_count = {}
        for quote in all_quotes:
            status = quote['status'].upper()
            status_count[status] = status_count.get(status, 0) + 1
        
        if status_count:
            status_data = pd.DataFrame({
                'Status': list(status_count.keys()),
                'Count': list(status_count.values())
            })
            
            pie_chart = alt.Chart(status_data).mark_arc().encode(
                theta='Count:Q',
                color=alt.Color('Status:N', scale=alt.Scale(domain=list(status_count.keys()), range=COLOR_PALETTE)),
                tooltip=['Status:N', 'Count:Q']
            ).properties(height=400)
            
            st.altair_chart(pie_chart, use_container_width=True)
    
    with tab2:
        st.markdown("### 90-Day Revenue Forecast")
        forecast = forecast_revenue(90)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Forecast", format_currency(forecast['forecast']), border=True)
        with col2:
            st.metric("Daily Avg", format_currency(forecast['daily_average']), border=True)
        with col3:
            conf_text = "High" if forecast['confidence'] == 'High' else "Medium" if forecast['confidence'] == 'Medium' else "Low"
            st.metric("Confidence", conf_text, border=True)
        with col4:
            trend_text = "Positive" if forecast['trend'] == 'Positive' else "Negative"
            st.metric("Trend", trend_text, border=True)
        
        st.markdown("---")
        
        # Forecast visualization
        if forecast['forecast'] > 0:
            st.markdown("### Forecast Projection Chart")
            
            # Create forecast data
            historical_revenue = {}
            for quote in all_quotes:
                if quote['status'] in ['accepted', 'sent']:
                    try:
                        quote_date = datetime.fromisoformat(quote['created_at']).date()
                        date_str = quote_date.strftime('%Y-%m-%d')
                        historical_revenue[date_str] = historical_revenue.get(date_str, 0) + quote['total']
                    except:
                        pass
            
            if historical_revenue:
                dates = sorted(historical_revenue.keys())
                daily_avg = sum(historical_revenue.values()) / len(historical_revenue) if historical_revenue else 0
                
                # Create projection
                last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
                projection_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 91)]
                projection_revenues = [daily_avg] * 90
                
                combined_data = []
                for date, revenue in historical_revenue.items():
                    combined_data.append({'Date': date, 'Revenue': revenue, 'Type': 'Historical'})
                
                for date, revenue in zip(projection_dates, projection_revenues):
                    combined_data.append({'Date': date, 'Revenue': revenue, 'Type': 'Forecast'})
                
                forecast_df = pd.DataFrame(combined_data)
                
                forecast_chart = alt.Chart(forecast_df).mark_line().encode(
                    x='Date:T',
                    y=alt.Y('Revenue:Q', title='Revenue ($)'),
                    color=alt.Color('Type:N', scale=alt.Scale(domain=['Historical', 'Forecast'], range=['#00D9FF', '#FF006E'])),
                    strokeDash=alt.StrokeDash('Type:N', scale=alt.Scale(domain=['Historical', 'Forecast'], range=[[], [5, 5]])),
                    tooltip=['Date:T', alt.Tooltip('Revenue:Q', format='$,.0f'), 'Type:N']
                ).interactive().properties(height=400)
                
                st.altair_chart(forecast_chart, use_container_width=True)
        else:
            st.warning("Insufficient data for forecast. Need at least 5 quotes with sales data.")
    
    with tab3:
        st.markdown("### Top Customers by Revenue & CLV")
        
        if intelligence['top_customers']:
            df_data = []
            for customer_id, total in intelligence['top_customers'][:10]:
                customer = db.get_customer_by_id(customer_id)
                if customer:
                    clv = calculate_clv(customer_id)
                    df_data.append({
                        'Customer': customer['name'],
                        'Revenue': total,
                        'CLV': clv
                    })
            
            if df_data:
                df = pd.DataFrame(df_data)
                
                # Bar chart - Revenue
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Revenue by Customer")
                    revenue_chart = alt.Chart(df).mark_bar(color='#3FB950').encode(
                        y=alt.Y('Customer:N', sort='-x'),
                        x=alt.X('Revenue:Q', title='Revenue ($)'),
                        tooltip=['Customer:N', alt.Tooltip('Revenue:Q', format='$,.0f')]
                    ).interactive().properties(height=400)
                    st.altair_chart(revenue_chart, use_container_width=True)
                
                with col2:
                    st.markdown("#### Customer Lifetime Value")
                    clv_chart = alt.Chart(df).mark_bar(color='#FF006E').encode(
                        y=alt.Y('Customer:N', sort='-x'),
                        x=alt.X('CLV:Q', title='CLV ($)'),
                        tooltip=['Customer:N', alt.Tooltip('CLV:Q', format='$,.0f')]
                    ).interactive().properties(height=400)
                    st.altair_chart(clv_chart, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Detailed Customer Data")
                df_display = df.copy()
                df_display['Revenue'] = df_display['Revenue'].apply(format_currency)
                df_display['CLV'] = df_display['CLV'].apply(format_currency)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No customer data available")
    
    with tab4:
        st.markdown("### Product Performance Analysis")
        
        product_revenue = {}
        product_count = {}
        
        for quote in all_quotes:
            if quote['status'] in ['accepted', 'sent']:
                items = db.get_quote_items(quote['id'])
                for item in items:
                    product_id = item['product_id']
                    product_revenue[product_id] = product_revenue.get(product_id, 0) + item['line_total']
                    product_count[product_id] = product_count.get(product_id, 0) + 1
        
        if product_revenue:
            df_data = []
            for product_id, revenue in sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:10]:
                product = db.get_product_by_id(product_id)
                if product:
                    df_data.append({
                        'Product': product['name'],
                        'Revenue': revenue,
                        'Count': product_count.get(product_id, 0),
                        'Avg Price': revenue / product_count.get(product_id, 1)
                    })
            
            if df_data:
                df = pd.DataFrame(df_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Revenue by Product")
                    rev_chart = alt.Chart(df).mark_bar(color='#58A6FF').encode(
                        y=alt.Y('Product:N', sort='-x'),
                        x=alt.X('Revenue:Q', title='Revenue ($)'),
                        tooltip=['Product:N', alt.Tooltip('Revenue:Q', format='$,.0f'), 'Count:Q']
                    ).interactive().properties(height=400)
                    st.altair_chart(rev_chart, use_container_width=True)
                
                with col2:
                    st.markdown("#### Sales Count by Product")
                    count_chart = alt.Chart(df).mark_bar(color='#FFB81C').encode(
                        y=alt.Y('Product:N', sort='-x'),
                        x=alt.X('Count:Q', title='Number of Sales'),
                        tooltip=['Product:N', 'Count:Q', alt.Tooltip('Avg Price:Q', format='$,.2f')]
                    ).interactive().properties(height=400)
                    st.altair_chart(count_chart, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Detailed Product Data")
                df_display = df.copy()
                df_display['Revenue'] = df_display['Revenue'].apply(format_currency)
                df_display['Avg Price'] = df_display['Avg Price'].apply(format_currency)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No product data available")

def page_customer_health():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Customer Health Scores</h2>", unsafe_allow_html=True)
    
    # Calculate health scores
    calculate_health_scores_batch()
    
    health_scores = db.get_all_customer_health_scores()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    high_risk = len([s for s in health_scores if s['risk_level'] == 'HIGH'])
    medium_risk = len([s for s in health_scores if s['risk_level'] == 'MEDIUM'])
    low_risk = len([s for s in health_scores if s['risk_level'] == 'LOW'])
    
    with col1:
        st.metric("High Risk", high_risk)
    with col2:
        st.metric("Medium Risk", medium_risk)
    with col3:
        st.metric("Low Risk", low_risk)
    with col4:
        avg_score = sum([s['health_score'] for s in health_scores]) / len(health_scores) if health_scores else 0
        st.metric("Average Score", f"{avg_score:.1f}/100")
    
    st.markdown("---")
    
    # Health scores table
    tab1, tab2, tab3 = st.tabs(["All Customers", "At Risk", "Churn Analysis"])
    
    with tab1:
        if health_scores:
            df = pd.DataFrame([
                {
                    'Customer': s['name'],
                    'Engagement': f"{s['engagement_score']:.1f}",
                    'Spend Score': f"{s['spend_score']:.1f}",
                    'Growth': f"{s['growth_score']:.1f}",
                    'Health Score': f"{s['health_score']:.1f}",
                    'Risk Level': s['risk_level']
                }
                for s in health_scores
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        at_risk = [s for s in health_scores if s['risk_level'] in ['HIGH', 'MEDIUM']]
        if at_risk:
            st.warning(f"{len(at_risk)} customers at risk of churn")
            for customer in at_risk[:5]:
                with st.expander(f"{customer['name']} - Risk: {customer['risk_level']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Health Score", f"{customer['health_score']:.1f}/100")
                        st.metric("Engagement", f"{customer['engagement_score']:.1f}")
                    with col2:
                        st.metric("Spend Score", f"{customer['spend_score']:.1f}")
                        st.metric("Growth", f"{customer['growth_score']:.1f}")
                    
                    # Churn risk
                    customer_obj = db.get_customer_by_id(customer['customer_id'])
                    if customer_obj:
                        churn = predict_churn_risk(customer['customer_id'])
                        st.error(f"Churn Risk: {churn['risk']}% - {churn['reason']}")
                        
                        # Recommendations
                        st.markdown("**Recommended Actions:**")
                        st.info("Schedule customer check-in call\n\nSend personalized outreach\n\nOffer loyalty incentive")
    
    with tab3:
        st.markdown("### Customer Churn Analysis")
        churn_data = []
        for score in health_scores:
            churn = predict_churn_risk(score['customer_id'])
            churn_data.append({
                'Customer': score['name'],
                'Churn Risk %': churn['risk'],
                'Reason': churn['reason'],
                'Health Score': score['health_score']
            })
        
        df = pd.DataFrame(churn_data)
        df = df.sort_values('Churn Risk %', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

def page_batch_operations():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Batch Operations</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Import Quotes", "Import Customers", "Import Products", "Batch Actions"])
    
    with tab1:
        st.markdown("### Import Quotes from CSV")
        st.write("CSV should have columns: customer_name, product_name, quantity, notes")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download Template"):
                template = export_template_quotes_csv()
                st.download_button("Download CSV Template", template, "quotes_template.csv", "text/csv")
        
        with col2:
            csv_file = st.file_uploader("Upload CSV file", type="csv", key="quotes_csv")
            if csv_file:
                csv_content = csv_file.read().decode('utf-8')
                success, errors = batch_import_quotes_from_csv(csv_content)
                st.success(f"{success} quotes imported successfully!")
                if errors:
                    with st.expander("View errors"):
                        for error in errors:
                            st.error(error)
    
    with tab2:
        st.markdown("### Import Customers from CSV")
        st.write("CSV should have columns: name, email, phone (optional), company (optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download Template", key="template_customers"):
                template = export_template_customers_csv()
                st.download_button("Download CSV Template", template, "customers_template.csv", "text/csv", key="download_customers")
        
        with col2:
            csv_file = st.file_uploader("Upload CSV file", type="csv", key="customers_csv")
            if csv_file:
                csv_content = csv_file.read().decode('utf-8')
                success, errors = batch_create_customers_from_csv(csv_content)
                st.success(f"{success} customers imported successfully!")
                if errors:
                    with st.expander("View errors"):
                        for error in errors:
                            st.error(error)
    
    with tab3:
        st.markdown("### Import Products from CSV")
        st.write("CSV should have columns: name, price, category (optional), description (optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download Template", key="template_products"):
                template = export_template_products_csv()
                st.download_button("Download CSV Template", template, "products_template.csv", "text/csv", key="download_products")
        
        with col2:
            csv_file = st.file_uploader("Upload CSV file", type="csv", key="products_csv")
            if csv_file:
                csv_content = csv_file.read().decode('utf-8')
                success, errors = batch_create_products_from_csv(csv_content)
                st.success(f"{success} products imported successfully!")
                if errors:
                    with st.expander("View errors"):
                        for error in errors:
                            st.error(error)
    
    with tab4:
        st.markdown("### Batch Actions on Quotes")
        all_quotes = db.get_all_quotes()
        
        if all_quotes:
            quote_options = {f"{q['quote_number']} - {q['customer']}" : q['id'] for q in all_quotes}
            selected_quotes = st.multiselect("Select quotes", options=quote_options.keys())
            
            if selected_quotes:
                quote_ids = [quote_options[q] for q in selected_quotes]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Mark as Sent"):
                        success, failed = batch_update_status(quote_ids, 'sent')
                        st.success(f"{success} quotes updated")
                        if failed:
                            st.warning(f"{failed} quotes failed")
                
                with col2:
                    if st.button("Mark as Accepted"):
                        success, failed = batch_update_status(quote_ids, 'accepted')
                        st.success(f"{success} quotes updated")
                        if failed:
                            st.warning(f"{failed} quotes failed")
                
                with col3:
                    if st.button("Delete Quotes"):
                        success, failed = batch_delete_quotes(quote_ids)
                        st.success(f"{success} quotes deleted")
                        if failed:
                            st.warning(f"{failed} quotes failed")

def page_advanced_search():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Advanced Search & Filter</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Text Search", "Advanced Filter"])
    
    with tab1:
        search_term = st.text_input("Search quotes by number, customer name, or email:")
        if search_term:
            results = db.search_quotes(search_term)
            if results:
                st.success(f"Found {len(results)} quotes")
                df = pd.DataFrame([
                    {
                        'Quote #': r['quote_number'],
                        'Customer': r['customer'],
                        'Status': r['status'].upper(),
                        'Amount': format_currency(r['total']),
                        'Created': format_date(r['created_at'])
                    }
                    for r in results
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No quotes found")
    
    with tab2:
        st.markdown("### Filter Quotes")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = st.selectbox("Status", options=["All", "draft", "sent", "accepted", "rejected"])
        with col2:
            days_back = st.number_input("Days back", min_value=0, value=90)
        with col3:
            min_amount = st.number_input("Min amount", min_value=0.0, value=0.0, step=100.0)
        with col4:
            max_amount = st.number_input("Max amount", min_value=0.0, value=1000000.0, step=1000.0)
        
        if st.button("Apply Filter"):
            results = db.filter_quotes(
                status=None if status == "All" else status,
                min_amount=min_amount if min_amount > 0 else None,
                max_amount=max_amount,
                days_back=days_back if days_back > 0 else None
            )
            
            if results:
                st.success(f"Found {len(results)} quotes")
                df = pd.DataFrame([
                    {
                        'Quote #': r['quote_number'],
                        'Customer': r['customer'],
                        'Status': r['status'].upper(),
                        'Amount': format_currency(r['total']),
                        'Created': format_date(r['created_at'])
                    }
                    for r in results
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No quotes match your filters")

def page_export_center():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Export Center</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Quotes (Excel)", "Detailed Export", "Analytics Report", "Health Scores", "Audit Log"])
    
    all_quotes = db.get_all_quotes()
    quote_ids = [q['id'] for q in all_quotes]
    
    with tab1:
        st.markdown("### Export All Quotes to Excel")
        if st.button("Generate Excel"):
            buffer = export_quotes_to_excel(quote_ids)
            st.download_button(
                label="Download Quotes.xlsx",
                data=buffer,
                file_name=f"Quotes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab2:
        st.markdown("### Detailed Quote Export (with line items)")
        if all_quotes:
            selected_quote_nums = st.multiselect(
                "Select quotes to export",
                options=[q['quote_number'] for q in all_quotes]
            )
            
            if st.button("Generate Detailed Export"):
                selected_ids = [q['id'] for q in all_quotes if q['quote_number'] in selected_quote_nums]
                buffer = export_quotes_to_detailed_excel(selected_ids)
                st.download_button(
                    label="Download Detailed_Quotes.xlsx",
                    data=buffer,
                    file_name=f"Detailed_Quotes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with tab3:
        st.markdown("### Export Analytics Report")
        if st.button("Generate Analytics Report"):
            intelligence = get_sales_intelligence()
            buffer = export_analytics_report_to_excel(intelligence)
            st.download_button(
                label="Download Analytics_Report.xlsx",
                data=buffer,
                file_name=f"Analytics_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab4:
        st.markdown("### Export Customer Health Scores")
        if st.button("Generate Health Report"):
            buffer = export_customer_health_report()
            st.download_button(
                label="Download Customer_Health.xlsx",
                data=buffer,
                file_name=f"Customer_Health_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab5:
        st.markdown("### Export Audit Log")
        if st.button("Generate Audit Log"):
            buffer = export_audit_log_to_csv()
            st.download_button(
                label="Download Audit_Log.csv",
                data=buffer,
                file_name=f"Audit_Log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

def page_alerts():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Alerts & Notifications</h2>", unsafe_allow_html=True)
    
    # Run alert checks
    if st.button("Refresh Alerts"):
        AlertManager.run_all_checks()
        st.rerun()
    
    unread_alerts = db.get_unread_alerts(st.session_state.current_user_id)
    
    if unread_alerts:
        st.markdown(f"### Unread Alerts ({len(unread_alerts)})")
        
        for alert in unread_alerts:
            color = get_alert_color(alert['severity'])
            icon = get_alert_icon(alert['alert_type'])
            
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.markdown(icon, unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f"<div style='background-color: #161B22; padding: 15px; border-radius: 8px; border-left: 4px solid {color};'>"
                    f"<p style='color: {color}; font-weight: bold; margin: 0;'>{alert['title']}</p>"
                    f"<p style='color: #8B949E; margin: 5px 0 0 0;'>{alert['message']}</p>"
                    f"<p style='color: #8B949E; font-size: 0.8em; margin: 5px 0 0 0;'>{format_date(alert['created_at'])}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                if st.button("Mark as read", key=f"alert_{alert['id']}"):
                    db.mark_alert_as_read(alert['id'])
                    st.rerun()
    else:
        st.success("No unread alerts!")
    
    # Manual alert creation (for testing)
    st.markdown("---")
    st.markdown("### Create Test Alert")
    
    col1, col2 = st.columns(2)
    with col1:
        alert_type = st.selectbox("Alert Type", ["high_value_quote", "revenue_drop", "churn_risk", "system"])
    with col2:
        severity = st.selectbox("Severity", ["info", "success", "warning", "danger"])
    
    message = st.text_area("Message")
    
    if st.button("Create Alert"):
        db.create_alert(st.session_state.current_user_id, alert_type, alert_type.replace('_', ' ').title(), message, severity)
        st.success("Alert created!")
        st.rerun()

def page_admin_panel():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Admin Panel</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Users", "Audit Log", "System Settings"])
    
    with tab1:
        st.markdown("### User Management")
        users = db.get_all_users()
        
        if users:
            df = pd.DataFrame([
                {
                    'Username': u['username'],
                    'Email': u['email'],
                    'Role': u['role'].replace('_', ' ').title()
                }
                for u in users
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.markdown("### Audit Log")
        logs = db.get_audit_logs(limit=100)
        
        if logs:
            df = pd.DataFrame([
                {
                    'User': l['user'] or 'System',
                    'Action': l['action'],
                    'Entity': f"{l['entity_type']} #{l['entity_id']}" if l['entity_type'] else '-',
                    'Details': l['details'] or '-',
                    'Created': format_date(l['created_at'])
                }
                for l in logs
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab3:
        st.markdown("### System Settings")
        st.info("System is running normally")

def page_settings():
    render_header()
    st.markdown("<h2 style='color: #00D9FF;'>Settings</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Preferences", "About"])
    
    with tab1:
        st.markdown("### User Preferences")
        
        # Theme preference
        theme_pref = st.selectbox("Preferred Theme", ["Dark", "Light"])
        
        # Notifications
        alerts_enabled = st.checkbox("Enable Alerts", value=True)
        email_notif = st.checkbox("Email Notifications", value=True)
        
        if st.button("Save Preferences"):
            db.update_user_preferences(
                st.session_state.current_user_id,
                theme=theme_pref.lower(),
                alerts_enabled=alerts_enabled,
                email_notifications=email_notif
            )
            st.success("Preferences saved!")
    
    with tab2:
        st.markdown("### About Quote Builder Pro")
        st.info(
            "**Quote Builder Pro v2.0**\n\n"
            "Enterprise-grade quote management system with advanced analytics, "
            "AI-powered insights, and batch operations.\n\n"
            "**Features:**\n"
            "Advanced Customer Health Scoring\n"
            "AI Revenue Forecasting\n"
            "Batch Import/Export\n"
            "Real-time Alerts\n"
            "Multi-user Collaboration\n"
            "Enterprise Analytics\n\n"
            "Built with Streamlit + SQLite"
        )

# ===========================
# MAIN ROUTING
# ===========================

if page == "Dashboard":
    page_dashboard()
elif page == "Create Quote":
    page_create_quote()
elif page == "Manage Quotes":
    page_manage_quotes()
elif page == "Quote Details":
    page_quote_detail()
elif page == "Reports & Analytics":
    page_reports_analytics()
elif page == "Customer Health":
    page_customer_health()
elif page == "Batch Operations":
    page_batch_operations()
elif page == "Advanced Search":
    page_advanced_search()
elif page == "Export Center":
    page_export_center()
elif page == "Alerts":
    page_alerts()
elif page == "Admin Panel":
    if st.session_state.user_role in ['admin']:
        page_admin_panel()
    else:
        st.error("Admin access required")
elif page == "Settings":
    page_settings()