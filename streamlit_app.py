import streamlit as st
import sqlite3
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import platform
import requests
import re

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
    page_title="KYC Verification System",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 8px;
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
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        color: #856404;
    }
    .risk-high {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-low {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        amount TEXT,
                        status TEXT,
                        timestamp TEXT,
                        sow_category TEXT,
                        sow_notes TEXT,
                        risk_rating TEXT
                    )''')
        conn.commit()

init_db()

# Helper functions from original Flask app
def categorize_sow(text):
    text = text.lower()
    if 'salary' in text or 'income' in text:
        return 'Salary'
    elif 'cpf' in text:
        return 'CPF Withdrawal'
    elif 'dividend' in text or 'investment' in text:
        return 'Investment Income'
    elif 'gift' in text or 'inheritance' in text:
        return 'Gift or Inheritance'
    elif 'sales' in text or 'property' in text:
        return 'Asset Sale'
    elif text.strip() == "":
        return 'Undetected'
    else:
        return 'Other'

def extract_possible_name(id_text):
    for line in id_text.splitlines():
        if len(line.strip().split()) >= 2:
            return line.strip()
    return None

def check_pep_status(full_name):
    # Get API key from Streamlit secrets in production, or use hardcoded value for local dev
    try:
        api_key = st.secrets["DILISENSE_API_KEY"]
    except:
        # Fallback for local development
        api_key = 'X5kXACRdQW3b9lJRqHxap4yTu9EkxsDy7N3rnNQf'

    url = "https://api.dilisense.com/v1/checkIndividual"
    params = {
        "names": full_name,
        "fuzzy_search": 1,
        "includes": "dilisense_pep"
    }
    headers = {
        'x-api-key': api_key
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200 or not response.text.strip():
            return False, None

        result = response.json()
        matches = result.get('found_records', [])
        if matches:
            return True, matches
    except Exception as e:
        st.warning(f"PEP API error: {e}")

    return False, None

def assess_risk(sow_text, id_text, selfie_flag, sow_category, reason_log, form_name=None):
    red_flags = ['cash deposit', 'loan', 'borrowed', 'gift', 'crypto', 'cryptocurrency']
    yellow_flags = ['business income', 'sales', 'earned overseas', 'family transfer', 'remittance', 'inheritance', 'foreign source']
    watchlist_keywords = ['iran', 'islamic republic', 'republic of iran', 'tehran', 'persian', 'north korea', 'syria', 'terror', 'sanction']

    sow_text = sow_text.lower()
    id_text = re.sub(r'[^a-zA-Z ]', ' ', id_text)
    id_text = ' '.join(id_text.split()).lower()

    if any(term in sow_text for term in red_flags):
        reason_log.append("SOW contains red-flag terms")
        return 'High', reason_log

    for term in watchlist_keywords:
        for word in id_text.split():
            if term in word:
                reason_log.append(f"ID contains high-risk keyword: {term}")
                return 'High', reason_log

    if selfie_flag:
        reason_log.append("Selfie failed verification checks")
        return 'High', reason_log

    name_candidate = extract_possible_name(id_text)
    if name_candidate:
        pep_hit, pep_info = check_pep_status(name_candidate)
        if pep_hit:
            reason_log.append(f"PEP match from ID: {pep_info[0].get('name', 'unknown')}")
            return 'Medium', reason_log

    if form_name:
        pep_hit_manual, pep_info_manual = check_pep_status(form_name)
        if pep_hit_manual:
            reason_log.append(f"Entered name PEP match: {pep_info_manual[0].get('name', 'unknown')}")
            return 'Medium', reason_log

    if any(term in sow_text for term in yellow_flags):
        reason_log.append("SOW contains unclear or uncorroborated terms")
        return 'Medium', reason_log

    if sow_category == 'Undetected' or sow_text.strip() == "":
        reason_log.append("SOW could not be detected")
        return 'Medium', reason_log

    return 'Low', reason_log

def generate_pdf_report(client_id, upload_status, sow_category, sow_text, risk_rating, reason_log, client_data):
    pdf_path = f"uploads/report_{client_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, f"KYC Report for {client_data['name']}")
    c.drawString(100, 730, f"Email: {client_data['email']}")
    c.drawString(100, 710, f"Amount: {client_data['amount']}")
    c.drawString(100, 690, f"Timestamp: {client_data['timestamp']}")
    c.drawString(100, 670, f"Status: Completed")

    c.drawString(100, 640, "Documents Submitted:")
    y = 620
    for doc_type in ['id_doc', 'selfie', 'sow_doc']:
        label = {'id_doc': 'ID Document', 'selfie': 'Selfie Photo', 'sow_doc': 'Source of Wealth'}[doc_type]
        submitted = 'Yes' if upload_status.get(doc_type) else 'No'
        c.drawString(120, y, f"{label}: {submitted}")
        y -= 20

    c.drawString(100, y - 10, f"Detected SOW Category: {sow_category}")
    c.drawString(100, y - 30, f"Risk Rating: {risk_rating}")
    c.drawString(100, y - 50, "SOW Text Extract (first 300 chars):")

    lines_written = 0
    for i, line in enumerate(sow_text[:300].splitlines()):
        if y - 70 - i*15 > 100:
            c.drawString(120, y - 70 - i*15, line[:80])
            lines_written = i

    c.drawString(100, y - 90 - lines_written*15, "Reason Log:")
    for j, reason in enumerate(reason_log):
        if y - 110 - (lines_written+j)*15 > 50:
            c.drawString(120, y - 110 - (lines_written+j)*15, f"- {reason}")

    c.save()
    return pdf_path

# Main App
def main():
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Submit New KYC", "Admin Dashboard", "About"])

    if page == "Submit New KYC":
        show_new_kyc_page()
    elif page == "Admin Dashboard":
        show_admin_dashboard()
    elif page == "About":
        show_about_page()

def show_new_kyc_page():
    st.markdown('<h1 class="main-header">KYC Verification System</h1>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Complete the form below to submit your KYC application. All fields are required.</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Check if client is already registered
    if 'client_id' not in st.session_state:
        st.session_state.client_id = None
        st.session_state.show_upload = False
        st.session_state.processing_complete = False
        st.session_state.processing_results = None

    if not st.session_state.show_upload:
        # Registration Form
        st.subheader("Step 1: Client Information")

        with st.form("registration_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name", placeholder="Enter your full name")
                email = st.text_input("Email Address", placeholder="your.email@example.com")

            with col2:
                amount = st.text_input("Transaction Amount (SGD)", placeholder="e.g., 50000")

            submit_button = st.form_submit_button("Continue to Document Upload")

            if submit_button:
                if not name or not email or not amount:
                    st.error("Please fill in all fields before continuing.")
                else:
                    # Save to database
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    status = 'Pending'

                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO clients (name, email, amount, status, timestamp, sow_category, sow_notes, risk_rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (name, email, amount, status, timestamp, '', '', ''))
                        conn.commit()
                        client_id = c.lastrowid

                    st.session_state.client_id = client_id
                    st.session_state.client_name = name
                    st.session_state.client_email = email
                    st.session_state.client_amount = amount
                    st.session_state.client_timestamp = timestamp
                    st.session_state.show_upload = True
                    st.rerun()

    else:
        # Document Upload Form
        st.subheader("Step 2: Document Upload")
        st.markdown(f'<div class="success-box">Registration successful for <strong>{st.session_state.client_name}</strong>!</div>', unsafe_allow_html=True)
        st.markdown("---")

        st.info("Please upload the following documents:")

        with st.form("upload_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**ID Document**")
                id_doc = st.file_uploader("Upload ID (NRIC, Passport, etc.)", type=['png', 'jpg', 'jpeg', 'pdf'], key="id_doc")

            with col2:
                st.markdown("**Selfie Photo**")
                selfie = st.file_uploader("Upload a clear selfie", type=['png', 'jpg', 'jpeg'], key="selfie")

            with col3:
                st.markdown("**Source of Wealth Document**")
                sow_doc = st.file_uploader("Upload proof of income/wealth", type=['png', 'jpg', 'jpeg', 'pdf'], key="sow_doc")

            submit_docs = st.form_submit_button("Submit Documents for Verification")

            if submit_docs:
                if not id_doc or not selfie or not sow_doc:
                    st.error("Please upload all three documents before submitting.")
                else:
                    with st.spinner("Processing your documents... This may take a moment."):
                        try:
                            results = process_documents(
                                st.session_state.client_id,
                                id_doc,
                                selfie,
                                sow_doc,
                                st.session_state.client_name
                            )
                            st.session_state.processing_complete = True
                            st.session_state.processing_results = results
                            st.rerun()
                        except Exception as e:
                            st.error(f"An error occurred while processing documents: {str(e)}")
                            st.error("Please try again or contact support if the issue persists.")

        # Display results outside of form
        if st.session_state.processing_complete and st.session_state.processing_results:
            results = st.session_state.processing_results

            st.success("Documents processed successfully!")
            st.markdown("---")
            st.subheader("Verification Results")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Source of Wealth Category", results['sow_category'])
            with col2:
                risk_class = f"risk-{results['risk_rating'].lower()}"
                st.markdown(f'<div class="{risk_class}">Risk Rating: {results["risk_rating"]}</div>', unsafe_allow_html=True)

            if results['risk_reason']:
                st.markdown("**Risk Assessment Reasons:**")
                for reason in results['risk_reason']:
                    st.write(f"- {reason}")

            # Download PDF
            if os.path.exists(results['pdf_path']):
                with open(results['pdf_path'], 'rb') as f:
                    st.download_button(
                        label="Download PDF Report",
                        data=f,
                        file_name=f"KYC_Report_{st.session_state.client_id}.pdf",
                        mime="application/pdf"
                    )

        # Reset button
        if st.button("Start New Application"):
            st.session_state.client_id = None
            st.session_state.show_upload = False
            st.session_state.processing_complete = False
            st.session_state.processing_results = None
            st.rerun()

def process_documents(client_id, id_doc, selfie, sow_doc, client_name):
    upload_status = {}
    sow_text = ""
    id_text = ""
    selfie_flag = False
    risk_reason = []

    # Process each document
    files = {
        'id_doc': id_doc,
        'selfie': selfie,
        'sow_doc': sow_doc
    }

    for file_key, file in files.items():
        if file:
            try:
                filename = file.name
                filepath = os.path.join(UPLOAD_FOLDER, f"{client_id}_{file_key}_{filename}")

                # Save the uploaded file
                with open(filepath, 'wb') as f:
                    f.write(file.getbuffer())

                upload_status[file_key] = True

                # Process the image with OCR
                image = Image.open(filepath)
                image = image.convert('L')
                image = image.filter(ImageFilter.SHARPEN)
                image = ImageEnhance.Contrast(image).enhance(2)

                if file_key == 'sow_doc':
                    sow_text = pytesseract.image_to_string(image)
                elif file_key == 'id_doc':
                    id_text = pytesseract.image_to_string(image)
                elif file_key == 'selfie':
                    if image.size[0] < 100 or image.size[1] < 100:
                        selfie_flag = True
                        risk_reason.append("Selfie image is too small (may be fake or blank)")
            except Exception as e:
                st.warning(f"Error processing {file_key}: {str(e)}")
                upload_status[file_key] = False
                if file_key == 'sow_doc':
                    sow_text = f"OCR failed: {e}"
                if file_key == 'id_doc':
                    id_text = f"OCR failed: {e}"
        else:
            upload_status[file_key] = False

    # Categorize SOW
    sow_category = categorize_sow(sow_text)

    # Assess risk
    risk_rating, risk_reason = assess_risk(sow_text, id_text, selfie_flag, sow_category, risk_reason, client_name)

    # Update database
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        notes = sow_text[:500] + ("\nReasons: " + ", ".join(risk_reason) if risk_reason else "")
        c.execute("UPDATE clients SET status=?, sow_category=?, sow_notes=?, risk_rating=? WHERE id=?",
                  ('Completed', sow_category, notes, risk_rating, client_id))
        conn.commit()

    # Generate PDF report
    client_data = {
        'name': st.session_state.client_name,
        'email': st.session_state.client_email,
        'amount': st.session_state.client_amount,
        'timestamp': st.session_state.client_timestamp
    }

    pdf_path = generate_pdf_report(client_id, upload_status, sow_category, sow_text, risk_rating, risk_reason, client_data)

    # Return results instead of displaying them
    return {
        'sow_category': sow_category,
        'risk_rating': risk_rating,
        'risk_reason': risk_reason,
        'pdf_path': pdf_path
    }

def show_admin_dashboard():
    st.markdown('<h1 class="main-header">Admin Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Fetch all clients
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM clients ORDER BY timestamp DESC")
        clients = c.fetchall()

    if not clients:
        st.info("No KYC applications submitted yet.")
    else:
        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)

        total_clients = len(clients)
        completed = sum(1 for c in clients if c[4] == 'Completed')
        pending = sum(1 for c in clients if c[4] == 'Pending')
        high_risk = sum(1 for c in clients if c[8] == 'High')

        col1.metric("Total Applications", total_clients)
        col2.metric("Completed", completed)
        col3.metric("Pending", pending)
        col4.metric("High Risk", high_risk)

        st.markdown("---")
        st.subheader("All KYC Applications")

        # Display clients in a table
        for client in clients:
            client_id, name, email, amount, status, timestamp, sow_category, sow_notes, risk_rating = client

            with st.expander(f"**{name}** - {email} (ID: {client_id})"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Amount:** SGD {amount}")
                    st.write(f"**Status:** {status}")
                    st.write(f"**Submitted:** {timestamp}")

                with col2:
                    st.write(f"**SOW Category:** {sow_category if sow_category else 'N/A'}")
                    if risk_rating:
                        risk_class = f"risk-{risk_rating.lower()}"
                        st.markdown(f'<div class="{risk_class}">Risk: {risk_rating}</div>', unsafe_allow_html=True)

                with col3:
                    # Check if PDF exists
                    pdf_path = f"uploads/report_{client_id}.pdf"
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                label="Download Report",
                                data=f,
                                file_name=f"KYC_Report_{client_id}.pdf",
                                mime="application/pdf",
                                key=f"download_{client_id}"
                            )
                    else:
                        st.write("Report not available")

                if sow_notes:
                    st.markdown("**Notes:**")
                    st.text_area("", value=sow_notes, height=100, key=f"notes_{client_id}", disabled=True)

def show_about_page():
    st.markdown('<h1 class="main-header">About KYC Verification System</h1>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    ## What is KYC?

    **Know Your Customer (KYC)** is a regulatory requirement for financial institutions to verify the identity
    of their clients and assess potential risks of illegal intentions.

    ## How This System Works

    This automated KYC verification system helps streamline the customer onboarding process by:

    1. **Collecting Client Information** - Basic details like name, email, and transaction amount
    2. **Document Verification** - Analyzing ID documents, selfies, and source of wealth documentation
    3. **Automated Risk Assessment** - Using OCR and AI to detect potential risk factors including:
       - Red flag keywords in source of wealth documents
       - PEP (Politically Exposed Person) screening
       - Document quality checks
       - Watchlist screening
    4. **Report Generation** - Creating comprehensive PDF reports for compliance records

    ## Features

    - **User-Friendly Interface** - Simple, intuitive design for non-technical users
    - **Automated Document Processing** - OCR technology extracts text from uploaded documents
    - **Risk-Based Approach** - Three-tier risk rating system (Low, Medium, High)
    - **PEP Screening** - Integration with Dilisense API for politically exposed person checks
    - **Comprehensive Reporting** - Detailed PDF reports for audit trails
    - **Admin Dashboard** - Overview of all applications with filtering and download options

    ## Risk Rating System

    - **Low Risk** - Standard verification passed with no concerns
    - **Medium Risk** - Some flags detected, manual review recommended
    - **High Risk** - Critical flags detected, requires immediate attention

    ## Technology Stack

    - **Streamlit** - Web application framework
    - **SQLite** - Database for client records
    - **Tesseract OCR** - Optical character recognition
    - **ReportLab** - PDF generation
    - **Dilisense API** - PEP screening

    ---

    For questions or support, please contact your system administrator.
    """)

if __name__ == "__main__":
    main()
