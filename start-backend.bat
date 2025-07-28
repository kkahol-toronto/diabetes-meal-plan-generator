@echo off
echo Starting Diabetes Meal Plan Generator Backend...
echo.

REM Change to backend directory
cd backend

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using global Python...
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found in backend directory!
    echo Please ensure you have configured your environment variables.
    echo.
)

REM Start the backend server
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python main.py

pause 