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
    """Call Mistral AI using beta.conversations.start and return the text response."""
    client = get_mistral_client()
    if not client:
        raise RuntimeError("Mistral client not initialized. Check MISTRAL_API_KEY.")

    inputs = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    completion_args = {
        "temperature": 0,
        "max_tokens": 4096,
        "top_p": 1,
    }

    response = client.beta.conversations.start(
        inputs=inputs,
        model="mistral-large-latest",
        instructions=instructions,
        completion_args=completion_args,
        tools=[],
    )

    # Extract text from response
    # The response object has an `outputs` list; the last item contains the assistant reply
    if hasattr(response, 'outputs') and response.outputs:
        last_output = response.outputs[-1]
        if hasattr(last_output, 'text'):
            return last_output.text
        elif hasattr(last_output, 'content'):
            return last_output.content
        else:
            return str(last_output)
    elif hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    else:
        return str(response)


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
    You are an expert procurement assistant. Extract the following information from the vendor quote text provided below.
    
    Please extract the following specific fields:
    - VendorName: The name of the vendor.
    - TotalCost: The grand total or sum of the quote. return a number.
    - LeadTime: The general lead time mentioned (e.g. "4 weeks").
    - PaymentTerms: The payment terms (e.g. "Net 30").
    - ComplianceStatus: Any mention of compliance standards like IATF 16949 (Yes/No/Unknown).
    - Incoterms: Delivery terms (e.g., "FOB", "EXT").
    - Warranty: Warranty period (e.g., "12 months").
    - IATFCertified: Set to true if IATF 16949 certification is mentioned.
    
    Also extract line items as 'items'. Each item should have:
    - part_number: The automotive part number if present.
    - item_name: Description of the part.
    - price: Unit price.
    - lead_time: Specific lead time if different from general.
    - material_spec: Any technical material specifications (e.g., "Grade A Steel").
    
    Return ONLY a valid JSON object matching the following structure. Do not include any preamble, markdown code identifiers, or postscript.
    
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
        "risk_flags": ["..."]
    }}
    
    If a field is missing, return null.
    
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
