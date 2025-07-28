@echo off
echo ================================================================
echo    Diabetes Meal Plan Generator - System Check
echo ================================================================
echo.

echo 🔍 Checking system requirements...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.11+
    goto :error
) else (
    echo ✅ Python installed
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found! Please install Node.js
    goto :error
) else (
    echo ✅ Node.js installed
)

REM Check backend directory
if not exist "backend\main.py" (
    echo ❌ Backend main.py not found!
    goto :error
) else (
    echo ✅ Backend files found
)

REM Check frontend directory
if not exist "frontend\package.json" (
    echo ❌ Frontend package.json not found!
    goto :error
) else (
    echo ✅ Frontend files found
)

REM Check backend dependencies
echo.
echo 🔍 Checking backend dependencies...
cd backend
python -c "import fastapi, openai, azure" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Backend dependencies missing. Installing...
    pip install -r requirements.txt
) else (
    echo ✅ Backend dependencies OK
)

REM Check frontend dependencies
echo.
echo 🔍 Checking frontend dependencies...
cd ..\frontend
if not exist "node_modules" (
    echo ⚠️  Frontend dependencies missing. Installing...
    npm install
) else (
    echo ✅ Frontend dependencies OK
)

cd ..

echo.
echo ================================================================
echo ✅ SYSTEM CHECK PASSED!
echo ================================================================
echo.
echo 🎯 Your system is ready for the demo!
echo.
echo Next steps:
echo 1. Run 'quick-demo-setup.bat' to start everything
echo 2. Follow 'DEMO_INSTRUCTIONS.md' for the presentation
echo.
goto :end

:error
echo.
echo ================================================================
echo ❌ SYSTEM CHECK FAILED!
echo ================================================================
echo.
echo Please fix the issues above before running the demo.
echo.

:end
pause 