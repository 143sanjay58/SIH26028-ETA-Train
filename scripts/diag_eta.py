import httpx, asyncio

async def main():
    c = httpx.AsyncClient(base_url='http://localhost:8000', timeout=20)
    r = await c.post('/api/auth/login', json={'username': 'passenger', 'password': 'passenger123'})
    h = {'Authorization': f'Bearer {r.json()["access_token"]}'}
    r = await c.get('/api/predictions/eta/12345', headers=h)
    print(r.status_code)
    print(r.text[:2500])
    await c.aclose()

asyncio.run(main())