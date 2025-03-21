@echo off
echo Testing FinOps Expert Module...
cd finopshubs-ui\backend
python test_finops_expert.py
echo.
echo Test complete. Press any key to exit...
pause > nul 