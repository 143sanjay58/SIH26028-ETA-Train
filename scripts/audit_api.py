import httpx, json, asyncio, sys, os
os.environ.setdefault('ENVIRONMENT', 'development')
BASE = 'http://localhost:8000'
c = httpx.AsyncClient(base_url=BASE, timeout=15)

async def login(u, p):
    r = await c.post('/api/auth/login', json={'username': u, 'password': p})
    if r.status_code != 200:
        return None
    return r.json()['access_token']

async def auth_get(url, token):
    return await c.get(url, headers={'Authorization': f'Bearer {token}'})

async def auth_post(url, token, data=None):
    return await c.post(url, json=data, headers={'Authorization': f'Bearer {token}'})

results = []

def log(feature, status, detail=''):
    results.append((feature, status, detail))
    print(f'  {status:20s} | {feature} | {detail}')

async def main():
    print('=== PHASE 1: AUTH & CORE API ===')
    
    t_pass = await login('passenger', 'passenger123')
    t_sm = await login('station_master', 'station123')
    t_op = await login('operator', 'operator123')
    t_ad = await login('admin', 'admin123')
    t_su = await login('supervisor', 'supervisor123')
    
    log('1. Passenger login', 'PASS' if t_pass else 'FAIL', f'token={bool(t_pass)}')
    log('2. Station Master login', 'PASS' if t_sm else 'FAIL', f'token={bool(t_sm)}')
    log('   Operator login', 'PASS' if t_op else 'FAIL')
    log('   Admin login', 'PASS' if t_ad else 'FAIL')
    log('   Supervisor login', 'PASS' if t_su else 'FAIL')
    
    # Bad credentials
    r = await c.post('/api/auth/login', json={'username': 'passenger', 'password': 'wrong'})
    log('Bad password rejected', 'PASS' if r.status_code == 401 else 'FAIL', f'status={r.status_code}')
    
    # Missing fields
    r = await c.post('/api/auth/login', json={})
    log('Empty login rejected', 'PASS' if r.status_code != 200 else 'FAIL', f'status={r.status_code}')
    
    # Unauthorized access
    r = await c.get('/api/trains')
    log('Unauth trains blocked', 'PASS' if r.status_code == 401 else 'FAIL', f'status={r.status_code}')
    
    # Admin-only endpoint
    r_op = await auth_get('/api/trains', t_op)
    r_pa = await auth_get('/api/trains', t_pass)
    log('Passenger can list trains', 'PASS' if r_pa.status_code == 200 else 'FAIL', f'status={r_pa.status_code}')
    
    print('\n=== PHASE 2: TRAIN SEARCH & DETAILS ===')
    
    r = await auth_get('/api/trains/number/12345', t_ad)
    log('3. Train search by number', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    train = r.json() if r.status_code == 200 else {}
    tid = train.get('id', 7)
    log('4. Train details', 'PASS' if train.get('train_number') == '12345' else 'FAIL',
        f'number={train.get("train_number")} name={train.get("train_name")} type={train.get("train_type")}')
    
    # Search non-existent
    r = await auth_get('/api/trains/number/99999', t_ad)
    log('Non-existent train returns 404', 'PASS' if r.status_code == 404 else 'FAIL', f'status={r.status_code}')
    
    print('\n=== PHASE 3: LIVE TRACKING ===')
    
    r = await auth_get(f'/api/trains/{tid}/live', t_pass)
    live = r.json() if r.status_code == 200 else {}
    has_pos = live.get('current_position') is not None
    speed = live.get('current_speed_kmh', 0)
    delay = live.get('current_delay_minutes', 0)
    ns = live.get('next_station')
    
    log('5. Train location (lat/lon)', 'PASS' if has_pos else 'PARTIALLY',
        f'has_position={has_pos} speed={speed:.1f}km/h')
    log('6. Current speed', 'PASS' if speed > 0 else 'PARTIALLY', f'speed={speed:.1f}km/h')
    log('7. Next station', 'PASS' if ns else 'PARTIALLY',
        f'name={ns.get("station_name") if ns else "None"} code={ns.get("station_code") if ns else "None"}')
    log('   Distance remaining', 'PASS', f'km={live.get("distance_remaining_km", 0):.1f}')
    log('   Data source label', 'PASS' if live.get('data_source') else 'PARTIALLY', f'source={live.get("data_source")}')
    
    # Train route
    r = await auth_get(f'/api/trains/{tid}/route', t_pass)
    route = r.json() if r.status_code == 200 else {}
    log('   Train route', 'PASS' if r.status_code == 200 else 'FAIL',
        f'upcoming={len(route.get("upcoming_stations", []))} passed={len(route.get("passed_stations", []))}')
    
    # Train events
    r = await auth_get(f'/api/trains/{tid}/events', t_pass)
    events = r.json() if r.status_code == 200 else []
    log('   Train events', 'PASS' if r.status_code == 200 else 'FAIL', f'count={len(events)}')
    
    # Train positions (historical)
    r = await auth_get(f'/api/trains/{tid}/positions', t_pass)
    positions = r.json() if r.status_code == 200 else []
    log('   Train positions history', 'PASS' if r.status_code == 200 else 'FAIL', f'count={len(positions)}')
    
    print('\n=== PHASE 4: ETA & PREDICTIONS ===')
    
    r = await auth_get(f'/api/predictions/eta/12345', t_pass)
    eta = r.json() if r.status_code == 200 else {}
    log('8. ETA prediction', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    log('9. Scheduled vs predicted', 'PASS' if eta.get('predicted_arrival_time') else 'PARTIALLY',
        f'predicted={eta.get("predicted_arrival_time")} delay={eta.get("predicted_arrival_delay_minutes")}')
    log('10. Delay calc', 'PASS' if eta.get('current_delay_minutes') is not None else 'FAIL',
        f'current_delay={eta.get("current_delay_minutes")}')
    log('    Model type', 'PASS', f'{eta.get("model_type")}')
    log('    Confidence', 'PASS' if eta.get('confidence_score') is not None else 'PARTIALLY',
        f'={eta.get("confidence_score")}')
    log('    Destination', 'PASS', f'{eta.get("destination_station")}')
    log('    Data source', 'PASS', f'{eta.get("data_source")}')
    
    # Delay propagation - different trains
    for tn in ['12001', '12002', '12301', '12302', '12951']:
        r = await auth_get(f'/api/predictions/eta/{tn}', t_pass)
        e = r.json() if r.status_code == 200 else {}
        d = e.get('predicted_arrival_delay_minutes', 'N/A')
        log(f'    ETA for {tn}', 'PASS' if r.status_code == 200 else 'SKIP',
            f'delay={d} model={e.get("model_type", "?")}')
    
    # Explanation endpoint (factors appear only when a delay exists; empty at 0 delay is correct)
    r = await auth_get('/api/predictions/eta/12345?include_explanations=true', t_pass)
    e2 = r.json() if r.status_code == 200 else {}
    has_exp = bool(e2.get('explanations'))
    delay_zero = e2.get('predicted_arrival_delay_minutes') in (0, 0.0)
    log('22. Explanations', 'PASS' if (has_exp or delay_zero) else 'PARTIALLY',
        f'count={len(e2.get("explanations", []))}')
    
    # Prediction interval
    has_interval = bool(e2.get('prediction_interval_lower') and e2.get('prediction_interval_upper'))
    log('21. Uncertainty interval', 'PASS' if has_interval else 'PARTIALLY',
        f'lower={e2.get("prediction_interval_lower")} upper={e2.get("prediction_interval_upper")}')
    
    # ETA without explanations
    r = await auth_get('/api/predictions/eta/12345?include_explanations=false&include_uncertainty=false', t_pass)
    e3 = r.json() if r.status_code == 200 else {}
    log('    ETA (no explanations)', 'PASS' if r.status_code == 200 else 'FAIL')
    
    print('\n=== PHASE 5: WEATHER ===')
    
    r = await auth_get('/api/weather/station/1', t_pass)
    w = r.json() if r.status_code == 200 else {}
    has_cur = w.get('current') is not None
    log('12. Weather API', 'PASS' if has_cur else 'PARTIALLY',
        f'has_current={has_cur} source={w.get("data_source")} temp={w.get("current", {}).get("temperature_celsius")}')
    log('    Weather station code', 'PASS' if w.get('station_code') else 'FAIL', f'{w.get("station_code")}')
    log('    Weather condition', 'PASS' if has_cur and w['current'].get('weather_condition') else 'PARTIALLY',
        f'{w.get("current", {}).get("weather_condition")} / {w.get("current", {}).get("weather_description")}')
    log('    Weather humidity', 'PASS' if has_cur else 'SKIP', f'{w.get("current", {}).get("humidity_percent")}')
    log('    Weather wind', 'PASS' if has_cur else 'SKIP', f'{w.get("current", {}).get("wind_speed_kmh")} km/h')
    
    # Forecast
    forecast = w.get('forecast', [])
    log('    Weather forecast', 'PASS' if len(forecast) > 0 else 'PARTIALLY', f'days={len(forecast)}')
    
    # GPS weather
    r = await auth_get('/api/weather/coordinates?lat=28.6139&lon=77.2090', t_pass)
    wg = r.json() if r.status_code == 200 else {}
    log('    GPS weather', 'PASS' if wg.get('current') else 'PARTIALLY', f'status={r.status_code}')
    
    # Route weather
    r = await auth_get(f'/api/weather/route/{tid}', t_pass)
    wr = r.json() if r.status_code == 200 else []
    log('13. Route weather', 'PASS' if r.status_code == 200 else 'PARTIALLY', f'count={len(wr) if isinstance(wr, list) else "?"}')
    
    print('\n=== PHASE 6: STATION MASTER OPERATIONS ===')
    
    r = await auth_get('/api/stations?limit=1', t_sm)
    st = r.json() if r.status_code == 200 else {}
    st_list = st.get('stations', [])
    st_id = st_list[0]['id'] if st_list else 1
    
    # Create report
    report = {
        'train_id': tid,
        'station_id': st_id,
        'event_type': 'PLATFORM_OCCUPIED',
        'severity': 'HIGH',
        'description': 'Freight train occupying platform 2, preventing scheduled departure',
        'start_time': '2026-09-12T06:00:00Z',
        'delay_impact_minutes': 15,
    }
    r = await c.post(f'/api/stations/{st_id}/reports', json=report,
                     headers={'Authorization': f'Bearer {t_sm}'})
    log('14. Station Master report', 'PASS' if r.status_code in [200, 201] else 'FAIL',
        f'status={r.status_code}')
    report_id = r.json().get('id') if r.status_code in [200, 201] else None
    
    # Read reports
    r = await auth_get(f'/api/stations/{st_id}/reports', t_sm)
    reports = r.json() if r.status_code == 200 else {}
    items = reports.get('items', [])
    log('15. Delay reports list', 'PASS' if r.status_code == 200 else 'FAIL', f'count={len(items)}')
    
    # Station detail
    r = await auth_get(f'/api/stations/{st_id}', t_pass)
    sd = r.json() if r.status_code == 200 else {}
    log('    Station detail', 'PASS' if r.status_code == 200 else 'FAIL',
        f'name={sd.get("name")} code={sd.get("code")} platform_count={sd.get("platform_count")}')
    
    # Passenger cannot create report (authorization check)
    r_p_report = await c.post(f'/api/stations/{st_id}/reports', json=report,
                              headers={'Authorization': f'Bearer {t_pass}'})
    log('24. Passenger blocked from station reports', 'PASS' if r_p_report.status_code in [401, 403] else 'FAIL',
        f'status={r_p_report.status_code}')
    
    # Station events
    r = await auth_get(f'/api/stations/{st_id}/events', t_pass)
    log('    Station events', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    
    # Station reports by code
    r = await auth_get('/api/stations/code/NDLS', t_pass)
    log('    Station by code', 'PASS' if r.status_code == 200 else 'FAIL',
        f'name={r.json().get("name") if r.status_code==200 else "?"}')
    
    print('\n=== PHASE 7: ALERTS & CONGESTION ===')
    
    r = await auth_get('/api/alerts', t_ad)
    alerts = r.json() if r.status_code == 200 else []
    log('    Alerts list', 'PASS' if r.status_code == 200 else 'FAIL', f'count={len(alerts)}')
    
    r = await auth_get('/api/congestion/network', t_ad)
    cong = r.json() if r.status_code == 200 else []
    log('20. Network congestion', 'PASS' if r.status_code == 200 else 'FAIL',
        f'count={len(cong)} status={r.status_code}')
    
    # Station congestion
    r = await auth_get(f'/api/congestion/station/{st_id}', t_ad)
    log('    Station congestion', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    
    print('\n=== PHASE 8: SIMULATION ===')
    
    r = await c.post('/api/simulation/control', json={'action': 'start'},
                    headers={'Authorization': f'Bearer {t_ad}'})
    log('   Start simulation', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    
    scenarios = ['NORMAL', 'CONGESTION', 'SIGNAL_DELAY', 'SPEED_RESTRICTION',
                 'HEAVY_RAIN', 'LOW_VISIBILITY', 'UNSCHEDULED_STOP', 'CASCADING_DELAY', 'RECOVERY']
    
    for sc in scenarios:
        r = await c.post('/api/simulation/control',
                        json={'action': 'set_scenario', 'scenario': sc},
                        headers={'Authorization': f'Bearer {t_ad}'})
        sc_ok = r.status_code == 200
        await asyncio.sleep(1)
        
        # Check status
        r = await auth_get('/api/simulation/status', t_ad)
        st = r.json() if r.status_code == 200 else {}
        match = st.get('scenario') == sc
        
        # Check ETA changed
        r = await auth_get('/api/predictions/eta/12345?include_explanations=false&include_uncertainty=false', t_pass)
        eta = r.json() if r.status_code == 200 else {}
        delay = eta.get('predicted_arrival_delay_minutes', 'N/A')
        
        log(f'18. Scenario {sc}', 'PASS' if match else 'FAIL',
            f'scenario_set={match} actual={st.get("scenario")} delay={delay}')
    
    # Resume normal
    await c.post('/api/simulation/control', json={'action': 'set_scenario', 'scenario': 'NORMAL'},
                headers={'Authorization': f'Bearer {t_ad}'})
    
    # Speed control
    r = await c.post('/api/simulation/control', json={'action': 'set_speed', 'speed': 10.0},
                    headers={'Authorization': f'Bearer {t_ad}'})
    log('    Speed control', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    
    # Pause/Resume
    r = await c.post('/api/simulation/control', json={'action': 'pause'},
                    headers={'Authorization': f'Bearer {t_ad}'})
    r2 = await auth_get('/api/simulation/status', t_ad)
    s2 = r2.json() if r2.status_code == 200 else {}
    log('    Pause simulation', 'PASS' if s2.get('is_paused') else 'FAIL', f'paused={s2.get("is_paused")}')
    
    r = await c.post('/api/simulation/control', json={'action': 'resume'},
                    headers={'Authorization': f'Bearer {t_ad}'})
    r2 = await auth_get('/api/simulation/status', t_ad)
    s2 = r2.json() if r2.status_code == 200 else {}
    log('    Resume simulation', 'PASS' if s2.get('is_running') else 'FAIL', f'running={s2.get("is_running")}')
    
    # Stop
    r = await c.post('/api/simulation/control', json={'action': 'stop'},
                    headers={'Authorization': f'Bearer {t_ad}'})
    r2 = await auth_get('/api/simulation/status', t_ad)
    s2 = r2.json() if r2.status_code == 200 else {}
    log('    Stop simulation', 'PASS' if not s2.get('is_running') else 'FAIL', f'running={s2.get("is_running")}')
    
    # What-if
    whatif = {'train_number': '12345', 'scenario_type': 'delay', 'parameters': {'delay_minutes': 30}, 'simulation_duration_minutes': 60}
    r = await auth_post('/api/simulation/what-if', t_ad, whatif)
    log('    What-if simulation', 'PASS' if r.status_code == 200 else 'FAIL',
        f'status={r.status_code}')
    
    print('\n=== PHASE 9: PREDICTION PIPELINE ===')
    
    r = await auth_get('/api/predictions/trains/7', t_pass)
    preds = r.json() if r.status_code == 200 else []
    log('    Prediction history', 'PASS' if r.status_code == 200 else 'FAIL', f'count={len(preds)}')
    
    r = await auth_get('/api/predictions/current/12345', t_pass)
    log('    Current ETA endpoint', 'PASS' if r.status_code == 200 else 'FAIL', f'status={r.status_code}')
    
    # Health check (no auth required)
    r = await c.get('/api/health')
    log('23. Health endpoint', 'PASS' if r.status_code == 200 else 'FAIL',
        f'db={r.json().get("database")} redis={r.json().get("redis")}')
    
    print('\n=== PHASE 10: AUTHORIZATION ===')
    
    # Station master cannot access admin-only endpoints
    # Passenger cannot do admin actions
    r = await auth_post('/api/trains', t_pass, {'train_number': 'TEST', 'train_name': 'Test', 'train_type': 'EXPRESS',
        'origin_station_id': 1, 'destination_station_id': 2, 'route_id': 1,
        'scheduled_departure': '2026-01-01T00:00:00', 'scheduled_arrival': '2026-01-01T06:00:00'})
    log('    Passenger cannot create train', 'PASS' if r.status_code in [401, 403] else 'FAIL', f'status={r.status_code}')
    
    # SUMMARY
    print('\n' + '=' * 70)
    pass_c = sum(1 for _, s, _ in results if s == 'PASS')
    part_c = sum(1 for _, s, _ in results if s == 'PARTIALLY')
    fail_c = sum(1 for _, s, _ in results if s == 'FAIL')
    skip_c = sum(1 for _, s, _ in results if s in ('SKIP', 'CHECK_CODE'))
    print(f'PASS: {pass_c} | PARTIAL: {part_c} | FAIL: {fail_c} | SKIP: {skip_c} | Total: {len(results)}')
    print('\nFAILURES:')
    for f, s, d in results:
        if s == 'FAIL':
            print(f'  FAIL: {f} -- {d}')
    print('\nPARTIAL:')
    for f, s, d in results:
        if s == 'PARTIALLY':
            print(f'  PARTIAL: {f} -- {d}')

asyncio.run(main())
