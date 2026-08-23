def score_company(company) -> int:
    """
    Calculates a lead score for a given company.
    
    This is a pure function isolated from ingestion logic to allow for
    easy tuning later (as per Architecture Doc Section 7).
    
    Formula Weights (Max 100 points):
    - Google Rating: rating * 10 (Max 50 points for 5.0)
    - Review Count: 1 point per 10 reviews (Max 30 points for >= 300 reviews)
    - Verified Contacts: +20 points if at least one contact is verified
    
    Args:
        company: A company object or ORM model containing scoring fields.
        
    Returns:
        int: The calculated lead score (0-100).
    """
    if not company:
        return 0
        
    score = 0
    
    # 1. Google Rating (Max 50 points)
    if getattr(company, "google_rating", None) is not None:
        try:
            rating = float(company.google_rating)
            score += int(rating * 10)
        except (ValueError, TypeError):
            pass
            
    # 2. Review Count (Max 30 points)
    if getattr(company, "review_count", None) is not None:
        try:
            reviews = int(company.review_count)
            # 1 point per 10 reviews, capped at 30 points
            review_points = min(30, reviews // 10)
            score += review_points
        except (ValueError, TypeError):
            pass
            
    # 3. Verified Contact Exists (Max 20 points)
    contacts = getattr(company, "contacts", [])
    if contacts:
        for contact in contacts:
            status = getattr(contact, "verification_status", "")
            if status and status.lower() == "verified":
                score += 20
                break
                
    return score
