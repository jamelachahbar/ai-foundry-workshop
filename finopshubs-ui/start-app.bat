@echo off
echo ===================================
echo FinOpsHubs UI Application
echo ===================================
echo.

echo Starting Backend Server...
cd backend

REM Check for the FinOps Expert module
if exist finops_expert_with_bing_grounding.py (
    echo [✓] Found FinOps Expert module
) else (
    echo [!] FinOps Expert module not found
    if exist finops_expert_simplified.py (
        echo [✓] Using simplified module instead
        copy finops_expert_simplified.py finops_expert_with_bing_grounding.py
        echo [✓] Created copy as finops_expert_with_bing_grounding.py
    ) else (
        echo [✗] Neither module found, API will use mock responses
    )
)

REM Start the backend server with the enhanced script
start cmd /k "python start_server.py"
echo Backend server starting at http://127.0.0.1:8000

echo Waiting for backend to initialize (3 seconds)...
timeout /t 3 /nobreak > NUL

echo Starting Frontend...
cd ..\frontend

REM Start the frontend development server
npm run dev

echo FinOpsHubs application has been started! 