import re

def normalize_currency(price: float, currency: str) -> float:
    """
    Normalizes price to USD.
    Simple hardcoded rates for demo. Real app would use an API.
    """
    if not price:
        return 0.0
    
    currency = currency.strip().upper()
    rates = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.26,
        "INR": 0.012,
        "JPY": 0.0067,
        "CNY": 0.14
    }
    
    rate = rates.get(currency, 1.0) # Default to 1.0 if unknown
    return round(price * rate, 2)

def normalize_lead_time(lead_time_str: str) -> int:
    """
    Converts lead time string to number of days.
    e.g., "2 weeks" -> 14, "30 days" -> 30, "1 month" -> 30
    """
    if not lead_time_str:
        return 0
    
    text = lead_time_str.lower()
    
    # Extract number
    match = re.search(r'(\d+)', text)
    if not match:
        return 0
    
    number = int(match.group(1))
    
    if "week" in text:
        return number * 7
    elif "month" in text:
        return number * 30
    elif "year" in text:
        return number * 365
    
    # Default assume days
    return number
