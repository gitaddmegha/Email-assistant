from typing import Dict

def prioritize_email(email_data: Dict) -> str:
    """
    Assign priority to an email based on basic rules.
    
    Args:
        email_data: Dictionary containing email fields like subject, sender, etc.
    
    Returns:
        Priority level: 'high', 'medium', or 'low'
    """
    subject = email_data.get("subject", "").lower()
    sender = email_data.get("sender_email", "").lower()


    if any(keyword in subject for keyword in ["urgent", "asap", "immediately"]):
        return "high"
    if sender.endswith("@importantclient.com"):
        return "high"
    if "newsletter" in subject or "unsubscribe" in email_data.get("body_text", "").lower():
        return "low"
    
    return "medium"
