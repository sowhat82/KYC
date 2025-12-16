"""
KYC/AML Verification System - Main Application
Comprehensive demo for investor presentation with deterministic risk scoring.
"""

import streamlit as st
import sqlite3
import os
import json
from datetime import datetime, date
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import platform
import re

# Import custom modules
from risk_engine import calculate_risk, get_recommended_action
from reporting.pdf_generator import generate_pdf

# Configure Tesseract
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

# Constants
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_NAME = 'kyc.db'

# Page configuration
st.set_page_config(
    page_title="KYC/AML Verification System",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #145a8a;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        color: #856404;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
    }
    .risk-medium {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
    }
    .risk-low {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
    }
    /* Hide sidebar by default */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 0px;
        max-width: 0px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0px;
        max-width: 0px;
        margin-left: -21rem;
    }
    /* Hide sidebar toggle button */
    button[kind="header"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    """Create database table if it doesn't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        dob TEXT,
                        nationality TEXT,
                        address TEXT,
                        occupation TEXT,
                        email TEXT,
                        amount REAL,
                        source_of_wealth TEXT,
                        purpose TEXT,
                        status TEXT,
                        timestamp TEXT,
                        sow_category TEXT,
                        risk_score INTEGER,
                        risk_band TEXT,
                        risk_reasons TEXT
                    )''')
        conn.commit()

init_db()

# Load countries data
def load_countries():
    """Load countries and industries from JSON file."""
    try:
        with open('data/countries.json', 'r') as f:
            data = json.load(f)
            return data['countries'], data['high_risk_industries']
    except:
        return [], []

countries, industries = load_countries()

# Initialize session state
def init_session_state():
    """Initialize all session state variables."""
    if 'page' not in st.session_state:
        st.session_state.page = 'Submit New KYC'
    if 'client_data' not in st.session_state:
        st.session_state.client_data = {}
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'temp_files' not in st.session_state:
        st.session_state.temp_files = {}
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'risk_result' not in st.session_state:
        st.session_state.risk_result = None
    if 'client_id' not in st.session_state:
        st.session_state.client_id = None

init_session_state()

def reset_application():
    """Reset application state for new submission."""
    # Clear file uploader states
    for key in ['id_doc', 'selfie', 'proof_address', 'sow_doc']:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.client_data = {}
    st.session_state.uploaded_files = {}
    st.session_state.temp_files = {}
    st.session_state.current_step = 1
    st.session_state.risk_result = None
    st.session_state.client_id = None

# ==================== MAIN NAVIGATION ====================

def main():
    """Main application with page navigation."""

    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Submit New KYC", "Admin Dashboard", "About"],
        key="page_selector"
    )

    # Update page in session state
    if page != st.session_state.page:
        st.session_state.page = page
        # Don't reset state when going to admin dashboard
        if page == "Submit New KYC":
            pass  # Keep state for multi-step form

    # Route to appropriate page
    if page == "Submit New KYC":
        show_kyc_submission_page()
    elif page == "Admin Dashboard":
        show_admin_dashboard()
    elif page == "About":
        show_about_page()

# ==================== KYC SUBMISSION PAGE ====================

def show_kyc_submission_page():
    """Multi-step KYC submission form."""
    st.markdown('<h1 class="main-header">🔒 KYC/AML Verification System</h1>', unsafe_allow_html=True)

    # Progress indicator
    step_names = ["Client Information", "Document Upload", "Verification Results"]
    current = st.session_state.current_step

    # Show progress bar
    progress_cols = st.columns(3)
    for idx, step_name in enumerate(step_names, 1):
        with progress_cols[idx-1]:
            if idx < current:
                st.success(f"✓ Step {idx}: {step_name}")
            elif idx == current:
                st.info(f"→ Step {idx}: {step_name}")
            else:
                st.write(f"Step {idx}: {step_name}")

    st.markdown("---")

    # Display appropriate step
    if current == 1:
        show_client_information_form()
    elif current == 2:
        show_document_upload_form()
    elif current == 3:
        show_verification_results()

def show_client_information_form():
    """Step 1: Comprehensive client information form."""
    st.subheader("Step 1: Client Information")
    st.markdown('<div class="info-box">Please provide complete and accurate information. All fields marked with * are required.</div>', unsafe_allow_html=True)

    with st.form("client_info_form"):
        # Row 1: Name and DOB
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Legal Name *", placeholder="e.g., John Michael Smith")
        with col2:
            dob = st.date_input(
                "Date of Birth *",
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                value=date(1990, 1, 1)
            )

        # Row 2: Nationality and Email
        col3, col4 = st.columns(2)
        with col3:
            nationality = st.selectbox("Nationality *", options=[""] + countries)
        with col4:
            email = st.text_input("Email Address *", placeholder="john.smith@example.com")

        # Row 3: Address
        address = st.text_area(
            "Residential Address *",
            placeholder="Street address, city, postal code, country",
            height=100
        )

        # Row 4: Occupation and Amount
        col5, col6 = st.columns(2)
        with col5:
            occupation = st.selectbox(
                "Occupation / Industry *",
                options=[""] + [
                    "Accountant", "Architect", "Banking", "Business Owner",
                    "Consultant", "Doctor", "Engineer", "Entrepreneur",
                    "Finance Professional", "Government Official", "Healthcare",
                    "IT Professional", "Lawyer", "Professor", "Retired", "Teacher"
                ] + industries  # Add high-risk industries
            )
        with col6:
            amount = st.number_input(
                "Transaction Amount (USD) *",
                min_value=0.0,
                max_value=10000000.0,
                value=10000.0,
                step=1000.0,
                format="%.2f"
            )

        # Row 5: Source of Wealth
        source_of_wealth = st.text_area(
            "Source of Wealth Description *",
            placeholder="Describe the origin of your funds (e.g., employment income, business profits, investment returns, inheritance, property sale, etc.)",
            height=100
        )

        # Row 6: Purpose
        purpose = st.selectbox(
            "Purpose of Transaction *",
            options=["", "Investment", "Property Purchase", "Business Operations",
                    "Savings/Deposit", "Loan Repayment", "International Transfer",
                    "Other"]
        )

        # Submit button
        submitted = st.form_submit_button("Continue to Document Upload →")

    # Handle form submission outside the form context
    if submitted:
        # Validation
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Please enter a valid full name")
        if not nationality:
            errors.append("Please select your nationality")
        if not email or '@' not in email:
            errors.append("Please enter a valid email address")
        if not address or len(address.strip()) < 3:
            errors.append("Please enter your address")
        if not occupation:
            errors.append("Please select your occupation")
        if amount <= 0:
            errors.append("Transaction amount must be greater than zero")
        if not source_of_wealth or len(source_of_wealth.strip()) < 3:
            errors.append("Please provide a source of wealth description")
        if not purpose:
            errors.append("Please select the purpose of transaction")

        if errors:
            st.error("**Please complete all required fields:**")
            for error in errors:
                st.error(f"• {error}")
        else:
            # Store client data in session state
            st.session_state.client_data = {
                'name': name.strip(),
                'dob': dob.strftime('%Y-%m-%d'),
                'nationality': nationality,
                'address': address.strip(),
                'occupation': occupation,
                'email': email.strip().lower(),
                'amount': amount,
                'source_of_wealth': source_of_wealth.strip(),
                'purpose': purpose,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Move to next step
            st.session_state.current_step = 2
            st.rerun()

def show_document_upload_form():
    """Step 2: Document upload with file validation."""
    st.subheader("Step 2: Document Upload")

    client = st.session_state.client_data
    st.markdown(f'<div class="success-box">✓ Client Information saved for <strong>{client["name"]}</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Please upload the required documents. Accepted formats: PNG, JPG, JPEG, PDF</div>', unsafe_allow_html=True)

    # File uploaders - simple labels, no markdown
    id_doc = st.file_uploader(
        "1. ID Document (Passport/National ID) *",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key="id_doc"
    )

    selfie = st.file_uploader(
        "2. Selfie Photo *",
        type=['png', 'jpg', 'jpeg'],
        key="selfie"
    )

    proof_address = st.file_uploader(
        "3. Proof of Address (Utility Bill/Bank Statement) *",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key="proof_address"
    )

    sow_doc = st.file_uploader(
        "4. Source of Wealth Document (Payslip/Tax Return/etc.) *",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key="sow_doc"
    )

    st.markdown("---")

    # Show upload status
    uploaded_count = sum([id_doc is not None, selfie is not None, proof_address is not None, sow_doc is not None])
    if uploaded_count > 0:
        st.info(f"📎 {uploaded_count} document(s) uploaded")

    # Action buttons
    col_back, col_submit = st.columns([1, 1])

    with col_back:
        if st.button("← Back to Client Info", key="back_button", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()

    with col_submit:
        if st.button("Submit for Verification →", key="submit_button", use_container_width=True, type="primary"):
            # Get files directly from uploaders
            files_dict = {
                'id_doc': id_doc,
                'selfie': selfie,
                'proof_address': proof_address,
                'sow_doc': sow_doc
            }

            # Check if at least ID document is uploaded
            if not id_doc:
                st.error("⚠️ At minimum, please upload your ID document to proceed")
            else:
                # Process the submission
                with st.spinner("Processing documents and performing risk assessment..."):
                    process_kyc_submission(files_dict)
                st.session_state.current_step = 3
                st.rerun()

def process_kyc_submission(files_dict):
    """Process KYC submission: save files, extract data, calculate risk, generate report."""

    # Save client to database first to get ID
    client = st.session_state.client_data
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO clients (
            name, dob, nationality, address, occupation, email, amount,
            source_of_wealth, purpose, status, timestamp, sow_category,
            risk_score, risk_band, risk_reasons
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            client['name'], client['dob'], client['nationality'], client['address'],
            client['occupation'], client['email'], client['amount'],
            client['source_of_wealth'], client['purpose'], 'Pending',
            client['timestamp'], '', 0, '', ''
        ))
        conn.commit()
        client_id = c.lastrowid

    st.session_state.client_id = client_id
    client['id'] = client_id

    # Save uploaded files to disk
    saved_files = {}
    sow_text = ""

    for file_key, file in files_dict.items():
        if file:
            filename = f"{client_id}_{file_key}_{file.name}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            with open(filepath, 'wb') as f:
                f.write(file.getbuffer())

            saved_files[file_key] = filepath

            # Extract text from SOW document using OCR
            if file_key == 'sow_doc':
                try:
                    image = Image.open(filepath)
                    image = image.convert('L')
                    image = image.filter(ImageFilter.SHARPEN)
                    image = ImageEnhance.Contrast(image).enhance(2)
                    sow_text = pytesseract.image_to_string(image)
                except:
                    sow_text = ""

    # Determine SOW category from extracted text or description
    sow_category = categorize_sow(sow_text if sow_text else client['source_of_wealth'])

    # Calculate risk score
    risk_result = calculate_risk(client, files_dict)

    # Update database with results
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""UPDATE clients SET
            status=?, sow_category=?, risk_score=?, risk_band=?, risk_reasons=?
            WHERE id=?""",
            ('Completed', sow_category, risk_result['score'], risk_result['band'],
             json.dumps(risk_result['reasons']), client_id)
        )
        conn.commit()

    # Generate PDF report
    report_data = {
        'client_data': client,
        'risk_result': risk_result,
        'documents': {k: v is not None for k, v in files_dict.items()},
        'sow_category': sow_category,
        'timestamp': client['timestamp']
    }

    pdf_path = os.path.join(UPLOAD_FOLDER, f"report_{client_id}.pdf")
    generate_pdf(report_data, pdf_path)

    # Store results in session state
    st.session_state.risk_result = risk_result
    st.session_state.sow_category = sow_category
    st.session_state.pdf_path = pdf_path
    st.session_state.uploaded_files = saved_files

def categorize_sow(text):
    """Categorize source of wealth based on keywords."""
    text = text.lower()
    if 'salary' in text or 'employment' in text or 'payslip' in text or 'wage' in text:
        return 'Employment Income'
    elif 'business' in text or 'profit' in text or 'company' in text:
        return 'Business Profits'
    elif 'investment' in text or 'dividend' in text or 'capital gain' in text:
        return 'Investment Returns'
    elif 'inheritance' in text or 'estate' in text or 'bequest' in text:
        return 'Inheritance'
    elif 'property' in text or 'real estate' in text or 'sale of asset' in text:
        return 'Asset Sale'
    elif 'gift' in text or 'donation' in text:
        return 'Gift'
    elif 'pension' in text or 'retirement' in text:
        return 'Pension/Retirement'
    elif text.strip() == "":
        return 'Undetected'
    else:
        return 'Other'

def show_verification_results():
    """Step 3: Display risk assessment results."""
    st.subheader("Step 3: Verification Results")

    risk = st.session_state.risk_result
    client = st.session_state.client_data
    sow_category = st.session_state.sow_category

    # Success message
    st.markdown('<div class="success-box">✓ KYC verification completed successfully!</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Display risk score and band
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Risk Score", f"{risk['score']} / 100")

    with col2:
        risk_band = risk['band']
        risk_class = f"risk-{risk_band.lower()}"
        st.markdown(f'<div class="{risk_class}">Risk Band: {risk_band}</div>', unsafe_allow_html=True)

    with col3:
        st.metric("SOW Category", sow_category)

    st.markdown("---")

    # Recommended action
    action = get_recommended_action(risk_band)
    st.subheader("Recommended Action")
    if "APPROVE" in action:
        st.success(action)
    elif "REQUEST EDD" in action:
        st.warning(action)
    else:
        st.error(action)

    # Triggered rules
    st.subheader("Risk Assessment Details")
    with st.expander("📋 Triggered Rules", expanded=True):
        reasons = risk['reasons']
        if reasons:
            for reason in reasons:
                rule_name = reason['rule']
                points = reason['points']
                description = reason['description']

                if points > 0:
                    st.markdown(f"**{rule_name}** (+{points} points)")
                    st.write(f"  ↳ {description}")
                else:
                    st.info(f"**{rule_name}**: {description}")
        else:
            st.info("No risk factors detected")

    # Download PDF report
    st.markdown("---")
    if os.path.exists(st.session_state.pdf_path):
        with open(st.session_state.pdf_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"KYC_Report_{client['name'].replace(' ', '_')}_{st.session_state.client_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # Start new application button
    st.markdown("---")
    if st.button("🔄 Start New Application", use_container_width=True):
        reset_application()
        st.rerun()

# ==================== ADMIN DASHBOARD ====================

def show_admin_dashboard():
    """Admin dashboard with filters and action buttons."""
    st.markdown('<h1 class="main-header">👨‍💼 Admin Dashboard</h1>', unsafe_allow_html=True)

    # Fetch all clients
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM clients ORDER BY timestamp DESC")
        clients = c.fetchall()

    if not clients:
        st.info("📭 No KYC applications submitted yet.")
        return

    # Summary statistics
    st.subheader("📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total = len(clients)
    completed = sum(1 for c in clients if c[10] == 'Completed')
    pending = sum(1 for c in clients if c[10] == 'Pending')
    high_risk = sum(1 for c in clients if c[14] == 'High')

    col1.metric("Total Applications", total)
    col2.metric("Completed", completed)
    col3.metric("Pending", pending)
    col4.metric("High Risk", high_risk, delta=None if high_risk == 0 else f"{high_risk}")

    st.markdown("---")

    # Filters
    st.subheader("🔍 Filters")
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        risk_filter = st.selectbox(
            "Filter by Risk Band",
            options=["All", "Low", "Medium", "High"]
        )

    with filter_col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "Pending", "Completed"]
        )

    # Apply filters
    filtered_clients = clients
    if risk_filter != "All":
        filtered_clients = [c for c in filtered_clients if c[14] == risk_filter]
    if status_filter != "All":
        filtered_clients = [c for c in filtered_clients if c[10] == status_filter]

    st.markdown("---")
    st.subheader(f"📋 Applications ({len(filtered_clients)} shown)")

    # Display clients
    for client in filtered_clients:
        (client_id, name, dob, nationality, address, occupation, email, amount,
         source_of_wealth, purpose, status, timestamp, sow_category,
         risk_score, risk_band, risk_reasons) = client

        with st.expander(f"**{name}** - {email} | ID: {client_id} | {timestamp}"):
            info_col1, info_col2, info_col3 = st.columns(3)

            with info_col1:
                st.write(f"**Amount:** ${amount:,.2f}")
                st.write(f"**Nationality:** {nationality}")
                st.write(f"**DOB:** {dob}")
                st.write(f"**Occupation:** {occupation}")

            with info_col2:
                st.write(f"**Status:** {status}")
                st.write(f"**SOW Category:** {sow_category if sow_category else 'N/A'}")
                st.write(f"**Purpose:** {purpose}")

                if risk_band:
                    risk_class = f"risk-{risk_band.lower()}"
                    st.markdown(f'<div class="{risk_class}">Risk: {risk_band} ({risk_score}/100)</div>', unsafe_allow_html=True)

            with info_col3:
                # Download report button
                pdf_path = os.path.join(UPLOAD_FOLDER, f"report_{client_id}.pdf")
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        st.download_button(
                            label="📄 Download Report",
                            data=pdf_file.read(),
                            file_name=f"KYC_Report_{client_id}.pdf",
                            mime="application/pdf",
                            key=f"download_{client_id}"
                        )

                # Action buttons (demo only - no backend action)
                action_col1, action_col2, action_col3 = st.columns(3)
                with action_col1:
                    if st.button("✅ Approve", key=f"approve_{client_id}", use_container_width=True):
                        st.success("Approved!")
                with action_col2:
                    if st.button("🔍 EDD", key=f"edd_{client_id}", use_container_width=True):
                        st.warning("EDD Requested")
                with action_col3:
                    if st.button("❌ Reject", key=f"reject_{client_id}", use_container_width=True):
                        st.error("Rejected")

# ==================== ABOUT PAGE ====================

def show_about_page():
    """About page with system information."""
    st.markdown('<h1 class="main-header">ℹ️ About This System</h1>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    ## KYC/AML Verification System - Demo

    This is a comprehensive demonstration of an automated KYC (Know Your Customer) and AML (Anti-Money Laundering)
    verification system designed for financial institutions and regulated entities.

    ### 🎯 Key Features

    - **Comprehensive Client Onboarding**: Multi-step form collecting detailed client information
    - **Document Management**: Upload and process ID documents, selfies, proof of address, and source of wealth documents
    - **Deterministic Risk Scoring**: Rules-based risk engine with transparent scoring methodology
    - **Automated Screening**: PEP (Politically Exposed Persons), sanctions, and adverse media checks
    - **Professional Reporting**: Generate detailed PDF reports with risk assessment details
    - **Admin Dashboard**: Monitor all applications with filtering and action capabilities

    ### 🔍 Risk Assessment Rules

    The system evaluates applications based on multiple risk factors:

    | Rule | Points | Threshold |
    |------|--------|-----------|
    | PEP/Sanctions Match | +40 | Name matches watchlist |
    | High-Risk Country | +20 | Jurisdiction flagged |
    | High Transaction Amount | +15 | ≥ $100,000 |
    | High-Risk Occupation | +10 | Casino, crypto, etc. |
    | Unusual Source of Wealth | +10 | Red-flag keywords |
    | Missing Documents | +10 | Required docs absent |
    | Adverse Media | +15 | Negative news match |
    | Address Mismatch | +5 | OCR verification fails |

    **Risk Bands:**
    - **Low Risk** (0-24 points): Standard approval
    - **Medium Risk** (25-59 points): Enhanced Due Diligence required
    - **High Risk** (60+ points): Reject or escalate to compliance

    ### ⚠️ Important Disclaimer

    **This is a demonstration system using mock data:**
    - PEP and sanctions lists are simulated for demo purposes
    - Adverse media matches use a limited test dataset
    - OCR and document verification are simplified
    - The system should NOT be used for actual compliance decisions

    All real KYC/AML systems must:
    - Use official watchlists (OFAC, UN, EU, etc.)
    - Comply with local regulations (FATF, FinCEN, FCA, MAS, etc.)
    - Include manual review by qualified compliance officers
    - Maintain audit trails and documentation
    - Follow data protection regulations (GDPR, PDPA, etc.)

    ### 🛠️ Technology Stack

    - **Frontend**: Streamlit
    - **Backend**: Python with SQLite
    - **OCR**: Tesseract
    - **Reporting**: ReportLab
    - **Risk Engine**: Custom rules-based scoring

    ### 📞 Support

    For questions about this demo system, please contact your system administrator.

    ---

    **Version:** 2.0 (Investor Demo)
    **Last Updated:** December 2025
    """)

# ==================== RUN APP ====================

if __name__ == "__main__":
    main()
