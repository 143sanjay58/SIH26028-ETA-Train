import httpx, asyncio

async def main():
    c = httpx.AsyncClient(base_url='http://127.0.0.1:8009', timeout=15)
    r = await c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    t = r.json()['access_token']
    h = {'Authorization': f'Bearer {t}'}

    # Start
    r = await c.post('/api/simulation/control', json={'action': 'start', 'speed': 5}, headers=h)
    print('control start:', r.status_code, r.text[:400])

    await asyncio.sleep(2)

    # Pause
    r = await c.post('/api/simulation/control', json={'action': 'pause'}, headers=h)
    print('control pause:', r.status_code)
    print(r.text[:1500])

    # Resume
    r = await c.post('/api/simulation/control', json={'action': 'resume'}, headers=h)
    print('control resume:', r.status_code)
    print(r.text[:1500])

    # Status
    await asyncio.sleep(3)
    r = await c.get('/api/simulation/status', headers=h)
    print('status:', r.status_code, r.text[:400])

    # Verify train moving after resume
    r = await c.post('/api/auth/login', json={'username': 'passenger', 'password': 'passenger123'})
    tp = r.json()['access_token']
    hp = {'Authorization': f'Bearer {tp}'}
    for i in range(2):
        await asyncio.sleep(3)
        r = await c.get('/api/trains/7/live', headers=hp)
        if r.status_code == 200:
            p = r.json().get('current_position')
            print(f'  live pos: lat={p["latitude"]:.4f} lon={p["longitude"]:.4f} speed={p["speed_kmh"]:.1f}')
        else:
            print('  live error:', r.status_code, r.text[:300])

    await c.aclose()

asyncio.run(main())
