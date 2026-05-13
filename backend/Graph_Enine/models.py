"""
Entity normalization layer to standardize Module 2 output
"""

def normalize_entities(raw_entities):
    """
    Normalize Module 2 output entities to a standardized format
    
    Args:
        raw_entities: Dict with keys like "wallets", "emails", "phones", "urls", "names"
    
    Returns:
        List of dicts with "type" and "value" keys
    """
    mapping = {
        "wallets": "Wallet",
        "emails": "Email",
        "phones": "Phone",
        "urls": "URL",
        "names": "Person"
    }

    normalized = []

    for key, values in raw_entities.items():
        label = mapping.get(key, None)
        if not label:
            continue

        # Handle None or empty values
        if not values:
            continue

        for v in values:
            if v:  # Skip empty values
                normalized.append({
                    "type": label,
                    "value": str(v).strip()
                })

    return normalized
