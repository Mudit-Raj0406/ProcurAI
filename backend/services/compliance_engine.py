"""
Compliance Engine — Deterministic, evidence-based compliance/risk flag rules.

This module runs AFTER LLM extraction to compare extracted bid data against
the Master RFQ requirements. Every flag is programmatic (no hallucination possible)
and includes structured evidence citing both the RFQ requirement and the bid value.

Risk Categories:
    CERTIFICATION  — Missing mandatory certs (IATF 16949, ISO 9001, etc.)
    PAYMENT        — Payment term deviations from RFQ baseline
    WARRANTY       — Warranty period shorter than RFQ minimum
    LEAD_TIME      — Lead time exceeds RFQ expected window
    INCOTERMS      — Delivery terms mismatch
    CLAUSE         — Tricky/hidden contractual clauses detected by LLM
    NUMERIC        — Suspicious numeric values that may be hallucinated
    COMPLIANCE     — General compliance status issues

Severity Levels:
    critical  — Mandatory requirement violated; bid may be disqualified
    high      — Significant deviation that requires management attention
    medium    — Notable deviation; acceptable with negotiation
    low       — Minor observation; informational
"""

import re
import json
from typing import List, Dict, Any, Optional


def build_compliance_report(
    bid_data: dict,
    rfq_requirements: dict,
    llm_risk_flags: List[dict],
    bid_raw_text: str = "",
) -> List[dict]:
    """
    Master function: runs all compliance rules and returns a unified,
    deduplicated list of structured risk flags.

    Each flag is:
    {
        "risk": "Human-readable title",
        "category": "CERTIFICATION|PAYMENT|WARRANTY|LEAD_TIME|INCOTERMS|CLAUSE|NUMERIC|COMPLIANCE",
        "severity": "critical|high|medium|low",
        "evidence": "Specific comparison: RFQ requires X, bid offers Y",
        "source": "programmatic|llm|hybrid"
    }
    """
    flags: List[dict] = []

    # --- 1. Certification checks ---
    flags.extend(_check_certifications(bid_data, rfq_requirements))

    # --- 2. Payment term checks ---
    flags.extend(_check_payment_terms(bid_data, rfq_requirements))

    # --- 3. Warranty checks ---
    flags.extend(_check_warranty(bid_data, rfq_requirements))

    # --- 4. Lead time checks ---
    flags.extend(_check_lead_time(bid_data, rfq_requirements))

    # --- 5. Incoterms mismatch ---
    flags.extend(_check_incoterms(bid_data, rfq_requirements))

    # --- 6. Compliance status ---
    flags.extend(_check_compliance_status(bid_data))

    # --- 7. Numeric sanity checks (anti-hallucination) ---
    flags.extend(_check_numeric_sanity(bid_data, bid_raw_text))

    # --- 8. Tricky clause detection from raw text ---
    flags.extend(_check_tricky_clauses(bid_raw_text))

    # --- 9. Merge LLM flags (promote with structure) ---
    flags.extend(_promote_llm_flags(llm_risk_flags, flags))

    # Deduplicate by (category, risk) key
    seen = set()
    unique_flags = []
    for f in flags:
        key = (f.get("category", ""), f.get("risk", "").lower())
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    # Sort: critical first, then high, medium, low
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unique_flags.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 4))

    return unique_flags


# =============================================================================
# CERTIFICATION RULES
# =============================================================================

# Common automotive/industrial certifications to check
KNOWN_CERTIFICATIONS = [
    "IATF 16949", "IATF16949",
    "ISO 9001", "ISO9001",
    "ISO 14001", "ISO14001",
    "ISO 45001", "ISO45001",
    "AS9100",
    "NADCAP",
    "TS 16949", "TS16949",
    "ISO 13485", "ISO13485",
]


def _check_certifications(bid_data: dict, rfq_reqs: dict) -> List[dict]:
    flags = []
    required_certs = rfq_reqs.get("certifications", [])
    if not isinstance(required_certs, list):
        required_certs = [str(required_certs)] if required_certs else []

    if not required_certs:
        return flags

    # Normalize required certs for matching
    for cert in required_certs:
        cert_upper = str(cert).upper().strip()

        # Check IATF specifically (has a dedicated boolean field)
        if "IATF" in cert_upper:
            if not bid_data.get("is_iatf_certified", False):
                flags.append({
                    "risk": f"Missing Mandatory Certification: {cert}",
                    "category": "CERTIFICATION",
                    "severity": "critical",
                    "evidence": f"RFQ requires '{cert}', but vendor bid does not confirm this certification.",
                    "source": "programmatic",
                })
            continue

        # For other certs, check compliance_status and raw text indicators
        compliance_str = str(bid_data.get("compliance_status", "")).upper()
        vendor_text_indicators = " ".join([
            str(bid_data.get("compliance_status", "")),
            str(bid_data.get("warranty_terms", "")),
            str(bid_data.get("vendor_name", "")),
        ]).upper()

        # Normalize cert name for flexible matching (e.g., "ISO 9001" matches "ISO9001")
        cert_normalized = cert_upper.replace(" ", "")
        text_normalized = vendor_text_indicators.replace(" ", "")

        if cert_normalized not in text_normalized and "YES" not in compliance_str:
            flags.append({
                "risk": f"Unconfirmed Certification: {cert}",
                "category": "CERTIFICATION",
                "severity": "high",
                "evidence": f"RFQ requires '{cert}', but vendor bid does not explicitly mention this certification.",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# PAYMENT TERMS RULES
# =============================================================================

# Risk classification for payment terms
PAYMENT_RISK_MAP = {
    # Favorable to buyer (low risk)
    "net 90": 0, "net 60": 0, "net 45": 0,
    # Standard
    "net 30": 1,
    # Slightly unfavorable
    "net 15": 2, "net 10": 2,
    # High risk to buyer
    "due on receipt": 3, "cod": 3, "cash on delivery": 3,
    "advance": 4, "upfront": 4, "100% advance": 4,
    "prepaid": 4, "proforma": 3, "50% advance": 3,
}


def _extract_payment_risk_level(terms: str) -> int:
    """Returns 0 (safest) to 4 (riskiest) for a payment terms string."""
    if not terms:
        return -1  # Unknown
    terms_lower = terms.lower().strip()

    # Direct match
    for key, level in PAYMENT_RISK_MAP.items():
        if key in terms_lower:
            return level

    # Try to extract "net X" pattern
    net_match = re.search(r'net\s*(\d+)', terms_lower)
    if net_match:
        days = int(net_match.group(1))
        if days >= 45:
            return 0
        elif days >= 30:
            return 1
        elif days >= 15:
            return 2
        else:
            return 3

    return -1  # Unknown


def _check_payment_terms(bid_data: dict, rfq_reqs: dict) -> List[dict]:
    flags = []
    rfq_payment = rfq_reqs.get("payment_terms", "")
    bid_payment = bid_data.get("payment_terms", "")

    if not rfq_payment or not bid_payment:
        return flags

    rfq_risk = _extract_payment_risk_level(str(rfq_payment))
    bid_risk = _extract_payment_risk_level(str(bid_payment))

    if rfq_risk == -1 or bid_risk == -1:
        return flags

    deviation = bid_risk - rfq_risk

    if deviation >= 3:
        flags.append({
            "risk": "Critical Payment Term Deviation",
            "category": "PAYMENT",
            "severity": "critical",
            "evidence": f"RFQ specifies '{rfq_payment}', but vendor requires '{bid_payment}'. "
                        f"This represents a significant cash flow risk (advance/upfront payment vs. net terms).",
            "source": "programmatic",
        })
    elif deviation >= 2:
        flags.append({
            "risk": "Unfavorable Payment Terms",
            "category": "PAYMENT",
            "severity": "high",
            "evidence": f"RFQ specifies '{rfq_payment}', but vendor requires '{bid_payment}'. "
                        f"Shorter payment window increases working capital pressure.",
            "source": "programmatic",
        })
    elif deviation >= 1:
        flags.append({
            "risk": "Payment Terms Differ from RFQ Baseline",
            "category": "PAYMENT",
            "severity": "medium",
            "evidence": f"RFQ specifies '{rfq_payment}', vendor offers '{bid_payment}'.",
            "source": "programmatic",
        })

    # Check for upfront/advance keywords regardless of RFQ
    bid_lower = str(bid_payment).lower()
    if any(kw in bid_lower for kw in ["advance", "upfront", "100%", "prepaid"]):
        if not any(f["category"] == "PAYMENT" and f["severity"] == "critical" for f in flags):
            flags.append({
                "risk": "Advance Payment Required",
                "category": "PAYMENT",
                "severity": "high",
                "evidence": f"Vendor payment terms '{bid_payment}' include advance/upfront payment, "
                            f"which increases financial exposure before delivery.",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# WARRANTY RULES
# =============================================================================

def _extract_months(text: str) -> Optional[int]:
    """Extracts warranty duration in months from a text string."""
    if not text:
        return None
    text_lower = text.lower().strip()

    # "24 months", "12-month", "12months"
    month_match = re.search(r'(\d+)\s*[-]?\s*month', text_lower)
    if month_match:
        return int(month_match.group(1))

    # "2 years", "1-year", "2year"
    year_match = re.search(r'(\d+)\s*[-]?\s*year', text_lower)
    if year_match:
        return int(year_match.group(1)) * 12

    # "1 yr"
    yr_match = re.search(r'(\d+)\s*yr', text_lower)
    if yr_match:
        return int(yr_match.group(1)) * 12

    # Just a number (assume months)
    num_match = re.search(r'^(\d+)$', text_lower.strip())
    if num_match:
        return int(num_match.group(1))

    return None


def _check_warranty(bid_data: dict, rfq_reqs: dict) -> List[dict]:
    flags = []
    rfq_warranty = rfq_reqs.get("warranty", "")
    bid_warranty = bid_data.get("warranty_terms", "") or bid_data.get("Warranty", "")

    # Check for missing warranty
    if not bid_warranty or bid_warranty.lower() in ("n/a", "none", "not specified", "null", "-"):
        if rfq_warranty:
            flags.append({
                "risk": "No Warranty Specified",
                "category": "WARRANTY",
                "severity": "critical",
                "evidence": f"RFQ requires warranty of '{rfq_warranty}', but vendor bid does not specify any warranty terms.",
                "source": "programmatic",
            })
        else:
            flags.append({
                "risk": "No Warranty Specified",
                "category": "WARRANTY",
                "severity": "medium",
                "evidence": "Vendor bid does not specify any warranty terms.",
                "source": "programmatic",
            })
        return flags

    if not rfq_warranty:
        return flags

    rfq_months = _extract_months(str(rfq_warranty))
    bid_months = _extract_months(str(bid_warranty))

    if rfq_months is None or bid_months is None:
        return flags

    if bid_months < rfq_months:
        shortfall = rfq_months - bid_months
        severity = "critical" if shortfall >= 12 else "high" if shortfall >= 6 else "medium"
        flags.append({
            "risk": "Warranty Period Below RFQ Requirement",
            "category": "WARRANTY",
            "severity": severity,
            "evidence": f"RFQ requires minimum '{rfq_warranty}' ({rfq_months} months), "
                        f"but vendor offers only '{bid_warranty}' ({bid_months} months). "
                        f"Shortfall: {shortfall} months.",
            "source": "programmatic",
        })

    return flags


# =============================================================================
# LEAD TIME RULES
# =============================================================================

def _extract_days(text: str) -> Optional[int]:
    """Extracts duration in days from a lead time string."""
    if not text:
        return None
    text_lower = text.lower().strip()

    match = re.search(r'(\d+)', text_lower)
    if not match:
        return None

    number = int(match.group(1))

    if "week" in text_lower:
        return number * 7
    elif "month" in text_lower:
        return number * 30
    elif "year" in text_lower:
        return number * 365
    else:
        return number  # Assume days


def _check_lead_time(bid_data: dict, rfq_reqs: dict) -> List[dict]:
    flags = []
    # RFQ may not always have a lead time requirement; skip if absent
    rfq_lead_time = rfq_reqs.get("lead_time", "") or rfq_reqs.get("delivery_timeline", "")
    bid_lead_time = bid_data.get("lead_time", "") or bid_data.get("LeadTime", "")

    if not bid_lead_time or str(bid_lead_time).lower() in ("n/a", "none", "-"):
        return flags

    bid_days = _extract_days(str(bid_lead_time))

    # Check against RFQ requirement if available
    if rfq_lead_time:
        rfq_days = _extract_days(str(rfq_lead_time))
        if rfq_days and bid_days and bid_days > rfq_days:
            overshoot_pct = ((bid_days - rfq_days) / rfq_days) * 100
            severity = "critical" if overshoot_pct > 100 else "high" if overshoot_pct > 50 else "medium"
            flags.append({
                "risk": "Lead Time Exceeds RFQ Requirement",
                "category": "LEAD_TIME",
                "severity": severity,
                "evidence": f"RFQ expects delivery within '{rfq_lead_time}' (~{rfq_days} days), "
                            f"but vendor quotes '{bid_lead_time}' (~{bid_days} days). "
                            f"Exceeds by {overshoot_pct:.0f}%.",
                "source": "programmatic",
            })

    # Absolute sanity: flag extremely long lead times (>180 days)
    if bid_days and bid_days > 180:
        if not any(f["category"] == "LEAD_TIME" for f in flags):
            flags.append({
                "risk": "Unusually Long Lead Time",
                "category": "LEAD_TIME",
                "severity": "high",
                "evidence": f"Vendor quotes lead time of '{bid_lead_time}' (~{bid_days} days), "
                            f"which exceeds 6 months and may indicate supply chain risk.",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# INCOTERMS RULES
# =============================================================================

# Incoterms risk/cost transfer from buyer perspective
# Higher = more cost/risk borne by seller (better for buyer)
INCOTERMS_BUYER_FAVORABILITY = {
    "exw": 0,   # Buyer bears all risk & cost from seller's premises
    "fca": 1,
    "fas": 2,
    "fob": 3,
    "cfr": 4, "c&f": 4,
    "cif": 5,
    "cpt": 4,
    "cip": 5,
    "dap": 6,
    "dpu": 7,
    "ddp": 8,   # Seller bears all risk & cost to buyer's door
}


def _check_incoterms(bid_data: dict, rfq_reqs: dict) -> List[dict]:
    flags = []
    rfq_incoterms = str(rfq_reqs.get("incoterms", "")).strip().upper()
    bid_incoterms = str(bid_data.get("incoterms", "")).strip().upper()

    if not rfq_incoterms or not bid_incoterms:
        return flags
    if rfq_incoterms.lower() in ("n/a", "none", "-", ""):
        return flags
    if bid_incoterms.lower() in ("n/a", "none", "-", ""):
        return flags

    rfq_score = INCOTERMS_BUYER_FAVORABILITY.get(rfq_incoterms.lower())
    bid_score = INCOTERMS_BUYER_FAVORABILITY.get(bid_incoterms.lower())

    if rfq_score is None or bid_score is None:
        return flags

    if rfq_incoterms != bid_incoterms:
        if bid_score < rfq_score:
            # Vendor shifts MORE cost/risk to buyer than RFQ wanted
            flags.append({
                "risk": "Incoterms Less Favorable Than RFQ",
                "category": "INCOTERMS",
                "severity": "high" if (rfq_score - bid_score) >= 3 else "medium",
                "evidence": f"RFQ specifies '{rfq_incoterms}', but vendor offers '{bid_incoterms}'. "
                            f"This shifts more logistics cost and risk to the buyer.",
                "source": "programmatic",
            })
        else:
            # Vendor offers MORE favorable terms than required (informational)
            flags.append({
                "risk": "Incoterms Differ from RFQ (More Favorable)",
                "category": "INCOTERMS",
                "severity": "low",
                "evidence": f"RFQ specifies '{rfq_incoterms}', vendor offers '{bid_incoterms}' "
                            f"which is actually more favorable to the buyer.",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# COMPLIANCE STATUS
# =============================================================================

def _check_compliance_status(bid_data: dict) -> List[dict]:
    flags = []
    status = str(bid_data.get("compliance_status", "")).lower().strip()

    if status in ("no", "non-compliant", "false"):
        flags.append({
            "risk": "Vendor Declared Non-Compliant",
            "category": "COMPLIANCE",
            "severity": "critical",
            "evidence": f"Vendor's compliance status is explicitly '{bid_data.get('compliance_status')}'. "
                        f"This bid may not meet minimum regulatory or quality requirements.",
            "source": "programmatic",
        })
    elif status in ("partial", "conditional"):
        flags.append({
            "risk": "Partial Compliance Only",
            "category": "COMPLIANCE",
            "severity": "high",
            "evidence": f"Vendor compliance status is '{bid_data.get('compliance_status')}'. "
                        f"Conditional compliance may require additional negotiation or verification.",
            "source": "programmatic",
        })
    elif status in ("unknown", "", "n/a"):
        flags.append({
            "risk": "Compliance Status Unknown",
            "category": "COMPLIANCE",
            "severity": "medium",
            "evidence": "Vendor bid does not clearly state compliance status. Manual verification recommended.",
            "source": "programmatic",
        })

    return flags


# =============================================================================
# NUMERIC HALLUCINATION CHECKS
# =============================================================================

def _check_numeric_sanity(bid_data: dict, raw_text: str) -> List[dict]:
    """
    Validates that key numeric values extracted by LLM actually appear
    in the raw document text. Flags suspicious values that may be hallucinated.
    """
    flags = []
    if not raw_text:
        return flags

    # Clean raw text for number searching
    raw_clean = raw_text.replace(",", "").replace("$", "").replace("€", "").replace("£", "")

    # Check total cost
    total_cost = bid_data.get("total_cost")
    if total_cost and total_cost > 0:
        cost_str = f"{total_cost:.0f}" if total_cost == int(total_cost) else f"{total_cost:.2f}"
        # Also check without decimals
        cost_int_str = str(int(total_cost))

        # Look for the number in raw text (with some flexibility)
        found = (cost_str in raw_clean) or (cost_int_str in raw_clean)

        # Also try the original formatted form (e.g., "5,000" or "$5000")
        if not found:
            # Try with comma formatting
            formatted = f"{total_cost:,.0f}".replace(",", "")
            found = formatted in raw_clean

        if not found and total_cost > 100:
            # Only flag if > $100 to avoid false positives on small numbers
            flags.append({
                "risk": "Extracted Total Cost Not Found in Source Document",
                "category": "NUMERIC",
                "severity": "high",
                "evidence": f"The extracted total cost (${total_cost:,.2f}) could not be located in "
                            f"the original document text. This value may be incorrectly calculated or hallucinated. "
                            f"Manual verification strongly recommended.",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# TRICKY CLAUSE DETECTION (Pattern-based)
# =============================================================================

# Patterns that indicate potentially tricky contractual clauses
TRICKY_CLAUSE_PATTERNS = [
    {
        "pattern": r"(?:subject\s+to|conditional\s+(?:upon|on))\s+(?:price\s+)?(?:adjustment|change|revision|escalation)",
        "risk": "Price Adjustment/Escalation Clause Detected",
        "severity": "high",
        "description": "Vendor reserves the right to adjust pricing, making the quoted total non-binding.",
    },
    {
        "pattern": r"(?:price|cost)s?\s+(?:are\s+)?(?:subject\s+to\s+change|may\s+(?:vary|change|increase)|not\s+(?:guaranteed|fixed|firm))",
        "risk": "Non-Firm Pricing",
        "severity": "high",
        "description": "Prices quoted are explicitly stated as non-firm or subject to change.",
    },
    {
        "pattern": r"(?:tooling|mold|die|setup)\s+(?:cost|charge|fee)s?\s+(?:(?:are\s+)?additional|not\s+included|extra|separate)",
        "risk": "Hidden Tooling/Setup Costs",
        "severity": "high",
        "description": "Tooling, mold, die, or setup costs are excluded from the quoted total and will be charged separately.",
    },
    {
        "pattern": r"(?:shipping|freight|transport(?:ation)?|delivery)\s+(?:cost|charge|fee)s?\s+(?:(?:are\s+)?(?:additional|not\s+included|extra|separate)|excluded)",
        "risk": "Shipping/Freight Costs Excluded",
        "severity": "medium",
        "description": "Shipping or freight charges are excluded from the quoted total.",
    },
    {
        "pattern": r"(?:penalty|penalt(?:ies)|liquidated\s+damages?)\s+(?:for|of|clause)",
        "risk": "Penalty/Liquidated Damages Clause",
        "severity": "medium",
        "description": "Contract includes penalty or liquidated damages provisions.",
    },
    {
        "pattern": r"(?:cancellation|termination)\s+(?:fee|charge|penalty|cost)",
        "risk": "Cancellation/Termination Fees",
        "severity": "medium",
        "description": "Vendor charges fees for order cancellation or early termination.",
    },
    {
        "pattern": r"(?:minimum\s+order|moq|minimum\s+quantity)\s+(?:of\s+)?\d+",
        "risk": "Minimum Order Quantity Requirement",
        "severity": "low",
        "description": "Vendor imposes a minimum order quantity that may affect flexibility.",
    },
    {
        "pattern": r"(?:force\s+majeure|act\s+of\s+god|unforeseeable\s+circumstances)",
        "risk": "Broad Force Majeure Clause",
        "severity": "low",
        "description": "Contract includes force majeure provisions that may limit vendor liability.",
    },
    {
        "pattern": r"(?:warranty|guarantee)\s+(?:void|invalid|null)\s+(?:if|when|upon)",
        "risk": "Conditional Warranty Voidance",
        "severity": "high",
        "description": "Warranty can be voided under certain conditions — review terms carefully.",
    },
    {
        "pattern": r"(?:liability|damages?)\s+(?:limited\s+to|shall\s+not\s+exceed|capped\s+at)\s+(?:the\s+)?(?:purchase\s+price|order\s+value|invoice)",
        "risk": "Liability Cap at Purchase Price",
        "severity": "medium",
        "description": "Vendor limits total liability to the purchase price, which may be insufficient for consequential damages.",
    },
    {
        "pattern": r"(?:exclud(?:es?|ing)|(?:does\s+)?not\s+(?:include|cover))\s+(?:tax(?:es)?|duties|customs|vat|gst|import)",
        "risk": "Taxes/Duties Excluded from Quote",
        "severity": "medium",
        "description": "Quoted price excludes taxes, duties, or customs — actual cost will be higher.",
    },
    {
        "pattern": r"(?:price|rate)s?\s+(?:valid|effective)\s+(?:until|through|for)\s+(?:only\s+)?\d+\s+(?:days?|weeks?|months?)",
        "risk": "Time-Limited Price Validity",
        "severity": "low",
        "description": "Quoted prices have a limited validity window.",
    },
    {
        "pattern": r"(?:retention\s+of\s+title|title\s+remains?\s+with\s+(?:the\s+)?(?:seller|vendor|supplier))",
        "risk": "Retention of Title Clause",
        "severity": "medium",
        "description": "Vendor retains ownership of goods until full payment is received.",
    },
]


def _check_tricky_clauses(raw_text: str) -> List[dict]:
    """Scans raw bid text for tricky contractual clauses using regex patterns."""
    flags = []
    if not raw_text:
        return flags

    text_lower = raw_text.lower()

    for clause in TRICKY_CLAUSE_PATTERNS:
        matches = list(re.finditer(clause["pattern"], text_lower, re.IGNORECASE))
        if matches:
            # Extract the actual matched text as evidence (first match, with context)
            match = matches[0]
            start = max(0, match.start() - 40)
            end = min(len(raw_text), match.end() + 40)
            context = raw_text[start:end].strip().replace("\n", " ")

            flags.append({
                "risk": clause["risk"],
                "category": "CLAUSE",
                "severity": clause["severity"],
                "evidence": f"{clause['description']} Found in document: \"...{context}...\"",
                "source": "programmatic",
            })

    return flags


# =============================================================================
# LLM FLAG PROMOTION
# =============================================================================

def _promote_llm_flags(llm_flags: List[dict], existing_flags: List[dict]) -> List[dict]:
    """
    Takes raw LLM risk flags and promotes them to structured format.
    Skips any that duplicate existing programmatic flags.
    """
    promoted = []

    # Build a set of existing risk titles (lowercase) to check for dupes
    existing_risks = {f.get("risk", "").lower() for f in existing_flags}

    for flag in llm_flags:
        if not isinstance(flag, dict):
            continue

        risk_text = flag.get("risk", "")
        evidence = flag.get("evidence", "")

        if not risk_text:
            continue

        # Skip if already covered by programmatic checks
        risk_lower = risk_text.lower()
        if any(existing in risk_lower or risk_lower in existing for existing in existing_risks):
            continue

        # Infer category from risk text
        category = _infer_category(risk_text)

        # Infer severity from keywords
        severity = _infer_severity(risk_text, evidence)

        # Validate evidence exists (guardrail)
        if not evidence or evidence.strip() == "":
            evidence = "Identified during AI analysis — no specific document quote available. Manual verification recommended."

        promoted.append({
            "risk": risk_text,
            "category": category,
            "severity": severity,
            "evidence": evidence,
            "source": "llm",
        })

    return promoted


def _infer_category(risk_text: str) -> str:
    """Infers a category from the risk description text."""
    text = risk_text.lower()
    if any(kw in text for kw in ["certif", "iatf", "iso ", "compliance"]):
        return "CERTIFICATION"
    elif any(kw in text for kw in ["payment", "advance", "upfront", "net "]):
        return "PAYMENT"
    elif any(kw in text for kw in ["warranty", "guarantee"]):
        return "WARRANTY"
    elif any(kw in text for kw in ["lead time", "delivery", "timeline", "delay"]):
        return "LEAD_TIME"
    elif any(kw in text for kw in ["incoterm", "fob", "exw", "ddp", "cif"]):
        return "INCOTERMS"
    elif any(kw in text for kw in ["price", "cost", "fee", "charge", "tooling", "hidden"]):
        return "CLAUSE"
    else:
        return "COMPLIANCE"


def _infer_severity(risk_text: str, evidence: str) -> str:
    """Infers severity from risk text keywords."""
    combined = (risk_text + " " + evidence).lower()
    if any(kw in combined for kw in ["missing mandatory", "non-compliant", "critical", "no warranty", "void"]):
        return "critical"
    elif any(kw in combined for kw in ["missing", "deviation", "exceed", "unfavorable", "hidden", "upfront", "advance"]):
        return "high"
    elif any(kw in combined for kw in ["partial", "differ", "unknown", "conditional"]):
        return "medium"
    else:
        return "medium"
