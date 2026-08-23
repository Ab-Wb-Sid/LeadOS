def normalize_domain(website: str) -> str:
    """
    Normalizes a website URL into a clean domain string.
    Strips protocol (http:// or https://), 'www.', and any trailing slash.
    Lowercases the result.
    
    This function is used for the `normalized_domain` UNIQUE constraint 
    on the companies table for cross-campaign deduplication.
    """
    if not website:
        return ""
        
    website = website.lower().strip()
    
    if website.startswith("http://"):
        website = website[7:]
    elif website.startswith("https://"):
        website = website[8:]
        
    if website.startswith("www."):
        website = website[4:]
        
    if website.endswith("/"):
        website = website[:-1]
        
    return website
