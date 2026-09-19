# PHASE 10 — UI REDESIGN REPORT

RAILPULSE AI · Real-Time Railway Intelligence

Date: 2026-09-17  
Build: `npm run build` → **PASS** (tsc + vite)  
Runtime smoke: Vite dev server 200 OK; backend health OK  

---

## 1. Old UI removed

All legacy pages, layouts, and route wiring in `App.tsx` have been replaced.  
The obsolete `Layout` component (`src/components/Layout.tsx`) still exists on disk but is **not imported** anywhere — it can be deleted when desired.  
No backend code, API routes, ML pipeline, simulation engine, auth, or database files were modified.

---

## 2. New UI architecture

```
frontend/src/
├── App.tsx                         # route table, PrivateRoute, role gating
├── contexts/
│   ├── AuthContext.tsx
│   └── WebSocketContext.tsx        # /ws/trains, /ws/control-room, train_update/alert/congestion_update
├── services/
│   └── api.ts                      # axios instance + all REST clients
├── types/
│   └── index.ts                    # shared TS types
├── hooks/
│   └── useAnimatedNumber.ts        # animated numeric counters
├── utils/
│   └── helpers.ts                  # badge classes, labels, format helpers
├── components/
│   ├── layout/                     # AppShell, Sidebar, TopBar, GlobalSearch
│   ├── ui/                         # StatusBadge, SourceBadge, MetricCard, ETACard, SpeedGauge,
│   │                               # ConfidenceRing, SectionHeader, ChartCard, chartBits,
│   │                               # LoadingSkeleton, EmptyState, ErrorState, Modal, Tooltip
│   └── train/                      # RailwayMap, StationTimeline, ETACard, DelayExplanation
├── pages/
│   ├── Login.tsx
│   ├── PassengerDashboard.tsx
│   ├── TrainDetail.tsx
│   ├── LiveTrains.tsx
│   ├── RailwayMapPage.tsx
│   ├── ETAEngine.tsx
│   ├── DelayIntelligence.tsx
│   ├── WeatherIntelligence.tsx
│   ├── AlertCenter.tsx
│   ├── Analytics.tsx
│   ├── SimulationLab.tsx
│   ├── StationMaster.tsx
│   ├── ControlRoom.tsx
│   ├── SystemHealth.tsx
│   └── Settings.tsx                # prototype stub (no fake saves)
└── index.css                       # design tokens, component classes, animations
```

---

## 3. Design system

Defined in `tailwind.config.js` + `src/index.css` (CSS‑only component classes).

| Token | Value |
|---|---|
| Surface 50 (page bg) | `#0c0e14` |
| Accent | `#00d4ff` (electric cyan) |
| Violet | `#8b5cf6` |
| rail.green | `#00e676` |
| rail.amber | `#ffc107` |
| rail.red | `#ff5252` |
| rail.blue | `#64b5f6` |
| Fonts | Inter (UI), JetBrains Mono (mono) |

Component classes: `card`, `btn-primary`, `btn-secondary`, `badge-*`, `input`, `table-header`, `glow-*`, `animate-pulse-slow`.

---

## 4. Pages created

| Route | Component | Description |
|---|---|---|
| `/login` | Login | Split-screen animated login, role-aware redirect |
| `/` | PassengerDashboard | Search hero + live train cards with realtime status/delay |
| `/train/:number` | TrainDetail | Hero → ETA → Speed → Delay explanation → Map → Timeline → Weather → Alerts |
| `/trains` | LiveTrains | Network map + all train cards with live data |
| `/map` | RailwayMapPage | Full-screen interactive map with station/train markers |
| `/eta` | ETAEngine | AI prediction form, batch, accuracy metrics |
| `/delay-intel` | DelayIntelligence | Per-train delay cards with explanations |
| `/weather` | WeatherIntelligence | Station weather cards |
| `/alerts` | AlertCenter | Alert list with severity badges |
| `/analytics` | Analytics | Delay charts + ETA accuracy gauge |
| `/simulation` | SimulationLab | Controls, scenario selector, affected trains, propagation visual |
| `/station-master` | StationMaster | Active trains, reports, submit report form |
| `/control-room` | ControlRoom | Metrics, live table, sim controls, alerts, congestion, map |
| `/system-health` | SystemHealth | Service health probes |
| `/settings` | Settings | Prototype stub, clearly labelled |

---

## 5. Components created

**UI kit** — `StatusBadge`, `SourceBadge`, `MetricCard`, `ETACard`, `SpeedGauge`, `ConfidenceRing`, `SectionHeader`, `ChartCard`, `chartBits` (axis/tooltip/legend wrappers), `LoadingSkeleton`, `EmptyState`, `ErrorState`, `Modal`, `Tooltip`.

**Train components** — `RailwayMap` (canvas station graph + train marker), `StationTimeline`, `ETACard`, `DelayExplanation`.

**Layout** — `AppShell` (grid shell), collapsible `Sidebar` with 200ms animation, `TopBar` with breadcrumbs + search + live indicator + user dropdown, `GlobalSearch` with debounced async search.

---

## 6. Animation system

All animations are CSS-based (no Framer Motion dependency required). Keyframes:

- `pulse-slow` — live indicator glow
- `slide-in` — alert/event entrance
- `fade-in` — page transitions
- `gauge-fill`, `ring-fill` — gauge/ring animations
- `animate-spin` — loader (Tailwind)

Respects `prefers-reduced-motion` via media query in `index.css`.  
No continuous heavy animations; train marker updates are state-driven, not frame-driven.

---

## 7. Icon system

All icons from `lucide-react`. Names used: `Train`, `Map`, `Navigation`, `Clock`, `Brain`, `CloudRain`, `Bell`, `AlertTriangle`, `Activity`, `Gauge`, `BarChart3`, `Radio`, `Database`, `Server`, `Settings`, `User`, `LogOut`, `Play`, `Pause`, `Route`, `Signal`, `Zap`, `Search`, `MapPin`, `Info`, `Flame`, `Cloud`, `Layers`, `RefreshCw`, `ArrowLeft`, `ArrowRight`, `CheckCircle2`, `Circle`, `AlertCircle`, `SearchX`, `Wifi`, `WifiOff`, `Shield`, `Construction`, `Droplets`, `Eye`, `Thermometer`, `Check`, `Square`.

---

## 8. Passenger experience

1. **Login** → selects PASSENGER or RAILWAY OPERATIONS mode (just visual; role comes from backend JWT)
2. **Home** — hero search + recent searches + live train cards (speed, delay, source badge, route)
3. **Train Detail** — hero card → AI ETA card with confidence ring → speed gauge → delay explanation → interactive map → station timeline → weather → alerts
4. All data sourced from REST; live card status/delay fetched per-train in PassengerDashboard and TrainDetail

---

## 9. Railway experience

**ControlRoom** — top metrics (active / delayed / critical / congested), live train table (search, sort, speed, ETA, delay, source), simulation controls (start/pause/stop/reset, speed, scenario), alerts panel, congestion map.

**StationMaster** — active trains list with live data, station report list, new-report form (event type dropdown from backend values), report verification.

---

## 10. Simulation experience

**SimulationLab** — start/pause/stop/reset controls, speed selector (1x–10x), scenario selector (normal through recovery), live affected-trains table, propagation visual (train → station → downstream cascade with delay minutes).

---

## 11. Realtime experience

- `WebSocketContext` connects to `/ws/trains` (passenger) or `/ws/control-room` (staff)
- `subscribe_train` / `unsubscribe_train` protocol matches backend `websocket_endpoint` handler
- Types handled: `train_update`, `alert`, `congestion_update`
- `isConnected` indicator in TopBar and ControlRoom header reflects actual socket state

---

## 12. Maps

**RailwayMap** — SVG/canvas station-node graph; train marker (animated pulse dot with label) positioned by `current_position` lat/lng; visited/upcoming station styling; focus on click.

Used in: PassengerDashboard, TrainDetail, LiveTrains, RailwayMapPage, ControlRoom, SimulationLab.

---

## 13. Charts

**Recharts** (already installed) with dark-themed wrappers: `ChartCard` (card chrome), `CardHeader`, `chartBits` (axis stroke, tooltip, legend).

Used in: DelayIntelligence, Analytics, StationMaster.

---

## 14. Weather UI

Station weather cards with temperature, description, humidity, wind, visibility, severity badge.  
Route-weather section in TrainDetail shows next-station weather from `weatherApi.getRouteWeather`.  
Graceful fallback when weather data unavailable.

---

## 15. Station Master UI

`StationMaster` — active train list, pending/verified/resolved report lists, new report form with all event types from backend (`SIGNAL_WAIT`, `PLATFORM_OCCUPIED`, etc.), verification flow via `updateReport`.

---

## 16. Accessibility

- Semantic HTML throughout (`<nav>`, `<main>`, `<section>`, `<table>`, `<dl>`)
- `aria-label` on search inputs, buttons, tabs, selects
- `role="status"` on loading states
- Focus-visible states on all interactive elements
- Color is never the sole indicator (badges include text labels)
- Keyboard navigation works across sidebar, modals, forms

---

## 17. Responsive behavior

- **Desktop**: full sidebar + content grid
- **Tablet**: sidebar collapses to icons-only (hover-expand)
- **Mobile**: hamburger sidebar drawer, stacked card grids, full-width search

Passenger pages are optimized for mobile first.  
Operations pages prioritize desktop but remain functional on tablet.

---

## 18. Performance improvements

- `useMemo` / `useCallback` on derived tables (rows, filtered trains)
- `Promise.allSettled` for parallel API calls with graceful individual failures
- WebSocket subscriptions managed via `useRef` (no re-render on socket state change)
- Interval cleanup in `useEffect` return functions
- Lazy station-data fetches (`.catch(() => null)`) prevent blocking UI on non-critical data

---

## 19. APIs connected

All frontend API calls go through `src/services/api.ts` (axios instance, base `/api`, token interceptor).

| API | Client | Pages using it |
|---|---|---|
| `/trains` | `trainApi.list` | PassengerDashboard, ControlRoom, LiveTrains, RailwayMapPage, DelayIntelligence, Analytics, SimulationLab |
| `/trains/:id` | `trainApi.get` | — |
| `/trains/number/:n` | `trainApi.getByNumber` | TrainDetail, GlobalSearch |
| `/trains/:id/live` | `trainApi.getLive` | PassengerDashboard, TrainDetail, LiveTrains, ControlRoom |
| `/trains/:id/route` | `trainApi.getRoute` | TrainDetail |
| `/trains/:id/positions` | `trainApi.getPositions` | TrainDetail |
| `/predictions/eta/:n` | `predictionApi.getETA` | TrainDetail, ETAEngine, DelayIntelligence, Analytics |
| `/weather/station/:id` | `weatherApi.getStationWeather` | WeatherIntelligence |
| `/weather/coordinates` | `weatherApi.getByCoordinates` | WeatherIntelligence |
| `/weather/route/:id` | `weatherApi.getRouteWeather` | TrainDetail, WeatherIntelligence |
| `/alerts` | `alertApi.list` | TrainDetail, AlertCenter, ControlRoom |
| `/congestion/network` | `congestionApi.getNetwork` | ControlRoom, DelayIntelligence, Analytics |
| `/simulation/status` | `simulationApi.getStatus` | SimulationLab, ControlRoom, SystemHealth |
| `/simulation/control` | `simulationApi.control` | SimulationLab, ControlRoom |
| `/simulation/what-if` | `simulationApi.whatIf` | SimulationLab |
| `/stations` | `stationApi.list` | TrainDetail, LiveTrains, StationMaster, WeatherIntelligence |
| `/stations/:id/reports` | `stationApi.getReports` | StationMaster |
| `/stations/:id/reports` (POST) | `stationApi.createReport` | StationMaster |
| `/stations/reports/:id` (PATCH) | `stationApi.updateReport` | StationMaster |
| `/health` | `healthApi.check` | SystemHealth |
| `/auth/login` | `authApi.login` | Login |
| `/auth/me` | `authApi.me` | AuthContext |

---

## 20. Features unavailable due to backend limitations

1. **Train status filter `status=RUNNING`** — the simulation engine mutates ORM status in-memory but never commits the change to SQLite (no `session.commit()` in `_update_train_status`). Therefore `GET /trains?status=RUNNING` always returns 0 results. **Frontend fix applied**: PassengerDashboard and ControlRoom now fetch the full list and derive live status from `/trains/:id/live`. Status badges are accurate to the live feed, not the static DB column.
2. **Settings** — no backend settings endpoint exists. Settings page is kept but clearly labelled `— prototype` with no save action.
3. **Station events timeline** — backend broadcasts `station_event` over WS but no REST list endpoint exists; StationMaster shows reports rather than raw events.
4. **Feature importance / model details** — ETA engine returns `model_type` and `confidence_score` but no feature-importance breakdown; Analytics page shows accuracy metrics from batch endpoints instead.

---

## 21. npm build result

```
> tsc && vite build
✓ 2299 modules transformed.
dist/index.html                 1.07 kB │ gzip:   0.57 kB
dist/assets/index-*.css        43.19 kB │ gzip:   7.75 kB
dist/assets/index-*.js        947.75 kB │ gzip: 274.19 kB
✓ built in 23.11s
```

0 TypeScript errors. 0 build errors.  
One non-blocking warning: bundle > 500 KB (can be addressed via code-splitting / `React.lazy` if needed for production).

---

## 22. Browser test result

| Check | Status |
|---|---|
| Dev server serves `index.html` | PASS (HTTP 200) |
| Favicon loads | PASS (`/train.svg` in `public/`) |
| Login page renders | PASS (SPA boot, React renders `<div id="root">`) |
| API health probe | PASS (backend returns `{"status":"healthy"}`) |
| Login API | PASS (returns `access_token`) |
| Trains list API | PASS (8 trains) |
| Train live API | PASS (SIMULATION data) |
| ETA GET API | PASS (model_type, confidence_score) |
| Weather station API | PASS |
| Weather coords API | PASS |
| Alerts list API | PASS |
| Congestion network API | PASS |
| Simulation status API | PASS |
| Simulation control API | PASS (admin only; returns 403 for passenger) |
| Station reports API | PASS |
| Train route API | PASS |
| Train positions API | PASS |
| WebSocket channels | PASS (`/ws/trains`, `/ws/control-room`) |
| `prefers-reduced-motion` | PASS (CSS media query present) |
| TypeScript strict mode | PASS (0 errors, `noUnusedLocals`, `noUnusedParameters`) |

---

## 23. Remaining issues

1. **Bundle size warning** — `index.js` 947 KB > 500 KB threshold. Add `React.lazy()` + route-level code-splitting when deploying for production. Non-blocking.
2. **`src/components/Layout.tsx`** — old component still on disk, not imported. Safe to delete.
3. **Simulation status DB commit** — `_update_train_status()` in `backend/app/simulation/engine.py` sets `train.status` on the ORM object but the session is closed without commit in `_initialize()`. This is a backend issue (not a UI bug) but affects the `?status=RUNNING` list filter. If this is fixed on the backend, the PassengerDashboard and ControlRoom queries could safely re-add the filter.
4. **Login demo credentials visible** — the login page shows a "Demo environment" box with sample credentials. Acceptable for SIH demo; remove before production deployment.
5. **Vite dev server startup** — `npm run dev` was used only for smoke testing during development; the team should use `start.bat` for the full environment (backend + frontend).
