# 🚀 Quick Start Guide - KYC/AML System v2.0

## Launch the Application

```bash
# Navigate to project directory
cd /workspaces/KYC

# Run the new v2.0 application
streamlit run app_v2.py

# Or run on a specific port
streamlit run app_v2.py --server.port 8502
```

The app will be available at:
- **Local:** http://localhost:8501 (or 8502)
- **Network:** Will display in terminal output

---

## 📝 Quick Test (2 Minutes)

### High-Risk Test

1. **Go to "Submit New KYC"**

2. **Fill the form:**
   - Name: `Donald Trump`
   - DOB: `1946-06-14`
   - Nationality: `United States`
   - Address: `1600 Pennsylvania Ave, Washington DC`
   - Occupation: `Cryptocurrency / Virtual Assets`
   - Email: `test@example.com`
   - Amount: `$250,000`
   - Source of Wealth: `Crypto trading and cash deposits from offshore accounts`
   - Purpose: `Investment`

3. **Click "Continue to Document Upload"**

4. **Upload documents:**
   - Upload any image for ID Document (required)
   - Skip other documents to trigger missing docs penalty
   - Click "Submit for Verification"

5. **View Results:**
   - **Expected Score:** 75-85 points
   - **Risk Band:** HIGH (red)
   - **Triggered Rules:**
     - PEP Match (+40)
     - High Transaction Amount (+15)
     - High-Risk Occupation (+10)
     - Unusual Source of Wealth (+10 - keywords: crypto, cash, offshore)
     - Missing Documents (+10)
   - **Action:** REJECT

6. **Download PDF Report**
   - Click "Download PDF Report"
   - Review professional compliance report

7. **Check Admin Dashboard**
   - Go to "Admin Dashboard" in sidebar
   - See your application with HIGH risk badge
   - Filter by "High" risk band
   - Download report again from dashboard

---

## 🟢 Low-Risk Test

1. **Start New Application** (or reset)

2. **Fill the form:**
   - Name: `Jane Smith`
   - DOB: `1990-01-15`
   - Nationality: `Singapore`
   - Address: `123 Orchard Road, Singapore`
   - Occupation: `Teacher`
   - Email: `jane@example.com`
   - Amount: `$5,000`
   - Source of Wealth: `Monthly employment salary`
   - Purpose: `Savings/Deposit`

3. **Upload all 4 documents** (any images)

4. **View Results:**
   - **Expected Score:** 0 points
   - **Risk Band:** LOW (green)
   - **Action:** APPROVE

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app_v2.py` | Main Streamlit application (NEW VERSION) |
| `streamlit_app.py` | Original application (still works) |
| `risk_engine.py` | Risk calculation logic |
| `reporting/pdf_generator.py` | PDF report creation |
| `data/pep_sanctions.json` | Mock PEP and sanctions watchlists |
| `data/adverse_media.json` | Mock adverse media database |
| `data/countries.json` | Countries and high-risk industries |
| `TEST_SCENARIOS.md` | 8 detailed test scenarios |
| `README_V2.md` | Complete documentation |

---

## 🎯 Risk Scoring Quick Reference

| Score Range | Band | Action | Color |
|-------------|------|--------|-------|
| 0-24 | Low | Approve | 🟢 Green |
| 25-59 | Medium | Request EDD | 🟡 Orange |
| 60+ | High | Reject | 🔴 Red |

### Point Values

| Rule | Points |
|------|--------|
| PEP/Sanctions Match | 40 |
| High-Risk Country | 20 |
| High Amount (≥$100k) | 15 |
| Adverse Media | 15 |
| High-Risk Occupation | 10 |
| Unusual Source of Wealth | 10 |
| Missing Documents | 10 |
| Address Mismatch | 5 |

---

## 🔍 Common Issues

### "Tesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

### "Module not found: risk_engine"
```bash
# Ensure you're in the correct directory
pwd  # Should show /workspaces/KYC

# Check if file exists
ls risk_engine.py

# If missing, check git
git status
git pull
```

### "Database locked"
```bash
# Stop all Streamlit instances
pkill -f streamlit

# Delete database (will lose test data)
rm kyc.db

# Restart app - database will be recreated
streamlit run app_v2.py
```

---

## 🎨 Customization

### Change Risk Thresholds

Edit `risk_engine.py`, line ~220:

```python
# Current thresholds
if score < 25:
    band = 'Low'
elif score < 60:
    band = 'Medium'
else:
    band = 'High'

# Example: Make it stricter
if score < 20:      # Lower threshold for Low
    band = 'Low'
elif score < 50:    # Lower threshold for Medium
    band = 'Medium'
else:
    band = 'High'
```

### Add New Risk Rule

Edit `risk_engine.py`, add before line 180:

```python
# Rule 9: Suspicious Email Domain
suspicious_domains = ['tempmail.com', 'guerrillamail.com', '10minutemail.com']
email_domain = client_data.get('email', '').split('@')[-1]
if email_domain in suspicious_domains:
    score += 5
    reasons.append({
        'rule': 'Suspicious Email',
        'points': 5,
        'description': f'Email from temporary/disposable domain: {email_domain}'
    })
```

### Change App Title

Edit `app_v2.py`, line ~240:

```python
st.markdown('<h1 class="main-header">🔒 Your Company KYC Portal</h1>', unsafe_allow_html=True)
```

---

## 📊 Demo Tips for Investors

1. **Start with Dashboard**
   - Show existing applications (if any)
   - Explain risk distribution
   - Demonstrate filters

2. **Run Live Demo**
   - Use high-risk scenario (Donald Trump example)
   - Show real-time risk calculation
   - Emphasize transparency of rules

3. **Show PDF Report**
   - Professional appearance
   - Compliance-ready format
   - Detailed audit trail

4. **Explain Determinism**
   - Same input = same output
   - No black-box AI
   - Fully explainable decisions

5. **Highlight Scalability**
   - Works with real APIs (just swap mock data)
   - Can process thousands of applications
   - Easy to add new rules

---

## 🚀 Deployment

### Streamlit Cloud (Recommended)

1. Push to GitHub (already done)
2. Go to https://share.streamlit.io
3. Connect repository: `sowhat82/KYC`
4. Main file: `app_v2.py`
5. Add secret: `DILISENSE_API_KEY = "your_key"`
6. Deploy!

### Local Network

```bash
# Run on all network interfaces
streamlit run app_v2.py --server.address 0.0.0.0

# Access from other devices on same network
http://YOUR_IP:8501
```

---

## 📞 Support

- **Documentation:** See `README_V2.md`
- **Test Scenarios:** See `TEST_SCENARIOS.md`
- **System Info:** Click "About" in app sidebar
- **Issues:** Check app logs in terminal

---

**Version:** 2.0
**Status:** Production-Ready Demo
**Updated:** December 2025

Enjoy your KYC/AML demo! 🎉
