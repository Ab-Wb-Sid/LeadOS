import uuid
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

HUBSPOT_API_URL = "https://api.hubapi.com/crm/v3"

def get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }

async def find_company_by_domain(domain: str) -> Optional[Dict[str, Any]]:
    """
    Search for a company in HubSpot by domain to avoid duplicates.
    """
    if not settings.USE_LIVE_HUBSPOT:
        # Mock behavior: Simulate company not found so creation logic is triggered.
        return None

    url = f"{HUBSPOT_API_URL}/objects/companies/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "domain",
                "operator": "EQ",
                "value": domain
            }]
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("total", 0) > 0 and data.get("results"):
            return data["results"][0]
        return None

async def create_company(company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new company in HubSpot.
    """
    if not settings.USE_LIVE_HUBSPOT:
        # Mock behavior: Return a realistic mock ID to continue testing the pipeline.
        return {
            "id": f"mock-comp-{uuid.uuid4().hex[:8]}",
            "properties": {
                "name": company.get("name", "Unknown Mock Company"),
                "domain": company.get("domain", "")
            }
        }

    url = f"{HUBSPOT_API_URL}/objects/companies"
    
    properties = {
        "name": company.get("name"),
        "domain": company.get("domain"),
        "phone": company.get("phone"),
        "address": company.get("address"),
        "city": company.get("city"),
        "state": company.get("state"),
        "country": company.get("country"),
        "industry": company.get("industry"),
        "website": company.get("website")
    }
    
    # Strip out None values so HubSpot doesn't complain
    properties = {k: v for k, v in properties.items() if v is not None}
    
    payload = {"properties": properties}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        return response.json()

async def find_contact_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Search for a contact in HubSpot by email to avoid duplicates.
    """
    if not settings.USE_LIVE_HUBSPOT:
        # Mock behavior: Simulate contact not found.
        return None

    url = f"{HUBSPOT_API_URL}/objects/contacts/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("total", 0) > 0 and data.get("results"):
            return data["results"][0]
        return None

async def create_contact(contact: Dict[str, Any], hubspot_company_id: str) -> Dict[str, Any]:
    """
    Create a new contact in HubSpot and associate it with an existing company.
    """
    if not settings.USE_LIVE_HUBSPOT:
        # Mock behavior: Return a realistic mock ID.
        return {
            "id": f"mock-cont-{uuid.uuid4().hex[:8]}",
            "properties": {
                "email": contact.get("email", ""),
                "firstname": contact.get("first_name", ""),
                "lastname": contact.get("last_name", "")
            }
        }

    url = f"{HUBSPOT_API_URL}/objects/contacts"
    
    properties = {
        "email": contact.get("email"),
        "firstname": contact.get("first_name"),
        "lastname": contact.get("last_name"),
        "jobtitle": contact.get("position"),
        "linkedin": contact.get("linkedin_url")
    }
    
    # Strip out None values
    properties = {k: v for k, v in properties.items() if v is not None}
    
    # Association category and ID (1 = Contact-to-Company)
    payload = {
        "properties": properties,
        "associations": [
            {
                "to": {
                    "id": hubspot_company_id
                },
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 1 
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
