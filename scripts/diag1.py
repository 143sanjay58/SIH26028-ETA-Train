import httpx, asyncio, json

BASE = 'http://localhost:8000'
c = httpx.AsyncClient(base_url=BASE, timeout=20)

async def login(u, p):
    r = await c.post('/api/auth/login', json={'username': u, 'password': p})
    return r.json()['access_token'] if r.status_code == 200 else None

async def main():
    t_ad = await login('admin', 'admin123')
    t_pass = await login('passenger', 'passenger123')
    HA = {'Authorization': f'Bearer {t_ad}'}
    H = {'Authorization': f'Bearer {t_pass}'}

    for action in ['start', 'pause']:
        r = await c.post('/api/simulation/control', json={'action': action}, headers=HA)
        print(f'control {action}:', r.status_code)
        print(r.text[:800])
        print('---')

    r = await c.get('/api/simulation/status', headers=HA)
    print('status:', r.status_code, r.text[:300])

    r = await c.get('/api/trains/7/live', headers=H)
    print('live 7:', r.status_code)
    print(r.text[:500])

asyncio.run(main())