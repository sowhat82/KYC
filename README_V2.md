# KYC/AML Verification System v2.0 - Investor Demo

A comprehensive, deterministic KYC (Know Your Customer) and AML (Anti-Money Laundering) verification system with professional risk assessment and reporting capabilities.

## 🚀 Quick Start

### Run the New Version

```bash
streamlit run app_v2.py
```

### Run the Original Version

```bash
streamlit run streamlit_app.py
```

## 📋 Features

### 1. Comprehensive Client Onboarding
- **Multi-step Form**: Guided process with progress indicators
- **10+ Data Points**: Full name, DOB, nationality, address, occupation, email, amount, source of wealth, purpose
- **Smart Validation**: Real-time form validation with helpful error messages
- **High-Risk Industry Detection**: Automatically flags risky occupations

### 2. Document Management
- **4 Document Types**: ID, Selfie, Proof of Address, Source of Wealth
- **Multiple Formats**: PNG, JPG, JPEG, PDF accepted
- **OCR Processing**: Automatic text extraction from documents
- **File Validation**: Type and quality checks

### 3. Deterministic Risk Engine
- **8 Risk Rules**: Transparent, rule-based scoring
- **100-Point Scale**: Clear numerical risk assessment
- **3 Risk Bands**: Low (0-24), Medium (25-59), High (60+)
- **Detailed Explanations**: Every rule trigger is documented

### 4. Watchlist Screening
- **PEP Screening**: Politically Exposed Persons detection
- **Sanctions Lists**: Compliance with international sanctions
- **Adverse Media**: Negative news and criminal activity checks
- **Mock Data**: Demo uses simulated watchlists

### 5. Professional PDF Reports
- **Complete Documentation**: Client info, documents, risk assessment
- **Visual Risk Indicators**: Color-coded bands and scores
- **Triggered Rules Table**: Detailed breakdown of all risk factors
- **Compliance-Ready**: Professional format for audit trails

### 6. Admin Dashboard
- **Real-time Statistics**: Total applications, risk distribution
- **Advanced Filters**: Filter by risk band and status
- **Bulk Actions**: Approve, Request EDD, Reject (demo only)
- **Quick Access**: Download reports, view details

## 🎯 Risk Assessment Rules

| Rule | Points | Trigger Condition |
|------|--------|-------------------|
| PEP/Sanctions Match | 40 | Name matches watchlist |
| High-Risk Country | 20 | Jurisdiction flagged (Afghanistan, Iran, North Korea, etc.) |
| High Transaction Amount | 15 | Amount ≥ $100,000 |
| High-Risk Occupation | 10 | Casino, Crypto, Arms Trade, Money Service, etc. |
| Unusual Source of Wealth | 10 | Keywords: cash, crypto, inheritance, shell, offshore, etc. |
| Missing Documents | 10 | Required documents not uploaded |
| Adverse Media | 15 | Name in negative news database |
| Address Mismatch | 5 | OCR address differs from form input |

## 🧪 Test Scenarios

### Low-Risk Client
```
Name: Jane Smith
Nationality: Singapore
Amount: $5,000
Occupation: Teacher
Source of Wealth: Monthly salary from employment
Expected Score: 0-10 (Low Risk)
```

### High-Risk Client
```
Name: Donald Trump
Nationality: United States
Amount: $1,000,000
Occupation: Crypto Exchange
Source of Wealth: Crypto trading and cash deposits
Expected Score: 65+ (High Risk)
```

## 📂 Project Structure

```
KYC/
├── app_v2.py                    # Main Streamlit application (NEW)
├── streamlit_app.py             # Original application
├── risk_engine.py               # Risk scoring logic
├── reporting/
│   ├── __init__.py
│   └── pdf_generator.py         # PDF report generation
├── data/
│   ├── pep_sanctions.json       # Mock PEP and sanctions lists
│   ├── adverse_media.json       # Mock adverse media database
│   └── countries.json           # Countries and high-risk industries
├── uploads/                     # Uploaded documents and reports
├── requirements.txt             # Python dependencies
└── README_V2.md                 # This file
```

## 🔧 Configuration

### Environment Variables (Optional)

```bash
# For production, set API key as environment variable
export DILISENSE_API_KEY="your_api_key_here"
```

### Streamlit Config

Create `.streamlit/secrets.toml` for production:

```toml
DILISENSE_API_KEY = "your_api_key_here"
```

## 📊 Database Schema

```sql
CREATE TABLE clients (
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
);
```

## ⚠️ Important Disclaimers

**This is a demonstration system:**

1. **Mock Data**: PEP, sanctions, and adverse media lists are simulated
2. **Simplified OCR**: Document verification is basic for demo purposes
3. **No Real Compliance**: Not suitable for actual KYC/AML decisions
4. **Educational Only**: For demonstration and investor presentations

**Real KYC/AML systems must:**
- Use official watchlists (OFAC, UN, EU, FATF)
- Comply with local regulations (FinCEN, FCA, MAS, etc.)
- Include manual review by compliance officers
- Maintain comprehensive audit trails
- Follow data protection laws (GDPR, PDPA)

## 🛠️ Technology Stack

- **Streamlit** 1.41.1 - Web application framework
- **Python** 3.11+ - Backend logic
- **SQLite** - Client data storage
- **Tesseract OCR** - Document text extraction
- **ReportLab** 4.3.1 - PDF generation
- **Pillow** 11.1.0 - Image processing

## 🚢 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Set main file to `app_v2.py`
4. Add secrets in dashboard settings
5. Deploy!

### Docker (Render/Heroku)

The existing Dockerfile works with both versions:

```bash
docker build -t kyc-app .
docker run -p 8501:8501 kyc-app
```

## 📈 Future Enhancements

- [ ] Real API integration for PEP/sanctions screening
- [ ] Advanced OCR with ID document parsing
- [ ] Biometric face matching for selfie verification
- [ ] Blockchain integration for immutable audit trails
- [ ] Machine learning risk models
- [ ] Multi-language support
- [ ] REST API for programmatic access
- [ ] Real-time watchlist updates

## 📝 License

This is a demonstration project for educational and presentation purposes.

## 👥 Support

For questions or issues:
1. Check the About page in the application
2. Review this README
3. Contact your system administrator

---

**Version:** 2.0
**Last Updated:** December 2025
**Status:** Demo/Prototype
