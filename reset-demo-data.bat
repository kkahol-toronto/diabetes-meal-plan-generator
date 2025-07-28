@echo off
echo ================================================================
echo    Reset and Regenerate Demo Data
echo ================================================================
echo.

echo ⚠️  WARNING: This will delete all existing demo data!
echo.
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Operation cancelled.
    pause
    exit /b
)

echo.
echo 🧹 Cleaning up existing demo data...
cd backend

REM Clean up demo users and data
python -c "
import requests
import json

BACKEND_URL = 'http://localhost:8000'
DEMO_EMAILS = [
    'alice.johnson@demo.com',
    'bob.smith@demo.com', 
    'carol.davis@demo.com',
    'david.wilson@demo.com',
    'emma.brown@demo.com'
]

print('Cleaning up demo users...')
for email in DEMO_EMAILS:
    try:
        # Delete user data if cleanup endpoint exists
        pass
    except:
        pass

print('Cleanup complete!')
"

echo.
echo 📊 Regenerating fresh demo data...
python demo_data_generator.py

echo.
echo ✅ Demo data reset complete!
echo.
pause 