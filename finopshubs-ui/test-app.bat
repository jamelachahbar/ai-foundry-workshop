@echo off
echo ===================================
echo FinOpsHubs UI - Debug Mode
echo ===================================
echo.

echo Running backend server with debug logging...
echo.

cd backend

REM Set environment variables for debugging
set PYTHONPATH=%CD%
set DEBUG=1

echo Current directory: %CD%
echo PYTHONPATH: %PYTHONPATH%
echo.

echo FinOps Expert module path:
if exist finops_expert_with_bing_grounding.py (
    echo [FOUND] %CD%\finops_expert_with_bing_grounding.py
) else (
    echo [NOT FOUND] %CD%\finops_expert_with_bing_grounding.py
)

if exist finops_expert_simplified.py (
    echo [FOUND] %CD%\finops_expert_simplified.py
) else (
    echo [NOT FOUND] %CD%\finops_expert_simplified.py
)
echo.

echo Installing required dependencies...
pip install uvicorn fastapi

echo.
echo Starting FastAPI backend server...
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level debug

echo.
echo Server stopped.
pause