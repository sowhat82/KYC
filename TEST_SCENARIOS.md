# KYC/AML System - Test Scenarios

Use these test scenarios to demonstrate the deterministic risk scoring system to investors.

## 🟢 Scenario 1: Low-Risk Client (Expected Score: 0-10)

**Profile:**
```
Full Name: Jane Smith
Date of Birth: 1985-03-15
Nationality: Singapore
Address: 123 Orchard Road, Singapore 238858
Occupation: Teacher
Email: jane.smith@email.com
Transaction Amount: $5,000
Source of Wealth: Monthly salary from employment at ABC School
Purpose: Savings/Deposit
```

**Documents:** Upload all 4 documents (any valid images)

**Expected Result:**
- Risk Score: 0 points
- Risk Band: Low
- Triggered Rules: Clean Screening (no adverse indicators)
- Recommended Action: APPROVE - Proceed with standard onboarding

---

## 🟡 Scenario 2: Medium-Risk Client (Expected Score: 25-50)

**Profile:**
```
Full Name: Ahmed Hassan
Date of Birth: 1978-11-22
Nationality: Pakistan
Address: Karachi Business District, Pakistan
Occupation: Business Owner
Email: ahmed.hassan@email.com
Transaction Amount: $75,000
Source of Wealth: Business income from textile trading company
Purpose: International Transfer
```

**Documents:** Upload only 2 documents (ID and SOW) - skip Selfie and Proof of Address

**Expected Result:**
- Risk Score: 30 points
- Risk Band: Medium
- Triggered Rules:
  - High-Risk Country (+20): Pakistan association
  - Missing Documents (+10): Selfie and Proof of Address missing
- Recommended Action: REQUEST EDD - Enhanced Due Diligence required

---

## 🟠 Scenario 3: Medium-Risk with Red Flags (Expected Score: 35-55)

**Profile:**
```
Full Name: Maria Rodriguez
Date of Birth: 1982-07-08
Nationality: Venezuela
Address: Caracas, Venezuela
Occupation: Real Estate Development
Email: maria.rodriguez@email.com
Transaction Amount: $120,000
Source of Wealth: Inheritance from family estate and property sales
Purpose: Property Purchase
```

**Documents:** Upload all 4 documents

**Expected Result:**
- Risk Score: 45 points
- Risk Band: Medium
- Triggered Rules:
  - High-Risk Country (+20): Venezuela flagged
  - High Transaction Amount (+15): $120,000 ≥ threshold
  - Unusual Source of Wealth (+10): "inheritance" keyword detected
- Recommended Action: REQUEST EDD - Enhanced Due Diligence required

---

## 🔴 Scenario 4: High-Risk Client - PEP Match (Expected Score: 60+)

**Profile:**
```
Full Name: Donald Trump
Date of Birth: 1946-06-14
Nationality: United States
Address: Mar-a-Lago, Palm Beach, FL
Occupation: Business Owner
Email: contact@example.com
Transaction Amount: $250,000
Source of Wealth: Business operations and investments
Purpose: Investment
```

**Documents:** Upload 3 documents (skip Selfie)

**Expected Result:**
- Risk Score: 65 points
- Risk Band: High
- Triggered Rules:
  - PEP Match (+40): Name matches PEP list
  - High Transaction Amount (+15): $250,000 ≥ threshold
  - Missing Documents (+10): Selfie missing
- Recommended Action: REJECT - Decline application or escalate to compliance

---

## 🔴 Scenario 5: High-Risk Client - Multiple Red Flags (Expected Score: 70+)

**Profile:**
```
Full Name: Vladimir Putin
Date of Birth: 1952-10-07
Nationality: Russia
Address: Moscow, Russian Federation
Occupation: Government Official
Email: official@example.com
Transaction Amount: $500,000
Source of Wealth: Offshore shell company investments and cash deposits
Purpose: Other
```

**Documents:** Upload only ID document

**Expected Result:**
- Risk Score: 95 points
- Risk Band: High
- Triggered Rules:
  - PEP Match (+40): Name on PEP watchlist
  - High-Risk Country (+20): Russia flagged
  - High Transaction Amount (+15): $500,000 ≥ threshold
  - Unusual Source of Wealth (+10): "offshore", "shell", "cash" keywords
  - Missing Documents (+10): 3 documents missing
- Recommended Action: REJECT - Decline application or escalate to compliance

---

## 🔴 Scenario 6: High-Risk - Adverse Media (Expected Score: 60+)

**Profile:**
```
Full Name: Sam Bankman-Fried
Date of Birth: 1992-03-06
Nationality: United States
Address: Nassau, Bahamas
Occupation: Cryptocurrency / Virtual Assets
Email: sbf@example.com
Transaction Amount: $1,000,000
Source of Wealth: Crypto trading profits and token sales
Purpose: Business Operations
```

**Documents:** Upload all 4 documents

**Expected Result:**
- Risk Score: 80 points
- Risk Band: High
- Triggered Rules:
  - PEP Match (+40): If in PEP list
  - Adverse Media (+15): Name in negative news database
  - High Transaction Amount (+15): $1,000,000 ≥ threshold
  - High-Risk Occupation (+10): Crypto industry flagged
  - Unusual Source of Wealth (+10): "crypto" keyword
- Recommended Action: REJECT - Decline application or escalate to compliance

---

## 🟢 Scenario 7: Low-Risk - Complete Documentation (Expected Score: 0)

**Profile:**
```
Full Name: Emily Chen
Date of Birth: 1990-05-20
Nationality: Canada
Address: 456 Bay Street, Toronto, ON M5H 2Y2
Occupation: Accountant
Email: emily.chen@email.com
Transaction Amount: $15,000
Source of Wealth: Employment income from KPMG
Purpose: Investment
```

**Documents:** Upload all 4 high-quality documents

**Expected Result:**
- Risk Score: 0 points
- Risk Band: Low
- Triggered Rules: Clean Screening
- Recommended Action: APPROVE - Proceed with standard onboarding

---

## 🔴 Scenario 8: High-Risk - Sanctions List (Expected Score: 60+)

**Profile:**
```
Full Name: Igor Sechin
Date of Birth: 1960-09-07
Nationality: Russia
Address: Moscow, Russian Federation
Occupation: Banking
Email: igor@example.com
Transaction Amount: $200,000
Source of Wealth: Executive compensation
Purpose: International Transfer
```

**Documents:** Upload 2 documents (ID and POA)

**Expected Result:**
- Risk Score: 85 points
- Risk Band: High
- Triggered Rules:
  - Sanctions Match (+40): Name on sanctions list
  - High-Risk Country (+20): Russia flagged
  - High Transaction Amount (+15): $200,000 ≥ threshold
  - Missing Documents (+10): 2 documents missing
- Recommended Action: REJECT - Decline application or escalate to compliance

---

## 📊 Testing Checklist

Use this checklist when demonstrating the system:

- [ ] Test a clean/low-risk profile (Scenario 1)
- [ ] Test a medium-risk profile (Scenario 2 or 3)
- [ ] Test a high-risk PEP match (Scenario 4)
- [ ] Test with missing documents to show +10 penalty
- [ ] Test high transaction amounts (≥$100k) to trigger +15
- [ ] Show PDF report generation for each risk band
- [ ] Demonstrate admin dashboard filters
- [ ] Test "Approve", "Request EDD", "Reject" actions
- [ ] Verify risk scores are deterministic (same input = same output)
- [ ] Show the "Triggered Rules" expander with explanations

---

## 🎯 Demo Flow Recommendation

**For Investor Presentations:**

1. **Start with Low-Risk** (Scenario 1)
   - Show how clean clients are quickly approved
   - Demonstrate PDF report with green risk band

2. **Show Medium-Risk** (Scenario 3)
   - Explain EDD process
   - Show how multiple small flags add up

3. **Demonstrate High-Risk** (Scenario 4 or 5)
   - Show PEP screening in action
   - Explain automatic rejection for high scores
   - Show detailed risk breakdown

4. **Navigate to Admin Dashboard**
   - Show all 3 applications side-by-side
   - Demonstrate risk band filtering
   - Download PDF reports

5. **Explain Deterministic Nature**
   - Same inputs always produce same score
   - Transparent rule-based system
   - Audit trail in PDF reports

---

## ⚠️ Important Notes

1. **Mock Data**: All PEP, sanctions, and adverse media lists are simulated
2. **Document Quality**: For demo, any image/PDF will work for upload
3. **OCR**: Document text extraction is basic; address mismatch rule may not trigger
4. **Reproducibility**: Run same scenario multiple times to show consistency
5. **PDF Downloads**: Reports are saved in `/uploads` directory

---

**Last Updated:** December 2025
**System Version:** 2.0
