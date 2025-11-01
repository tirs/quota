import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
from database import Database
from utils import (
    apply_dark_theme, render_header, format_currency, format_date,
    generate_pdf_quote, status_badge
)

apply_dark_theme()
db = Database()

def initialize_session_state():
    if 'current_quote_id' not in st.session_state:
        st.session_state.current_quote_id = None
    if 'current_customer_id' not in st.session_state:
        st.session_state.current_customer_id = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""

initialize_session_state()

def page_dashboard():
    render_header()

    col1, col2, col3, col4 = st.columns(4)

    all_quotes = db.get_all_quotes()

    with col1:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #00D9FF;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Quotes</p>"
            f"<h2 style='color: #00D9FF; margin: 10px 0 0 0;'>{len(all_quotes)}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col2:
        draft_count = len([q for q in all_quotes if q['status'] == 'draft'])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #8B949E;'>"
            f"<p style='color: #8B949E; margin: 0;'>Draft Quotes</p>"
            f"<h2 style='color: #8B949E; margin: 10px 0 0 0;'>{draft_count}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col3:
        accepted_count = len([q for q in all_quotes if q['status'] == 'accepted'])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #3FB950;'>"
            f"<p style='color: #8B949E; margin: 0;'>Accepted Quotes</p>"
            f"<h2 style='color: #3FB950; margin: 10px 0 0 0;'>{accepted_count}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col4:
        total_value = sum([q['total'] for q in all_quotes if q['status'] in ['sent', 'accepted']])
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #FF006E;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Value</p>"
            f"<h2 style='color: #FF006E; margin: 10px 0 0 0;'>{format_currency(total_value)}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border: 1px solid #30363D; margin: 30px 0;'>", unsafe_allow_html=True)

    st.markdown("<h2 style='color: #00D9FF;'>Recent Quotes</h2>", unsafe_allow_html=True)

    if all_quotes:
        quote_df = pd.DataFrame(all_quotes)
        quote_df = quote_df[['quote_number', 'customer', 'status', 'total', 'created_at']]
        quote_df.columns = ['Quote #', 'Customer', 'Status', 'Amount', 'Created']
        quote_df['Created'] = quote_df['Created'].apply(format_date)
        quote_df['Amount'] = quote_df['Amount'].apply(format_currency)
        
        status_map = {
            'draft': 'Draft',
            'sent': 'Sent',
            'accepted': 'Accepted',
            'rejected': 'Rejected'
        }
        quote_df['Status'] = quote_df['Status'].apply(lambda x: status_map.get(x, x))

        st.dataframe(quote_df, use_container_width=True, hide_index=True)
    else:
        st.info("No quotes created yet. Start by creating a new quote!")

def page_create_quote():
    render_header()

    st.markdown("<h2 style='color: #00D9FF;'>Create New Quote</h2>", unsafe_allow_html=True)

    customers = db.get_customers()
    products = db.get_products()

    col1, col2 = st.columns([2, 1])

    with col1:
        customer_names = [c['name'] for c in customers]
        customer_dict = {c['name']: c['id'] for c in customers}

        selected_customer = st.selectbox(
            "Select Customer",
            options=customer_names,
            key="create_quote_customer"
        )

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
                    st.write("")  # Spacer for alignment
                    if st.button("Add Item", key=f"add_item_btn_{customer_id}"):
                        quote_id = db.create_quote(customer_id, "")
                        st.session_state.current_quote_id = quote_id

                        product_id = product_dict[selected_product]
                        product = [p for p in products if p['id'] == product_id][0]
                        unit_price = product['price']

                        db.add_quote_item(quote_id, product_id, quantity, unit_price)
                        st.success(f"Quote created with {quantity} item(s)!")
                        st.session_state.message = f"Quote created with {quantity} item(s)!"
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
        
        status_map = {
            'draft': 'Draft',
            'sent': 'Sent',
            'accepted': 'Accepted',
            'rejected': 'Rejected'
        }
        quote_df['Status'] = quote_df['Status'].apply(lambda x: status_map.get(x, x))
        
        st.dataframe(quote_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### Quick View")
        
        for idx, quote in enumerate(quotes):
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
    
    # If no quote is selected, show a quote selector
    if not st.session_state.current_quote_id:
        st.markdown("<h2 style='color: #00D9FF;'>Quote Details</h2>", unsafe_allow_html=True)
        all_quotes = db.get_all_quotes()
        
        if not all_quotes:
            st.info("No quotes available. Create a quote from 'Create Quote' page.")
            return
        
        quote_options = {f"{q['quote_number']} - {q['customer']} ({q['status'].upper()})" : q['id'] for q in all_quotes}
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
            tax_rate = st.slider("Tax Rate (%)", min_value=0, max_value=50, value=int(quote['tax_rate'] * 100), step=1)
            new_tax_rate = tax_rate / 100
            if new_tax_rate != quote['tax_rate']:
                db.update_quote_tax(quote_id, new_tax_rate)
                st.rerun()

        with col3:
            st.markdown(f"**Total:** {format_currency(quote['total'])}")

        st.markdown("---")

        st.markdown("### Notes")
        new_notes = st.text_area("Add notes to this quote", value=quote.get('notes', ''), height=100)
        if st.button("Save Notes"):
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE quotes SET notes = ? WHERE id = ?", (new_notes, quote_id))
            conn.commit()
            conn.close()
            st.success("Notes saved!")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            pdf_buffer = generate_pdf_quote(quote, customer, items, {})
            st.download_button(
                label="Download as PDF",
                data=pdf_buffer,
                file_name=f"Quote_{quote['quote_number']}.pdf",
                mime="application/pdf"
            )

        with col2:
            csv_data = pd.DataFrame(items).to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv_data,
                file_name=f"Quote_{quote['quote_number']}_items.csv",
                mime="text/csv"
            )

    else:
        st.info("No line items in this quote yet.")

def page_customers():
    render_header()

    st.markdown("<h2 style='color: #00D9FF;'>Customer Management</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["All Customers", "Add New Customer"])

    with tab1:
        customers = db.get_customers()

        if customers:
            customer_df = pd.DataFrame(customers)
            st.dataframe(customer_df, use_container_width=True)
        else:
            st.info("No customers found.")

    with tab2:
        st.markdown("### Add New Customer")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Customer Name", key="new_customer_name")
            email = st.text_input("Email", key="new_customer_email")

        with col2:
            phone = st.text_input("Phone", key="new_customer_phone")
            company = st.text_input("Company", key="new_customer_company")

        if st.button("Add Customer"):
            if name and email:
                if db.add_customer(name, email, phone, company):
                    st.success(f"Customer {name} added successfully!")
                    st.rerun()
                else:
                    st.error("Customer with this name already exists.")
            else:
                st.error("Please fill in Name and Email fields.")

def page_products():
    render_header()

    st.markdown("<h2 style='color: #00D9FF;'>Product Catalog</h2>", unsafe_allow_html=True)

    products = db.get_products()

    if products:
        df = pd.DataFrame(products)
        df['price'] = df['price'].apply(format_currency)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No products found.")

    st.markdown("---")
    st.info("Products are managed at the database level. Contact admin to add/modify products.")

def page_reports():
    render_header()

    st.markdown("<h2 style='color: #00D9FF;'>Reports & Analytics</h2>", unsafe_allow_html=True)

    quotes = db.get_all_quotes()

    if not quotes:
        st.info("No quotes to generate reports from.")
        return

    # Date filtering
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")
    
    # Filter quotes by date
    filtered_quotes = quotes
    if start_date and end_date:
        filtered_quotes = [q for q in quotes if start_date <= datetime.strptime(q['created_at'], "%Y-%m-%d %H:%M:%S").date() <= end_date]

    st.markdown("---")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    total_quotes = len(filtered_quotes)
    total_revenue = sum([q['total'] for q in filtered_quotes])
    avg_value = total_revenue / total_quotes if total_quotes > 0 else 0
    acceptance_rate = (len([q for q in filtered_quotes if q['status'] == 'accepted']) / total_quotes * 100) if total_quotes > 0 else 0

    with col1:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #00D9FF;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Quotes</p>"
            f"<h2 style='color: #00D9FF; margin: 10px 0 0 0;'>{total_quotes}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #3FB950;'>"
            f"<p style='color: #8B949E; margin: 0;'>Total Revenue</p>"
            f"<h2 style='color: #3FB950; margin: 10px 0 0 0;'>{format_currency(total_revenue)}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #FF006E;'>"
            f"<p style='color: #8B949E; margin: 0;'>Average Value</p>"
            f"<h2 style='color: #FF006E; margin: 10px 0 0 0;'>{format_currency(avg_value)}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"<div style='background-color: #161B22; padding: 20px; border-radius: 8px; border-left: 4px solid #58A6FF;'>"
            f"<p style='color: #8B949E; margin: 0;'>Acceptance Rate</p>"
            f"<h2 style='color: #58A6FF; margin: 10px 0 0 0;'>{acceptance_rate:.1f}%</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Tabs for different analytics
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Status Overview", "Revenue Trends", "Top Customers", "Product Analysis", "Detailed View"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # Status Distribution
        status_counts = {}
        status_revenue = {}
        for quote in filtered_quotes:
            status = quote['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            status_revenue[status] = status_revenue.get(status, 0) + quote['total']

        with col1:
            st.markdown("### Quote Status Distribution")
            status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
            colors = ["#00D9FF", "#3FB950", "#FF006E", "#58A6FF", "#FFB81C"]
            color_map = {status: colors[i % len(colors)] for i, status in enumerate(status_df['Status'])}
            chart1 = alt.Chart(status_df).mark_bar().encode(
                x='Status:N',
                y='Count:Q',
                color=alt.Color('Status:N', scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())))
            ).interactive()
            st.altair_chart(chart1, use_container_width=True)
        
        with col2:
            st.markdown("### Revenue by Status")
            revenue_df = pd.DataFrame(list(status_revenue.items()), columns=['Status', 'Revenue'])
            colors = ["#FF006E", "#00D9FF", "#3FB950", "#58A6FF", "#FFB81C"]
            color_map = {status: colors[i % len(colors)] for i, status in enumerate(revenue_df['Status'])}
            chart2 = alt.Chart(revenue_df).mark_bar().encode(
                x='Status:N',
                y='Revenue:Q',
                color=alt.Color('Status:N', scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())))
            ).interactive()
            st.altair_chart(chart2, use_container_width=True)

    with tab2:
        st.markdown("### Revenue Timeline")
        # Group by date
        timeline_data = {}
        for quote in filtered_quotes:
            date = quote['created_at'].split()[0]
            timeline_data[date] = timeline_data.get(date, 0) + quote['total']
        
        timeline_df = pd.DataFrame(list(timeline_data.items()), columns=['Date', 'Revenue']).sort_values('Date')
        chart_timeline = alt.Chart(timeline_df).mark_line(color="#00D9FF", size=3).encode(
            x='Date:T',
            y='Revenue:Q'
        ).interactive()
        st.altair_chart(chart_timeline, use_container_width=True)
        
        st.markdown("### Daily Revenue Data")
        st.dataframe(timeline_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Top Customers by Revenue")
        customer_revenue = {}
        for quote in filtered_quotes:
            customer = quote['customer']
            customer_revenue[customer] = customer_revenue.get(customer, 0) + quote['total']
        
        top_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:10]
        top_cust_df = pd.DataFrame(top_customers, columns=['Customer', 'Total Revenue'])
        top_cust_df['Total Revenue'] = top_cust_df['Total Revenue'].apply(format_currency)
        
        st.dataframe(top_cust_df, use_container_width=True, hide_index=True)
        
        if top_customers:
            st.markdown("### Top Customers Chart")
            chart_df = pd.DataFrame(sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:5], columns=['Customer', 'Revenue'])
            colors = ["#FF006E", "#3FB950", "#58A6FF", "#FFB81C", "#00D9FF"]
            color_map = {customer: colors[i % len(colors)] for i, customer in enumerate(chart_df['Customer'])}
            chart_customers = alt.Chart(chart_df).mark_bar().encode(
                x='Customer:N',
                y='Revenue:Q',
                color=alt.Color('Customer:N', scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())))
            ).interactive()
            st.altair_chart(chart_customers, use_container_width=True)

    with tab4:
        st.markdown("### Product Performance")
        # Get all items from filtered quotes
        product_stats = {}
        for quote in filtered_quotes:
            items = db.get_quote_items(quote['id'])
            for item in items:
                product = item['name']
                if product not in product_stats:
                    product_stats[product] = {'qty': 0, 'revenue': 0}
                product_stats[product]['qty'] += item['quantity']
                product_stats[product]['revenue'] += item['line_total']
        
        if product_stats:
            prod_df = pd.DataFrame([
                {'Product': k, 'Quantity Sold': v['qty'], 'Revenue': v['revenue']}
                for k, v in product_stats.items()
            ]).sort_values('Revenue', ascending=False)
            
            prod_df['Revenue'] = prod_df['Revenue'].apply(format_currency)
            st.dataframe(prod_df, use_container_width=True, hide_index=True)
            
            st.markdown("### Revenue by Product")
            chart_data = pd.DataFrame([
                {'Product': k, 'Revenue': v['revenue']}
                for k, v in product_stats.items()
            ]).sort_values('Revenue', ascending=False).head(8)
            colors = ["#00D9FF", "#3FB950", "#FF006E", "#58A6FF", "#FFB81C", "#8E44AD", "#F39C12", "#E74C3C"]
            color_map = {product: colors[i % len(colors)] for i, product in enumerate(chart_data['Product'])}
            chart_products = alt.Chart(chart_data).mark_bar().encode(
                x='Product:N',
                y='Revenue:Q',
                color=alt.Color('Product:N', scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())))
            ).interactive()
            st.altair_chart(chart_products, use_container_width=True)
        else:
            st.info("No product data available.")

    with tab5:
        st.markdown("### All Quotes in Selected Period")
        detail_df = pd.DataFrame(filtered_quotes)
        if not detail_df.empty:
            detail_df = detail_df[['quote_number', 'customer', 'status', 'total', 'created_at']]
            detail_df.columns = ['Quote #', 'Customer', 'Status', 'Amount', 'Created']
            detail_df['Amount'] = detail_df['Amount'].apply(format_currency)
            st.dataframe(detail_df, use_container_width=True, hide_index=True)
        
        # Export
        st.markdown("### Export Data")
        if st.button("Download Report as CSV"):
            csv = detail_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"Quote_Report_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )

# Main Navigation
st.sidebar.markdown("<h2 style='color: #00D9FF; text-align: center;'>Quote Builder Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    options=["Dashboard", "Create Quote", "Manage Quotes", "Quote Details", "Customers", "Products", "Reports"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p style='color: #8B949E; font-size: 0.8em; text-align: center;'>v1.0 | Professional Quote Management</p>",
    unsafe_allow_html=True
)

if page == "Dashboard":
    page_dashboard()
elif page == "Create Quote":
    page_create_quote()
elif page == "Manage Quotes":
    page_manage_quotes()
elif page == "Quote Details":
    page_quote_detail()
elif page == "Customers":
    page_customers()
elif page == "Products":
    page_products()
elif page == "Reports":
    page_reports()