#!/usr/bin/env python3
"""Generate a 'How to Run' PDF guide for the RAILPULSE AI platform."""

from fpdf import FPDF

OUT = "docs/HOW_TO_RUN.pdf"

NAVY = (15, 30, 60)
BLUE = (37, 99, 235)
GRAY = (75, 85, 99)
LIGHT = (241, 245, 249)
GREEN = (5, 122, 85)
WHITE = (255, 255, 255)


class Pdf(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "RAILPULSE AI - How to Run", align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, "Built for Smart India Hackathon (SIH) - Demonstration Platform", align="C")


def title(p):
    p.add_page()
    p.set_fill_color(*NAVY)
    p.rect(0, 0, 210, 50, "F")
    p.set_font("Helvetica", "B", 22)
    p.set_text_color(*WHITE)
    p.set_xy(10, 14)
    p.cell(0, 10, "RAILPULSE AI", align="C", new_x="LMARGIN", new_y="NEXT")
    p.set_font("Helvetica", "", 12)
    p.cell(0, 8, "How to Run the Program - Step-by-Step Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    p.set_xy(10, 48)
    p.set_text_color(*GRAY)
    p.set_font("Helvetica", "I", 10)
    p.cell(0, 8, "AI-Powered Real-Time ETA Prediction, Train Tracking and Railway Operations Intelligence",
           align="C", new_x="LMARGIN", new_y="NEXT")
    p.set_text_color(0, 0, 0)


def h1(p, text):
    p.ln(4)
    p.set_font("Helvetica", "B", 15)
    p.set_text_color(*NAVY)
    p.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
    p.set_draw_color(*BLUE)
    p.set_line_width(0.6)
    p.line(10, p.get_y(), 200, p.get_y())
    p.ln(3)


def h2(p, text):
    p.ln(2)
    p.set_font("Helvetica", "B", 12)
    p.set_text_color(*BLUE)
    p.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    p.ln(1)


def body(p, text):
    p.set_font("Helvetica", "", 10.5)
    p.set_text_color(*GRAY)
    p.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")
    p.ln(1)


def bullet(p, text):
    p.set_font("Helvetica", "", 10.5)
    p.set_text_color(*GRAY)
    p.multi_cell(0, 5.5, "-  " + text, new_x="LMARGIN", new_y="NEXT")
    p.ln(0.5)


def code(p, block):
    lines = block.strip("\n").split("\n")
    p.set_font("Courier", "", 9.5)
    width = max(p.get_string_width(l) for l in lines) + 8
    x = 16
    y0 = p.get_y()
    h = len(lines) * 5 + 6
    if y0 + h > 285:
        p.add_page()
        y0 = p.get_y()
    p.set_fill_color(*LIGHT)
    p.rect(x - 3, y0, width + 2, h, "F")
    p.set_draw_color(*BLUE)
    p.rect(x - 3, y0, width + 2, h, "D")
    p.set_text_color(0, 0, 0)
    p.set_xy(x, y0 + 3)
    for l in lines:
        p.cell(0, 5, l, new_x="LMARGIN", new_y="NEXT")
        p.set_x(x)
    p.set_y(y0 + h + 4)
    p.set_text_color(*GRAY)


def table(p, headers, rows, widths):
    col_w = widths or [40] * len(headers)
    p.set_font("Helvetica", "B", 10)
    p.set_fill_color(*NAVY)
    p.set_text_color(*WHITE)
    for i, h in enumerate(headers):
        p.cell(col_w[i], 7, f"  {h}", "B", fill=True)
    p.ln()
    p.set_font("Helvetica", "", 9.5)
    p.set_text_color(*GRAY)
    for r in rows:
        for i, c in enumerate(r):
            p.cell(col_w[i], 6.5, f"  {c}", border="B")
        p.ln()
    p.ln(2)


p = Pdf(orientation="P", unit="mm", format="A4")
p.set_auto_page_break(auto=True, margin=18)

# ---------------- Title page ----------------
title(p)

body(p, "This guide explains how to set up and run the RAILPULSE AI platform on a "
        "local development machine. Two options are available: Docker Compose (quick start) "
        "and a manual development setup (backend + frontend).")

# ---------------- Prerequisites ----------------
h1(p, "1. Prerequisites")
bullet(p, "Git for cloning the repository and version control.")
bullet(p, "Docker & Docker Compose (only for the Docker Quick Start option).")
bullet(p, "Python 3.12 or later for the backend (manual option).")
bullet(p, "Node.js 18+ and npm 9+ for the frontend (manual option).")
bullet(p, "A terminal / command prompt with access to the project directory.")

# ---------------- Option A Docker ----------------
h1(p, "2. Option A - Docker Quick Start (Recommended)")
body(p, "The containerized approach starts the backend, frontend, database, cache and the simulation "
        "engine with a single command.")
h2(p, "2.1 Setup")
code(p, "# 1. Copy the environment template (first time only)\n"
        "cp .env.example .env\n\n"
        "# Or on Windows (PowerShell):\n"
        "Copy-Item .env.example .env")
h2(p, "2.2 Start all services")
code(p, "docker compose up --build")
h2(p, "2.3 Behind the scenes")
bullets = [
    "PostgreSQL and Redis are started as data-layer services.",
    "Backend (FastAPI) runs migrations (alembic upgrade head) before serving the API.",
    "Frontend (Vite dev server) is served for hot-reload development.",
    "Simulator engine runs live train position simulation.",
]
for b in bullets:
    bullet(p, b)
h2(p, "2.4 Access")
table(p, ["Service", "URL"], [
    ["Frontend UI", "http://localhost:5173"],
    ["Backend API", "http://localhost:8000"],
    ["API Docs (Swagger)", "http://localhost:8000/docs"],
], [60, 90])
h2(p, "2.5 Stop all services")
code(p, "docker compose down")

# ---------------- Option B Manual ----------------
p.add_page()
h1(p, "3. Option B - Manual Development Setup")
body(p, "Use when Docker is not available or you prefer running components natively on your machine.")

h2(p, "3.1 Backend")
code(p, "# From the project ROOT (packaging files are here, not in backend/)\n"
        "pip install -e \".[dev]\"     # or: pip install -e . --no-build-isolation\n"
        "alembic upgrade head          # no-op if no migration files exist\n"
        "python scripts/seed.py        # seeds demo users/trains/stations\n"
        "python -m uvicorn backend.app.main:app --reload")

h2(p, "3.2 Frontend (second terminal)")
code(p, "cd frontend\n"
        "npm install\n"
        "npm run dev")

h2(p, "3.3 Access")
table(p, ["Service", "URL"], [
    ["Frontend UI", "http://localhost:5173"],
    ["Backend API", "http://localhost:8000"],
    ["API Docs (Swagger)", "http://localhost:8000/docs"],
], [60, 90])

# ---------------- Demo Credentials ----------------
h1(p, "4. Demo Login Credentials")
table(p, ["Role", "Username", "Password"], [
    ["Admin", "admin", "admin123"],
    ["Operator", "operator", "operator123"],
    ["Supervisor", "supervisor", "supervisor123"],
    ["Station Master", "station_master", "station123"],
    ["Passenger", "passenger", "passenger123"],
], [45, 45, 45])

# ---------------- Environment Notes ----------------
h1(p, "5. Environment & Configuration")
body(p, "The .env file controls key settings. The default development database is SQLite, so no "
        "external database server is required in manual mode.")
code(p, "DATABASE_URL=sqlite+aiosqlite:///./railway.db\n"
        "REDIS_URL=redis://localhost:6379/0\n"
        "SECRET_KEY=your-secret-key\n"
        "WEATHER_PROVIDER=open-meteo\n"
        "SIMULATION_SPEED=1.0\n"
        "SIMULATION_SCENARIO=NORMAL\n"
        "VITE_API_URL=http://localhost:8000\n"
        "VITE_WS_URL=ws://localhost:8000")
body(p, "Note: simulation data is used for demonstration only. The platform never pretends "
        "simulated positions are live railway data.")

# ---------------- Troubleshooting ----------------
h1(p, "6. Troubleshooting")
troubles = [
    ("Cannot pip install from the backend/ folder",
     "The pyproject.toml lives at the project root. Run pip install -e \".[dev]\" from the parent\n(project root) directory, not from backend/."),
    ("alembic: ModuleNotFoundError: No module named 'backend'",
     "The editable install produced an empty package map because 'backend', 'ml' and 'simulator' are\nnamespace packages (no __init__.py). Ensure pyproject.toml has:\n[tool.setuptools.packages.find]\nwhere = [\".\"]\ninclude = [\"backend*\", \"ml*\", \"simulator*\"]\nnamespaces = true\nthen reinstall with: pip install -e . --no-build-isolation"),
    ("alembic: 'backend' import fails when run from backend/",
     "Always run alembic from the project ROOT directory, not from backend/ - alembic reads its\nconfiguration from the root's pyproject.toml (script_location = backend/app/database/migrations)."),
    ("alembic: alembic.ini doesn't exist / No 'script_location' key",
     "Configuration is stored in pyproject.toml under [tool.alembic]. Run from the project root.\nNo alembic.ini is required."),
    ("Login returns 500 Internal Server Error",
     "passlib 1.7.4 is incompatible with bcrypt 5.x. Downgrade to the last compatible version:\npip install \"bcrypt==4.0.1\""),
    ("Simulation engine: 'normal' is not a valid SimulationScenario",
     "The config default was lowercase 'normal' but the enum requires uppercase 'NORMAL'. Fixed in\nbackend/app/core/config.py; scenario parsing in the engine is now case-insensitive."),
    ("Frontend fails with 'Cannot find module caniuse-lite'",
     "Reinstall frontend dependencies:\nrm -rf node_modules package-lock.json && npm install\n(Windows/PowerShell: Remove-Item -Recurse -Force node_modules)"),
    ("Frontend fails with 'rollup-win32-x64-msvc ... is not a valid Win32 application'",
     "The native Rollup binary is corrupted. Delete node_modules and package-lock.json, then run\nnpm install again in the frontend folder."),
    ("Frontend shows a Babel 'Duplicate declaration' overlay",
     "There is a redundant import in the offending file (e.g. Settings.tsx). Remove the duplicate import and Vite hot-reloads automatically."),
    ("Backend does not start on port 8000",
     "Another process may be using the port. Check with:\nnetstat -ano | findstr :8000\nor run uvicorn on another port: uvicorn app.main:app --port 8001"),
    ("Database tables missing",
     "Run migrations and seed data:\nalembic upgrade head\npython scripts/seed.py"),
    ("Weather data unavailable",
     "The default provider is Open-Meteo (no API key needed). If using OpenWeatherMap, set\nWEATHER_PROVIDER=openweathermap and provide WEATHER_API_KEY."),
]
for title_, detail in troubles:
    h2(p, title_)
    body(p, detail)

# ---------------- Useful Commands ----------------
h1(p, "7. Useful Commands")
table(p, ["Task", "Command"], [
    ["Run backend tests", "cd backend && pytest tests/backend -v"],
    ["Run frontend tests", "cd frontend && npm test"],
    ["Run frontend linter", "cd frontend && npm run lint"],
    ["Production build", "cd frontend && npm run build"],
    ["Prod deployment", "docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d"],
    ["Scale simulators", "docker compose up --scale simulator=3"],
], [55, 105])

# ---------------- Verification Check ----------------
p.add_page()
h1(p, "8. Verifying Everything Works")
bullet(p, "Open http://localhost:5173 in a browser. The passenger UI should load.")
bullet(p, "Open http://localhost:8000/docs - Swagger UI should render with all API routes.")
bullet(p, "Search for train 12345 in the passenger UI to see live position, speed, ETA and weather.")
bullet(p, "Log in as station_master / station123 to submit and verify delay reports.")
bullet(p, "Log in as admin / admin123 to access the Control Room and view congestion + alerts.")
bullet(p, "Run the API test suite:  python test_all_apis.py")

p.output(OUT)
print(f"PDF created: {OUT}")