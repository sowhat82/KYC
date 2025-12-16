"""
Risk Engine Module
Implements deterministic KYC/AML risk scoring based on predefined rules.
Each rule contributes points to a total score which determines the risk band.
"""

import json
import os
import re
from typing import Dict, List, Any


def load_json_data(filename: str) -> Dict:
    """Load JSON data from the data directory."""
    filepath = os.path.join('data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def calculate_risk(client_data: Dict[str, Any], files: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate risk score based on multiple rules and return detailed results.

    Args:
        client_data: Dictionary containing client information
            - name: Full legal name
            - dob: Date of birth
            - nationality: Country of citizenship
            - address: Residential address
            - occupation: Occupation/industry
            - email: Email address
            - amount: Transaction amount
            - source_of_wealth: Description of wealth source
            - purpose: Purpose of transaction
        files: Dictionary of uploaded files
            - id_doc: ID document file
            - selfie: Selfie photo
            - proof_address: Proof of address
            - sow_doc: Source of wealth document

    Returns:
        Dictionary containing:
            - score: Total risk score (0-100)
            - band: Risk band (Low/Medium/High)
            - reasons: List of triggered rules with details
    """

    score = 0
    reasons = []

    # Load reference data
    pep_sanctions = load_json_data('pep_sanctions.json')
    adverse_media = load_json_data('adverse_media.json')
    countries_data = load_json_data('countries.json')

    pep_list = pep_sanctions.get('pep_list', [])
    sanctions_list = pep_sanctions.get('sanctions_list', [])
    adverse_list = adverse_media.get('adverse_media_list', [])
    high_risk_countries = countries_data.get('high_risk_countries', [])
    high_risk_industries = countries_data.get('high_risk_industries', [])

    # Get client data with safe defaults
    name = client_data.get('name', '').strip()
    nationality = client_data.get('nationality', '')
    address = client_data.get('address', '')
    occupation = client_data.get('occupation', '')
    amount = client_data.get('amount', 0)
    source_of_wealth = client_data.get('source_of_wealth', '').lower()

    # Rule 1: PEP/Sanctions Match (40 points)
    # Check if client name matches any PEP or sanctions list
    name_lower = name.lower()
    all_watch_lists = pep_list + sanctions_list
    for watch_name in all_watch_lists:
        if watch_name.lower() in name_lower or name_lower in watch_name.lower():
            score += 40
            list_type = "PEP" if watch_name in pep_list else "Sanctions"
            reasons.append({
                'rule': f'{list_type} Match',
                'points': 40,
                'description': f'Client name matches {list_type} list entry: {watch_name}'
            })
            break  # Only count once

    # Rule 2: High-Risk Country (20 points)
    # Check nationality or address against high-risk countries
    for country in high_risk_countries:
        if country.lower() in nationality.lower() or country.lower() in address.lower():
            score += 20
            reasons.append({
                'rule': 'High-Risk Country',
                'points': 20,
                'description': f'Client associated with high-risk jurisdiction: {country}'
            })
            break

    # Rule 3: High Transaction Amount (15 points)
    # Flag transactions >= 100,000
    if amount >= 100000:
        score += 15
        reasons.append({
            'rule': 'High Transaction Amount',
            'points': 15,
            'description': f'Transaction amount (${amount:,.2f}) exceeds threshold of $100,000'
        })

    # Rule 4: Occupation Risk (10 points)
    # Check if occupation is in high-risk industries
    for industry in high_risk_industries:
        if industry.lower() in occupation.lower():
            score += 10
            reasons.append({
                'rule': 'High-Risk Occupation',
                'points': 10,
                'description': f'Client occupation in high-risk industry: {industry}'
            })
            break

    # Rule 5: Unusual Source of Wealth (10 points)
    # Search for red-flag keywords
    red_flag_keywords = ['cash', 'crypto', 'cryptocurrency', 'inheritance', 'shell',
                         'anonymous', 'offshore', 'bearer', 'nominee', 'loan', 'gift']
    found_keywords = []
    for keyword in red_flag_keywords:
        if keyword in source_of_wealth:
            found_keywords.append(keyword)

    if found_keywords:
        score += 10
        reasons.append({
            'rule': 'Unusual Source of Wealth',
            'points': 10,
            'description': f'Source of wealth contains red-flag terms: {", ".join(found_keywords)}'
        })

    # Rule 6: Missing or Poor Quality Documents (10 points)
    # Check if required documents are present
    required_docs = ['id_doc', 'selfie', 'proof_address', 'sow_doc']
    missing_docs = []
    for doc_key in required_docs:
        if doc_key not in files or files[doc_key] is None:
            missing_docs.append(doc_key.replace('_', ' ').title())

    if missing_docs:
        score += 10
        reasons.append({
            'rule': 'Missing Documents',
            'points': 10,
            'description': f'Required documents missing: {", ".join(missing_docs)}'
        })

    # Rule 7: Adverse Media (15 points)
    # Check if client name appears in adverse media list
    for adverse_name in adverse_list:
        if adverse_name.lower() in name_lower or name_lower in adverse_name.lower():
            score += 15
            reasons.append({
                'rule': 'Adverse Media',
                'points': 15,
                'description': f'Client name matches adverse media entry: {adverse_name}'
            })
            break

    # Rule 8: Address Mismatch (5 points)
    # This would require OCR - implemented in document processing
    # Placeholder for OCR-based address verification
    if client_data.get('address_mismatch', False):
        score += 5
        reasons.append({
            'rule': 'Address Mismatch',
            'points': 5,
            'description': 'Address on ID document differs from provided address'
        })

    # Determine risk band based on total score
    # Thresholds: <25 = Low, 25-59 = Medium, >=60 = High
    if score < 25:
        band = 'Low'
    elif score < 60:
        band = 'Medium'
    else:
        band = 'High'

    # If no rules triggered, add a clean record note
    if not reasons:
        reasons.append({
            'rule': 'Clean Screening',
            'points': 0,
            'description': 'No adverse indicators detected'
        })

    return {
        'score': score,
        'band': band,
        'reasons': reasons
    }


def get_recommended_action(risk_band: str) -> str:
    """
    Return recommended action based on risk band.

    Args:
        risk_band: Risk classification (Low/Medium/High)

    Returns:
        Recommended action string
    """
    actions = {
        'Low': 'APPROVE - Proceed with standard onboarding',
        'Medium': 'REQUEST EDD - Enhanced Due Diligence required',
        'High': 'REJECT - Decline application or escalate to compliance'
    }
    return actions.get(risk_band, 'REVIEW - Manual review required')
