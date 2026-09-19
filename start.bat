@echo off
setlocal
echo ============================================
echo   RAILPULSE AI - Railway Intelligence Platform
echo   Predict every arrival. Understand every delay.
echo ============================================
echo.

echo Starting Backend (uvicorn on port 8000)...
start "RAILPULSE Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Frontend (vite on port 5173)...
start "RAILPULSE Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services started!
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo Demo accounts:
echo   passenger / passenger123  (PASSENGER)
echo   station_master / station_master123  (STATION_STAFF)
echo   supervisor / supervisor123  (SUPERVISOR)
echo   operator / operator123  (OPERATOR)
echo   admin / admin123  (ADMIN)
echo.
echo Tip: open http://localhost:5173 in your browser and log in with any account above.
pause