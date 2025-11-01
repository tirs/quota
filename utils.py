import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def format_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %Y")
    except:
        return date_str

def apply_dark_theme():
    st.set_page_config(
        page_title="Quote Builder Pro",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    dark_theme_css = """
    <style>
        :root {
            --primary-color: #00D9FF;
            --secondary-color: #1E1E30;
            --accent-color: #FF006E;
            --background: #0D1117;
            --surface: #161B22;
            --text-primary: #E6EAEF;
            --text-secondary: #8B949E;
            --border: #30363D;
            --success: #3FB950;
            --warning: #D29922;
            --danger: #F85149;
        }

        body {
            background-color: var(--background);
            color: var(--text-primary);
        }

        .stApp {
            background-color: var(--background);
        }

        [data-testid="stMetricValue"] {
            font-size: 2em;
            font-weight: bold;
            color: var(--primary-color);
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .metric-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 10px;
        }

        .quote-status-draft {
            background-color: rgba(139, 148, 158, 0.1);
            color: var(--text-secondary);
        }

        .quote-status-sent {
            background-color: rgba(63, 185, 80, 0.1);
            color: var(--success);
        }

        .quote-status-accepted {
            background-color: rgba(0, 217, 255, 0.1);
            color: var(--primary-color);
        }

        .quote-status-rejected {
            background-color: rgba(248, 81, 73, 0.1);
            color: var(--danger);
        }

        .stButton>button {
            background-color: var(--primary-color);
            color: var(--background);
            border: none;
            font-weight: 600;
            padding: 0.5em 1.5em;
            border-radius: 6px;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #00BCD4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3);
        }

        .stSelectbox, .stNumberInput, .stTextInput, .stTextArea {
            background-color: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-primary);
        }

        .section-header {
            color: var(--primary-color);
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }
    </style>
    """

    st.markdown(dark_theme_css, unsafe_allow_html=True)

def render_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #00D9FF;'>Quote Builder Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8B949E;'>Professional Quote Management System</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #30363D;'>", unsafe_allow_html=True)

def render_metric_card(title: str, value: str, delta: str = None, delta_type: str = None):
    with st.container():
        if delta:
            st.metric(title, value, delta, delta_color=delta_type)
        else:
            st.metric(title, value)

def generate_pdf_quote(quote_data: dict, customer_data: dict, items: list, company_info: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00D9FF'),
        spaceAfter=30,
        alignment=1
    )

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#00D9FF'),
        spaceAfter=12
    )

    story = []

    story.append(Paragraph("QUOTE", title_style))

    info_data = [
        ["QUOTE #:", quote_data.get('quote_number', 'N/A')],
        ["DATE:", format_date(quote_data.get('created_at', ''))],
        ["STATUS:", quote_data.get('status', 'Draft').upper()],
    ]

    info_table = Table(info_data, colWidths=[2*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#8B949E')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#E6EAEF')),
        ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("BILL TO:", header_style))

    customer_info = [
        [customer_data.get('name', 'N/A')],
        [f"Email: {customer_data.get('email', 'N/A')}"],
        [f"Phone: {customer_data.get('phone', 'N/A')}"],
        [f"Company: {customer_data.get('company', 'N/A')}"],
    ]

    customer_table = Table(customer_info, colWidths=[4*inch])
    customer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#E6EAEF')),
        ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("LINE ITEMS:", header_style))

    items_data = [["DESCRIPTION", "QTY", "UNIT PRICE", "TOTAL"]]
    for item in items:
        items_data.append([
            item.get('name', '')[:40],
            str(item.get('quantity', 0)),
            format_currency(item.get('unit_price', 0)),
            format_currency(item.get('line_total', 0))
        ])

    items_table = Table(items_data, colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00D9FF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D1117')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#30363D')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#161B22'), colors.HexColor('#0D1117')]),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#E6EAEF')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    totals_data = [
        ["SUBTOTAL:", format_currency(quote_data.get('subtotal', 0))],
        ["TAX ({}%)".format(int(quote_data.get('tax_rate', 0) * 100)), format_currency(quote_data.get('tax_amount', 0))],
        ["TOTAL:", format_currency(quote_data.get('total', 0))],
    ]

    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
        ('FONT', (0, 2), (-1, 2), 'Helvetica-Bold', 12),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#00D9FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#E6EAEF')),
        ('GRID', (0, 2), (-1, 2), 1, colors.HexColor('#00D9FF')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#1E1E30')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.2*inch))

    if quote_data.get('notes'):
        story.append(Paragraph("NOTES:", header_style))
        story.append(Paragraph(quote_data.get('notes', ''), styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

def status_badge(status: str) -> str:
    status_colors = {
        "draft": "#8B949E",
        "sent": "#3FB950",
        "accepted": "#00D9FF",
        "rejected": "#F85149"
    }
    color = status_colors.get(status.lower(), "#8B949E")
    return f"<span style='background-color: {color}20; color: {color}; padding: 4px 8px; border-radius: 4px; font-weight: 600;'>{status.upper()}</span>"

def apply_light_theme():
    """Apply light theme (alternative to dark)"""
    st.set_page_config(
        page_title="Quote Builder Pro",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    light_theme_css = """
    <style>
        :root {
            --primary-color: #0066CC;
            --secondary-color: #F5F5F5;
            --accent-color: #CC0033;
            --background: #FFFFFF;
            --surface: #F9F9F9;
            --text-primary: #1A1A1A;
            --text-secondary: #666666;
            --border: #E0E0E0;
            --success: #28A745;
            --warning: #FF9800;
            --danger: #DC3545;
        }
        
        body {
            background-color: var(--background);
            color: var(--text-primary);
        }
        
        .stApp {
            background-color: var(--background);
        }
    </style>
    """
    st.markdown(light_theme_css, unsafe_allow_html=True)

def get_theme_colors(theme: str = "dark") -> dict:
    """Get color palette based on theme"""
    if theme == "light":
        return {
            "primary": "#0066CC",
            "success": "#28A745",
            "warning": "#FF9800",
            "danger": "#DC3545",
            "background": "#FFFFFF",
            "surface": "#F9F9F9",
            "text": "#1A1A1A"
        }
    else:  # dark
        return {
            "primary": "#00D9FF",
            "success": "#3FB950",
            "warning": "#FFB81C",
            "danger": "#FF006E",
            "background": "#0D1117",
            "surface": "#161B22",
            "text": "#E6EAEF"
        }