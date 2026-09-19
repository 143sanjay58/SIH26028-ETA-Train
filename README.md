<<<<<<< HEAD
# ETA-Train-Time
=======
<<<<<<< HEAD
# ETA-Train-Time
=======
# RAILPULSE AI

Real-Time Railway Intelligence - AI-Powered Dynamic ETA Prediction, Train Tracking and Railway Operations Intelligence Platform

Built for Smart India Hackathon (SIH)

"Predict every arrival. Understand every delay."

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAILPULSE AI                                │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript + Tailwind)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Passenger UI │  │ Control Room │  │ Station Master UI    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python 3.12+)                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Trains  │ │Stations │ │   ETA   │ │ Weather │ │Congestion│  │
│  │ Service │ │ Service │ │ Service │ │ Service │ │ Service  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Alert   │ │ Delay   │ │Simulation│ │  ML     │ │ WebSocket│  │
│  │ Service │ │Propagate│ │ Engine   │ │Predictor│ │ Manager  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │ Redis        │  │ ML Models    │          │
│  │ (Primary)    │  │ (Cache/PubSub)│ │ (XGBoost/LGBM)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Passenger Platform
- Real-time train tracking with moving map marker
- Dynamic ETA predictions with confidence intervals
- Multi-model ETA (Baseline, Statistical, ML)
- Next station weather and route weather
- Station master reports (verified reasons for delays)
- GPS-assisted tracking (optional, permission-based)
- Delay propagation visualization
- Explainable AI for ETA predictions

### Railway Operations / Control Room
- Network overview with live train positions
- Real-time congestion monitoring
- Predictive alerts (delay, congestion, weather, anomalies)
- What-if simulation for operational decisions
- Digital twin of railway network
- Simulation engine with 11 scenarios
- Station master report verification workflow
- Model performance monitoring

### Core Intelligence
- **3-Level ETA Engine**: Baseline → Statistical → ML
- **Delay Propagation**: Section-by-section delay cascade
- **Congestion Intelligence**: Train density, speed, historical patterns
- **Weather Integration**: Open-Meteo API (no key required)
- **Extended Halt Detection**: Automatic dwell time analysis
- **ML Pipeline**: Feature engineering, training, inference
- **Explainability**: Feature contribution breakdown

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| ML | XGBoost, LightGBM, scikit-learn, pandas, numpy |
| Real-time | FastAPI WebSocket, asyncio |
| Database | PostgreSQL 16 (primary), SQLite (dev fallback) |
| Cache | Redis 7 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Maps | Leaflet + React-Leaflet |
| Charts | Recharts |
| Auth | JWT (HS256), bcrypt, RBAC |
| Container | Docker, Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Development Setup

```bash
# Clone and navigate
git clone <repo>
cd railpulse-ai

# Copy environment template
cp .env.example .env

# Start all services
docker compose up --build

# Access applications
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Development

```bash
# Backend (run from the project ROOT - pyproject.toml lives here)
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed.py
python -m uvicorn backend.app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Operator | operator | operator123 |
| Supervisor | supervisor | supervisor123 |
| Station Master | station_master | station123 |
| Passenger | passenger | passenger123 |

## API Endpoints

### Trains
- `GET /api/trains` - List trains with filters
- `GET /api/trains/{id}` - Train details
- `GET /api/trains/number/{number}` - Find by train number
- `GET /api/trains/{id}/live` - Real-time position & status
- `GET /api/trains/{id}/route` - Route with upcoming stations
- `GET /api/trains/{id}/positions` - Historical positions
- `GET /api/trains/{id}/events` - Train events

### Stations
- `GET /api/stations` - List stations
- `GET /api/stations/{id}` - Station details
- `GET /api/stations/{id}/reports` - Station reports
- `POST /api/stations/{id}/reports` - Create report (staff)
- `PATCH /api/stations/reports/{id}` - Update report

### Predictions
- `GET /api/predictions/eta/{train_number}` - ETA prediction
- `POST /api/predictions/eta` - Predict with options

### Weather
- `GET /api/weather/station/{id}` - Station weather
- `GET /api/weather/coordinates` - Weather by GPS
- `GET /api/weather/route/{train_id}` - Route weather

### Alerts
- `GET /api/alerts` - Active alerts
- `POST /api/alerts/{id}/acknowledge` - Acknowledge
- `POST /api/alerts/{id}/resolve` - Resolve

### Congestion
- `GET /api/congestion/network` - Network congestion
- `GET /api/congestion/section/{id}` - Section congestion
- `GET /api/congestion/station/{id}` - Station congestion

### Simulation
- `GET /api/simulation/status` - Simulation status
- `POST /api/simulation/control` - Control (start/pause/resume/stop)
- `POST /api/simulation/what-if` - What-if scenarios

### WebSocket
- `/ws/trains` - General train updates
- `/ws/train/{train_id}` - Specific train
- `/ws/control-room` - Control room feed

## Simulation Scenarios

| Scenario | Description |
|----------|-------------|
| NORMAL | Normal operations |
| CONGESTION | High train density |
| SIGNAL_DELAY | Signal failures |
| EXTENDED_HALT | Platform occupation |
| SPEED_RESTRICTION | Temporary speed limits |
| HEAVY_RAIN | Monsoon conditions |
| LOW_VISIBILITY | Fog/smog |
| PRECEDING_TRAIN_DELAY | Cascading delays |
| UNSCHEDULED_STOP | Emergency stops |
| CASCADING_DELAY | Network-wide delays |
| RECOVERY | Delay recovery |

## ML Pipeline

### Feature Categories
- **Train**: Type, route, stops
- **Temporal**: Hour, day, peak indicator
- **Running**: Speed, delay, trend
- **Section**: Historical times, variance
- **Station**: Dwell, junction, congestion
- **Network**: Nearby trains, preceding delay
- **Weather**: Temp, rain, visibility, wind

### Models
1. **Baseline**: Scheduled + current delay
2. **Statistical**: Historical section performance
3. **ML**: Gradient Boosting (XGBoost/LightGBM)

### Evaluation
- MAE, RMSE, R², Median AE
- Accuracy within ±5/10/15 minutes
- Prediction latency (target < 50ms)

## Data Sources

| Source | Type | Status |
|--------|------|--------|
| Train Positions | SIMULATION | Demo |
| Weather | WEATHER_API | Live (Open-Meteo) |
| Station Reports | USER_INPUT | Staff |
| ETA Predictions | ESTIMATED | ML |
| Congestion | SIMULATION | Computed |

**Never pretend simulation is live railway data.**

## Configuration

Key environment variables:
```env
DATABASE_URL=postgresql+asyncpg://railway:railway@localhost:5432/railway_intelligence
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
WEATHER_API_KEY=  # Optional, uses Open-Meteo by default
WEATHER_PROVIDER=open-meteo
SIMULATION_SPEED=1.0
SIMULATION_SCENARIO=normal
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/backend -v

# Frontend tests
cd frontend
npm test
```

## Deployment

```bash
# Production build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Scale simulation workers
docker compose up --scale simulator=3
```

## Security

- JWT authentication with HS256
- Password hashing with bcrypt
- Role-based access control (5 roles)
- Rate limiting on auth endpoints
- CORS configured for frontend origin
- Secure headers via FastAPI middleware
- Audit logging for all mutations
- Environment-based secrets

## Privacy

- GPS permission: Explicit opt-in
- Location: Minimal, session-only
- No personal tracking history
- Station master actions: Audited

## Project Structure

```
railpulse-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI routes
│   │   ├── core/              # Config, security, logging
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── realtime/          # WebSocket manager
│   │   ├── simulation/        # Simulation engine
│   │   ├── ml/                # ML predictor
│   │   └── database/          # DB session, migrations
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── contexts/          # React contexts
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Helpers
├── ml/                        # ML pipeline
├── simulator/                 # Standalone simulator
├── scripts/                   # DB init, seeding
├── tests/                     # Test suites
└── docs/                      # Documentation
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [ML Model](docs/ML_MODEL.md)
- [Data Pipeline](docs/DATA_PIPELINE.md)
- [Weather Integration](docs/WEATHER_INTEGRATION.md)
- [Station Reports](docs/STATION_REPORTS.md)
- [GPS Tracking](docs/GPS_TRACKING.md)
- [Real-time System](docs/REALTIME.md)
- [API Reference](docs/API.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Demo Guide](docs/DEMO_GUIDE.md)
- [SIH Features](docs/SIH_FEATURES.md)

## SIH Demo Scenario

1. **Train 12345** starts normally from New Delhi
2. Passenger searches `12345` → sees live position, speed, ETA, weather
3. **Congestion** scenario → ETA increases, alert generated
4. **Extended Halt** at Prayagraj → Auto-detected (18 min vs 5 min expected)
5. Station Master submits: "PLATFORM_OCCUPIED" → Verified → Published
6. Passenger sees: "WHY IS MY TRAIN STANDING?" + verified reason
7. ETA recalculates with reason
8. **Heavy Rain** → Weather warning, prediction interval widens
9. Train resumes → Delay recovery → ETA improves
10. Control room sees all events in real-time

## License

MIT License - Built for Smart India Hackathon

## Disclaimer

This is a demonstration platform using **SIMULATION DATA**. It does not connect to official Indian Railways systems. All train positions, delays, and predictions are simulated for demonstration purposes only.
>>>>>>> abb7873 (Initial project upload)
>>>>>>> ea4a710 (Initial)
