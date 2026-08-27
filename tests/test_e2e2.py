import urllib.request
import urllib.parse
import json
import http.cookiejar
import time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
req_login = urllib.request.Request(
    'http://localhost:8000/auth/login', 
    data=json.dumps({"email": "admin@sanestix.com", "password": "Leads0s"}).encode(),
    headers={'Content-Type': 'application/json'}
)
opener.open(req_login)

# Create Campaign
req_campaign = urllib.request.Request(
    'http://localhost:8000/campaigns', 
    data=json.dumps({
        "name": "Final Real E2E Test",
        "industry": "Real Estate",
        "country": "USA",
        "state": "NY",
        "max_leads": 10
    }).encode(),
    headers={'Content-Type': 'application/json'}
)
res = opener.open(req_campaign)
campaign = json.loads(res.read())
print(f"Created campaign: {campaign['id']}")
print("Waiting 15 seconds for n8n to process...")
time.sleep(15)
