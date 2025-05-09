from flask import Flask, request, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import platform
import requests
import re

if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = 'kyc.db'

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

@app.route('/')
def index():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM clients ORDER BY timestamp DESC")
        clients = c.fetchall()
    return render_template('admin.html', clients=clients)

@app.route('/start', methods=['POST'])
def start():
    name = request.form['name']
    email = request.form['email']
    amount = request.form['amount']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 'Pending'

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO clients (name, email, amount, status, timestamp, sow_category, sow_notes, risk_rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, email, amount, status, timestamp, '', '', ''))
        conn.commit()
        client_id = c.lastrowid

    return redirect(url_for('upload', client_id=client_id))

@app.route('/upload/<int:client_id>', methods=['GET', 'POST'])
def upload(client_id):
    if request.method == 'POST':
        upload_status = {}
        sow_text = ""
        id_text = ""
        selfie_flag = False
        risk_reason = []

        for file_key in ['id_doc', 'selfie', 'sow_doc']:
            file = request.files[file_key]
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_{file_key}_{filename}")
                file.save(filepath)
                upload_status[file_key] = True

                try:
                    image = Image.open(filepath)
                    image = image.convert('L')
                    image = image.filter(ImageFilter.SHARPEN)
                    image = ImageEnhance.Contrast(image).enhance(2)

                    if file_key == 'sow_doc':
                        sow_text = pytesseract.image_to_string(image)
                    elif file_key == 'id_doc':
                        id_text = pytesseract.image_to_string(image)
                        print("DEBUG: OCR extracted from ID ->", id_text)
                    elif file_key == 'selfie':
                        if image.size[0] < 100 or image.size[1] < 100:
                            selfie_flag = True
                            risk_reason.append("Selfie image is too small (may be fake or blank)")
                except Exception as e:
                    if file_key == 'sow_doc': sow_text = f"OCR failed: {e}"
                    if file_key == 'id_doc': id_text = f"OCR failed: {e}"
            else:
                upload_status[file_key] = False

        sow_category = categorize_sow(sow_text)

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM clients WHERE id=?", (client_id,))
            form_name = c.fetchone()[0]

        risk_rating, risk_reason = assess_risk(sow_text, id_text, selfie_flag, sow_category, risk_reason, form_name)

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            notes = sow_text[:500] + ("\nReasons: " + ", ".join(risk_reason) if risk_reason else "")
            c.execute("UPDATE clients SET status=?, sow_category=?, sow_notes=?, risk_rating=? WHERE id=?",
                      ('Completed', sow_category, notes, risk_rating, client_id))
            conn.commit()

        generate_pdf_report(client_id, upload_status, sow_category, sow_text, risk_rating)
        return redirect(url_for('index'))

    return render_template('upload.html', client_id=client_id)

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
        print(f"[DEBUG] Sending to Dilisense: {full_name}")
        response = requests.get(url, headers=headers, params=params)
        print(f"[DEBUG] Status: {response.status_code}")
        print(f"[DEBUG] Response: {response.text}")

        if response.status_code != 200 or not response.text.strip():
            return False, None

        result = response.json()
        matches = result.get('found_records', [])
        if matches:
            return True, matches
    except Exception as e:
        print(f"PEP API error: {e}")

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

def generate_pdf_report(client_id, upload_status, sow_category, sow_text, risk_rating):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        client = c.fetchone()
        form_name = client[1]
        c.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        client = c.fetchone()

    form_name = client[1]
    reason_log = []
    risk_rating, reason_log = assess_risk(sow_text, upload_status.get('id_ocr_text', ''), upload_status.get('selfie_flag', False), sow_category, reason_log, form_name)

    pdf_path = f"uploads/report_{client_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, f"KYC Report for {client[1]}")
    c.drawString(100, 730, f"Email: {client[2]}")
    c.drawString(100, 710, f"Amount: {client[3]}")
    c.drawString(100, 690, f"Timestamp: {client[5]}")
    c.drawString(100, 670, f"Status: {client[4]}")

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
    for i, line in enumerate(sow_text[:300].splitlines()):
        c.drawString(120, y - 70 - i*15, line)

    c.drawString(100, y - 90 - i*15, "Reason Log:")
    for j, reason in enumerate(reason_log):
        c.drawString(120, y - 110 - (i+j)*15, f"- {reason}")

    c.save()

@app.route('/report/<int:client_id>')
def report(client_id):
    pdf_path = f"uploads/report_{client_id}.pdf"
    return send_file(pdf_path, as_attachment=True)

@app.route('/new')
def new():
    return render_template('new.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
