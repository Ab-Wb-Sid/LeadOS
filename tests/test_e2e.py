import urllib.request
import json
import time

def login():
    req = urllib.request.Request(
        'http://localhost:8000/auth/login', 
        data=json.dumps({"email": "admin@sanestix.com", "password": "Leads0s"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        token = json.loads(res.read())['access_token']
        return token

def create_campaign(token):
    req = urllib.request.Request(
        'http://localhost:8000/campaigns', 
        data=json.dumps({
            "name": "Full E2E Python Test",
            "industry": "Real Estate",
            "country": "USA",
            "state": "CA",
            "max_leads": 5
        }).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as res:
        campaign = json.loads(res.read())
        print(f"Created campaign: {campaign['id']}")
        return campaign['id']

token = login()
campaign_id = create_campaign(token)
print(f"Waiting 10 seconds for n8n to finish processing...")
time.sleep(10)
