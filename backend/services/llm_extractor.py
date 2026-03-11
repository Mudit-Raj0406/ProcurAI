import os
import json
import time
from dotenv import load_dotenv
from mistralai import Mistral
from pydantic import BaseModel, Field
from typing import List, Optional
from . import normalization

# Load environment variables
load_dotenv()

# Initialize Mistral client
_mistral_client = None

def get_mistral_client():
    global _mistral_client
    if _mistral_client is None:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            print("ERROR: MISTRAL_API_KEY not set in environment")
            return None
        _mistral_client = Mistral(api_key=api_key)
    return _mistral_client


def call_mistral(prompt: str, instructions: str = "") -> str:
    """Call Mistral AI using chat.complete and return the text response."""
    client = get_mistral_client()
    if not client:
        raise RuntimeError("Mistral client not initialized. Check MISTRAL_API_KEY.")

    messages = []
    if instructions:
        messages.append({"role": "system", "content": instructions})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=messages,
        temperature=0,
        max_tokens=4096,
        top_p=1,
    )

    return response.choices[0].message.content


def call_mistral_with_retry(prompt: str, instructions: str = "", max_retries: int = 3) -> str:
    """Call Mistral with automatic retry on rate limit (429) errors."""
    for attempt in range(max_retries):
        try:
            return call_mistral(prompt, instructions)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower() or "too many" in error_str.lower():
                wait_time = 15 * (2 ** attempt)  # 15s, 30s, 60s
                print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # Re-raise non-rate-limit errors immediately
    # Final attempt without catching
    return call_mistral(prompt, instructions)


def parse_json_safely(text: str) -> dict:
    """
    Safely extracts and parses JSON from a text response.
    """
    try:
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            # Find the first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end+1]
            else:
                # Fallback to removing backticks
                lines = text.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

        return json.loads(text)
    except Exception as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Raw text that failed: {text if 'text' in locals() else 'N/A'}")
        return {}


def extract_data_from_text(text: str):
    prompt = """
    You are an expert automotive procurement analyst. Extract structured data from the vendor quote text below.

    ═══════════════════════════════════════════════════════
    CRITICAL GUARDRAILS — FOLLOW EXACTLY:
    ═══════════════════════════════════════════════════════

    1. ZERO NUMERIC HALLUCINATION:
       - Only extract numbers, prices, quantities, and durations that are EXPLICITLY written in the text.
       - If TotalCost is not explicitly stated as a grand total, SUM the individual line item prices. If you cannot compute it, return null.
       - NEVER invent, estimate, round, or interpolate numeric values.
       - If a field is not explicitly stated, return null — do NOT guess.

    2. EVIDENCE-BACKED RISK FLAGS:
       - Every risk_flag MUST include a direct quote (5-20 words) copied verbatim from the document as 'evidence'.
       - If you cannot provide a direct quote, state the specific absence (e.g., "No warranty clause found in document").
       - NEVER generate a risk flag without evidence.

    3. TRICKY CLAUSE DETECTION — Actively scan for:
       - Price escalation / adjustment clauses (e.g., "prices subject to change")
       - Hidden costs: tooling fees, setup charges, shipping exclusions, taxes excluded
       - Conditional warranties that can be voided
       - Liability caps or limitation of liability clauses
       - Minimum order quantities (MOQ) that restrict flexibility
       - Cancellation or termination penalties
       - Retention of title clauses
       - Non-firm pricing / time-limited validity
       - Advance payment or upfront payment requirements beyond industry norms

    ═══════════════════════════════════════════════════════
    FIELDS TO EXTRACT:
    ═══════════════════════════════════════════════════════

    - VendorName: The legal or trade name of the vendor/supplier.
    - TotalCost: Grand total or sum. MUST be a number explicitly from the text, or null.
    - LeadTime: General lead time as stated (e.g., "4 weeks", "30 days").
    - PaymentTerms: Exact payment terms (e.g., "Net 30", "50% advance, 50% on delivery").
    - ComplianceStatus: "Yes" if all compliance standards met, "Partial" if some, "No" if explicitly non-compliant, "Unknown" if not mentioned.
    - Incoterms: Delivery terms (e.g., "FOB", "EXW", "DDP", "CIF").
    - Warranty: Exact warranty period as stated (e.g., "12 months", "2 years").
    - IATFCertified: true ONLY if IATF 16949 certification is explicitly mentioned. false otherwise.

    LINE ITEMS (extract as 'items' array):
    - part_number: Automotive part number if present.
    - item_name: Description of the part/service.
    - price: Unit price (number). MUST be from text, not computed.
    - lead_time: Item-specific lead time if different from general.
    - material_spec: Technical material specifications (e.g., "Grade A Steel", "AL 6061-T6").

    RISK FLAGS (extract as 'risk_flags' array):
    Identify ALL of the following if present:
    - Missing or inadequate warranty
    - Payment terms requiring advance/upfront payment
    - Missing certifications (IATF 16949, ISO 9001, etc.)
    - Lead times exceeding 12 weeks for standard parts
    - Price escalation or non-firm pricing clauses
    - Hidden costs (tooling, shipping, taxes excluded)
    - Conditional warranty voidance clauses
    - Liability limitations
    - Cancellation penalties
    - Any other clause that could disadvantage the buyer

    ═══════════════════════════════════════════════════════
    OUTPUT FORMAT — Return ONLY this JSON, nothing else:
    ═══════════════════════════════════════════════════════

    {{
        "VendorName": "...",
        "TotalCost": 1000.0,
        "LeadTime": "...",
        "PaymentTerms": "...",
        "ComplianceStatus": "...",
        "Incoterms": "...",
        "Warranty": "...",
        "IATFCertified": true/false,
        "items": [
            {{
                "part_number": "...",
                "item_name": "...",
                "price": 0.0,
                "lead_time": "...",
                "material_spec": "..."
            }}
        ],
        "risk_flags": [
            {{
                "risk": "Short descriptive title of the risk",
                "evidence": "Direct quote from document or specific absence description"
            }}
        ]
    }}

    If a field is missing from the text, return null. Do NOT include markdown, preamble, or explanation.

    Quote Text:
    {text}
    """.format(text=text)

    try:
        print(f"--- DEBUG: Extracting data from text (length: {len(text)}) ---")
        response_text = call_mistral_with_retry(prompt, instructions="You are an expert procurement data extraction assistant. Always return valid JSON only.")
        print(f"--- DEBUG: Mistral Response length: {len(response_text)}")
        data = parse_json_safely(response_text)
        print(f"--- DEBUG: Parsed Data: {data}")

        # Normalize Data
        if "TotalCost" in data:
            currency = data.get("Currency", "USD")
            data["TotalCost"] = normalization.normalize_currency(data["TotalCost"], currency)

        if "LeadTime" in data:
            data["lead_time_days"] = normalization.normalize_lead_time(data["LeadTime"])

        return data
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {}


def extract_rfq_requirements(text: str):
    prompt = """
    You are an automotive procurement expert. Analyze this "Request for Quotation" (RFQ) document and extract the project summary and company's MUST-HAVE requirements.
    
    Extract the following if present:
    - summary: A 1-2 sentence overview of the RFQ project goal.
    - materials_required: Preferred material grades or specifications.
    - certifications_required: Mandatory certifications (e.g., IATF 16949, ISO 9001).
    - payment_terms: Preferred payment window (e.g., Net 45).
    - incoterms: Preferred delivery terms (e.g., EXW).
    - technical_specs: Key technical parameters or part requirements.
    - warranty_requirements: Minimum warranty period.

    Return ONLY a valid and concise JSON object. Do not include any preamble or extra text.
    
    {{
        "summary": "...",
        "materials": "...",
        "certifications": ["..."],
        "payment_terms": "...",
        "incoterms": "...",
        "technical_specs": "...",
        "warranty": "..."
    }}
    
    RFQ Text:
    {text}
    """.format(text=text)

    try:
        print(f"--- DEBUG: Extracting RFQ from text (length: {len(text)}) ---")
        response_text = call_mistral_with_retry(prompt, instructions="You are an automotive procurement expert. Always return valid JSON only.")
        print(f"--- DEBUG: RFQ Raw Response length: {len(response_text)}")
        return parse_json_safely(response_text)
    except Exception as e:
        print(f"RFQ Extraction Error: {e}")
        return {}


def generate_executive_summary(bids, rfq_requirements: str = None) -> str:
    """
    Generates a comparative executive summary for a list of bids, 
    comparing them against the Master RFQ requirements if provided.
    Expects 'bids' to be a list of dicts with score info.
    """
    # Prepare context with scores
    bids_summary = []
    for bid in bids:
        score_info = f"Score: {bid.get('score', 'N/A')}/100"
        if 'score_breakdown' in bid:
            sb = bid['score_breakdown']
            score_info += f" (Price: {sb['price']['score']}, LT: {sb['lead_time']['score']}, Comp: {sb['compliance']['score']})"
            
        bids_summary.append(
            f"- Vendor: {bid.get('vendor_name')}\n"
            f"  Total Cost: ${bid.get('total_cost')}\n"
            f"  Lead Time: {bid.get('lead_time')}\n"
            f"  Compliance: {bid.get('compliance_status')}\n"
            f"  IATF Certified: {'Yes' if bid.get('is_iatf_certified') else 'No'}\n"
            f"  {score_info}"
        )

    bids_context = "\n".join(bids_summary)
    rfq_context = f"Baseline RFQ Requirements:\n{rfq_requirements}" if rfq_requirements else "No specific RFQ baseline provided."

    prompt = f"""
    You are a Senior Procurement Analyst. Review the following bids and provide a strategic Executive Summary in Markdown format.
    
    CONTEXT:
    {rfq_context}
    
    BIDS RECEIVED (Scored based on Price, Lead Time, Compliance):
    {bids_context}
    
    INSTRUCTIONS:
    Provide a professional Markdown responses with the following sections. Do NOT use code blocks.
    
    # Overview
    (1-2 sentences summarizing the bidding result and top contender)
    
    # Comparative Analysis
    (Create a Markdown table comparing Vendor, Cost, Lead Time, compliance, and Score)
    
    # Scoring Rationale
    (Explain why the top vendor won based on the weighted scoring breakdown. Mention trade-offs.)
    
    # Risk Assessment
    (Bulleted list of potential risks for the top candidates, e.g., long lead times, lack of IATF cert, compliance gaps)
    
    # Recommendation
    (Clear, decisive recommendation on which vendor to proceed with and why. If the lowest price isn't the winner, explain why.)
    """

    try:
        response_text = call_mistral_with_retry(prompt, instructions="You are a simplified, professional procurement AI. Output valid Markdown.")
        
        # Clean up code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            # Remove first line if it's a code fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a code fence
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()
            
        return response_text
    except Exception as e:
        print(f"Summary Generation Error: {e}")
        return "Failed to generate summary."
