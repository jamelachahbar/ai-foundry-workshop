@echo off
echo =====================================================
echo FinOps Expert UI - Debug Startup Script
echo =====================================================
echo.

:: Check if Python is installed
echo [1/4] Checking for Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python and try again.
    goto :error
) else (
    echo [SUCCESS] Python is installed.
)

:: Check if pip is installed
echo [2/4] Checking for pip...
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed or not in PATH!
    goto :error
) else (
    echo [SUCCESS] pip is installed.
)

:: Run API test script
echo [3/4] Testing API before starting...
cd %~dp0
python test-api.py
echo.

:: Ask user if they want to proceed
set /p continue="Continue with starting the application? (Y/N): "
if /i "%continue%" neq "Y" goto :end

:: Start both servers in debug mode
echo [4/4] Starting servers in debug mode...
echo.
echo Starting Backend server (will open in a new window)...
start cmd /k "cd backend && python test_server.py"

:: Wait for backend to initialize
echo Waiting for backend to initialize (5 seconds)...
timeout /t 5 /nobreak > nul

:: Start Frontend
echo Starting Frontend server (will open in a new window)...
start cmd /k "cd frontend && npm run dev"

echo.
echo =====================================================
echo Both servers are running in debug mode.
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://127.0.0.1:8000
echo.
echo You can test the API with: python test-api.py
echo.
echo Press any key to close this window...
echo =====================================================
goto :end

:error
echo.
echo [ERROR] Setup failed. Please check the errors above.
pause

:end
echo.
pause 