import asyncio
import httpx
from collections import Counter

async def claim_account(client):
    try:
        response = await client.get('http://localhost:8000/internal/apify-accounts/available')
        if response.status_code == 200:
            return response.json()['id']
        return str(response.status_code)
    except Exception as e:
        return str(e)

async def main():
    headers = {'X-Internal-Key': '8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA'}
    async with httpx.AsyncClient(headers=headers) as client:
        # Launch 5 concurrent requests
        tasks = [claim_account(client) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        counter = Counter(results)
        print("Results:")
        for acct_id, count in counter.items():
            print(f"{acct_id}: {count} times")

if __name__ == "__main__":
    asyncio.run(main())
