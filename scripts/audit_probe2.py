import httpx, asyncio, json

BASE = 'http://localhost:8000'
c = httpx.AsyncClient(base_url=BASE, timeout=15)

async def login(u, p):
    r = await c.post('/api/auth/login', json={'username': u, 'password': p})
    return r.json()['access_token'] if r.status_code == 200 else None

async def main():
    t_pass = await login('passenger', 'passenger123')
    t_ad = await login('admin', 'admin123')
    H = {'Authorization': f'Bearer {t_pass}'}
    HA = {'Authorization': f'Bearer {t_ad}'}

    print('--- STATION CONGESTION ---')
    r = await c.get('/api/congestion/station/1', headers=HA)
    print('station congestion:', r.status_code, r.text[:300])

    print('\n--- SIM PAUSE/RESUME lifecycle ---')
    # ensure started
    r = await c.post('/api/simulation/control', json={'action': 'start', 'speed': 5}, headers=HA)
    print('start:', r.status_code, r.text)
    await asyncio.sleep(2)
    r = await c.get('/api/simulation/status', headers=HA)
    s1 = r.json()
    print('after start -> is_running=%s is_paused=%s scenario=%s' % (s1.get('is_running'), s1.get('is_paused'), s1.get('scenario')))

    r = await c.post('/api/simulation/control', json={'action': 'pause'}, headers=HA)
    print('pause:', r.status_code, r.text)
    await asyncio.sleep(1)
    r = await c.get('/api/simulation/status', headers=HA)
    s2 = r.json()
    print('after pause -> is_running=%s is_paused=%s' % (s2.get('is_running'), s2.get('is_paused')))

    # check train frozen during pause
    r = await c.get('/api/trains/7/live', headers=H)
    p1 = r.json().get('current_position', {})
    pos1 = (p1.get('latitude'), p1.get('longitude'))
    await asyncio.sleep(2)
    r = await c.get('/api/trains/7/live', headers=H)
    p2 = r.json().get('current_position', {})
    pos2 = (p2.get('latitude'), p2.get('longitude'))
    print('frozen during pause:', 'YES frozen' if pos1 == pos2 else 'NO moved', pos1, pos2)

    r = await c.post('/api/simulation/control', json={'action': 'resume'}, headers=HA)
    print('resume:', r.status_code, r.text)
    await asyncio.sleep(3)
    r = await c.get('/api/simulation/status', headers=HA)
    s3 = r.json()
    print('after resume -> is_running=%s is_paused=%s' % (s3.get('is_running'), s3.get('is_paused')))
    r = await c.get('/api/trains/7/live', headers=H)
    p3 = r.json().get('current_position', {})
    pos3 = (p3.get('latitude'), p3.get('longitude'))
    print('moving after resume:', 'YES moving' if pos3 != pos2 else 'NO frozen', pos3)
    print('sim state field:', s3)

    print('\n--- LIVE ENDPOINT next_station ---')
    r = await c.get('/api/trains/7/live', headers=H)
    live = r.json()
    print('next_station:', live.get('next_station'))
    print('current_position.next_station_id:', r.json().get('current_position', {}).get('next_station_id'))

    print('\n--- ETA RAW JSON ---')
    r = await c.get('/api/predictions/eta/12345', headers=H)
    eta = r.json()
    print('model_type=%s confidence=%s' % (eta.get('model_type'), eta.get('confidence_score')))
    print('interval_lower=%s upper=%s' % (eta.get('prediction_interval_lower'), eta.get('prediction_interval_upper')))
    print('explanations=%s ai=%s' % (len(eta.get('explanations', [])), eta.get('ai_explanation')))
    print('current_station=%s next_station=%s' % (eta.get('current_station'), eta.get('next_station')))
    print('predicted_arrival_delay=%s data_source=%s' % (eta.get('predicted_arrival_delay_minutes'), eta.get('data_source')))

    print('\n--- STATION REPORT CORRECT PAYLOAD ---')
    report = {
        'train_id': 7, 'station_id': 1, 'event_type': 'PLATFORM_OCCUPIED',
        'severity': 'HIGH', 'description': 'Platform 2 blocked by freight',
        'start_time': '2026-09-11T10:00:00', 'delay_impact_minutes': 15
    }
    r = await c.post('/api/stations/1/reports', json=report,
                     headers={'Authorization': f'Bearer {await login("station_master","station123")}'})
    print('correct-payload report:', r.status_code, r.text[:250])
    rid = r.json().get('id') if r.status_code == 201 else None
    if rid:
        rr = await c.patch(f'/api/stations/reports/{rid}',
                           json={'status': 'PUBLISHED'},
                           headers={'Authorization': f'Bearer {await login("station_master","station123")}'})
        print('verify/publish report:', rr.status_code, rr.json().get('status') if rr.status_code == 200 else rr.text)

    print('\n--- ALERT CREATION & WEBSOCKET BROADCAST ---')
    r = await c.post('/api/alerts', json={
        'station_id': 1, 'severity': 'MODERATE',
        'title': 'Test alert', 'message': 'Delay reported', 'type': 'DELAY'
    }, headers=HA)
    print('create alert:', r.status_code, r.text[:150])

asyncio.run(main())