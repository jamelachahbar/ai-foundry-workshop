@echo off
echo ========================================
echo Starting FinOps Hubs Application...
echo ========================================
echo.

echo Setting MOCK_MODE=false for real API usage
set MOCK_MODE=false

echo Starting Backend Server...
start cmd /k "cd finopshubs-ui\backend && python main.py"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd finopshubs-ui\frontend && npm run dev"

echo.
echo ========================================
echo Application started! 
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo New Features:
echo - Link verification to ensure sources are accessible
echo - Agent thoughts are now available (click "Show Agent Thoughts")
echo - Invalid links are marked with warning icons
echo - Enhanced markdown rendering (tables, code blocks, and lists)
echo - Better formatting of technical content similar to ChatGPT
echo.
echo ========================================
echo Troubleshooting Guide:
echo ========================================
echo If you see 404 errors or "Failed to fetch" errors:
echo 1. Make sure the backend server is running
echo 2. Check that finops_expert_with_bing_grounding.py exists in the correct location
echo 3. Try testing the API with: python finopshubs-ui\test-endpoint.py
echo 4. Check file locations with: python finopshubs-ui\check-files.py
echo.
echo If you see "Sorry, there was an error processing your request":
echo 1. Check the backend logs for specific error messages
echo 2. Verify that MOCK_MODE=true is set correctly for development
echo.
echo ========================================
echo Press any key to close this window...
pause > nul 