@echo off
echo Starting FinOps Hubs Application...
echo.

echo Setting MOCK_MODE=true for development
set MOCK_MODE=true

echo Starting Backend Server...
start cmd /k "cd finopshubs-ui\backend && python main.py"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd finopshubs-ui\frontend && npm run dev"

echo.
echo Application started! 
echo.
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
echo.
echo To test the FinOps Expert API:
echo Run: python finopshubs-ui\test-finops-expert.py
echo.
echo Press any key to close this window...
pause > nul 