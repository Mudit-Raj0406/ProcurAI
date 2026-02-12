from typing import List, Dict, Optional

def score_bids(bids: List[dict], weights: dict) -> List[dict]:
    """
    Scores a list of bids relative to each other using Min-Max Normalization.
    
    Formula:
    - Price Score = ((MaxPrice - Price) / (MaxPrice - MinPrice)) * 100
    - Lead Time Score = ((MaxLT - LT) / (MaxLT - MinLT)) * 100
    - Compliance Score = Yes(100), Partial(50), No(0), Unknown(0)
    
    Weights default: { "price": 0.5, "lead_time": 0.3, "compliance": 0.2 }
    """
    if not bids:
        return []

    # 1. Extract Values
    # Filter out bids with 0/invalid price for min/max calc, but still score them (as 0)
    valid_prices = [b.get("total_cost", 0) or 0 for b in bids if (b.get("total_cost", 0) or 0) > 0]
    min_price = min(valid_prices) if valid_prices else 0
    max_price = max(valid_prices) if valid_prices else 0
    
    # Lead time days should be pre-calculated. If not, we try to fallback or default.
    # We assume 'lead_time_days' is present from extraction/normalization.
    valid_lts = [b.get("lead_time_days", 0) or 0 for b in bids if (b.get("lead_time_days", 0) or 0) > 0]
    min_lt = min(valid_lts) if valid_lts else 0
    max_lt = max(valid_lts) if valid_lts else 0

    scored_bids = []
    
    for bid in bids:
        score_breakdown = {}
        total_score = 0.0
        
        # --- 1. PRICE SCORING (Lower is better) ---
        price = bid.get("total_cost", 0) or 0
        w_price = weights.get("price", 0.5)
        
        if price > 0 and max_price > min_price:
            # Inverse normalization: (Max - Actual) / (Max - Min)
            # If Price == Min (Best), num = Max-Min, score = 100
            # If Price == Max (Worst), num = 0, score = 0
            norm_price = ((max_price - price) / (max_price - min_price)) * 100
        elif price > 0 and max_price == min_price:
             # All prices equal
            norm_price = 100.0
        else:
            norm_price = 0.0
            
        weighted_price = norm_price * w_price
        total_score += weighted_price
        score_breakdown["price"] = {
            "value": price,
            "normalized": round(norm_price, 1),
            "weight": w_price,
            "score": round(weighted_price, 1)
        }

        # --- 2. LEAD TIME SCORING (Lower is better) ---
        lt = bid.get("lead_time_days", 0) or 0
        w_lt = weights.get("lead_time", 0.3)
        
        if lt > 0 and max_lt > min_lt:
            norm_lt = ((max_lt - lt) / (max_lt - min_lt)) * 100
        elif lt > 0 and max_lt == min_lt:
            norm_lt = 100.0
        else:
            # If data missing, penalize
            norm_lt = 0.0
            
        weighted_lt = norm_lt * w_lt
        total_score += weighted_lt
        score_breakdown["lead_time"] = {
            "value": f"{lt} days",
            "normalized": round(norm_lt, 1),
            "weight": w_lt,
            "score": round(weighted_lt, 1)
        }

        # --- 3. COMPLIANCE SCORING (Higher is better) ---
        comp_str = (bid.get("compliance_status") or "").lower()
        w_comp = weights.get("compliance", 0.2)
        
        if "yes" in comp_str:
            norm_comp = 100.0
        elif "partial" in comp_str:
            norm_comp = 50.0
        else:
            norm_comp = 0.0
            
        # IATF Bonus (Certification) - Adding a small flat bonus (e.g. 5%) to compliance part?
        # Or keeping it strictly within 0-100? Let's keep it clean:
        # If IATF is present, ensure compliance is maxed or give bonus if not already 100
        if bid.get("is_iatf_certified") and norm_comp < 100:
             norm_comp = min(100.0, norm_comp + 20.0) # Bonus for specific cert

        weighted_comp = norm_comp * w_comp
        total_score += weighted_comp
        score_breakdown["compliance"] = {
            "value": bid.get("compliance_status", "Unknown"),
            "normalized": round(norm_comp, 1),
            "weight": w_comp,
            "score": round(weighted_comp, 1)
        }
        
        # Final Assembly
        bid["score"] = round(total_score, 1)
        bid["score_breakdown"] = score_breakdown
        scored_bids.append(bid)
        
    return scored_bids
