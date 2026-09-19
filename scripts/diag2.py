import httpx, asyncio

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

    # Test exception handler
    r = await c.get('/api/nonexistent')
    print('nonexistent:', r.status_code, r.text[:200])

    # Get current sim status
    r = await c.get('/api/simulation/status', headers=HA)
    print('\ncurrent status:', r.status_code, r.text[:300])

    # Try start
    r = await c.post('/api/simulation/control', json={'action': 'start'}, headers=HA)
    print('\nstart:', r.status_code, r.text[:1000])

    # Live train 7
    r = await c.get('/api/trains/7/live', headers=H)
    print('\nlive 7:', r.status_code, r.text[:1000])

    # Try stop then start fresh
    r = await c.post('/api/simulation/control', json={'action': 'stop'}, headers=HA)
    print('\nstop:', r.status_code, r.text[:500])
    
    r = await c.get('/api/simulation/status', headers=HA)
    print('after stop status:', r.text[:300])
    
    r = await c.post('/api/simulation/control', json={'action': 'start'}, headers=HA)
    print('\nfresh start:', r.status_code, r.text[:1000])

asyncio.run(main())