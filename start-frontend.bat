@echo off
echo Starting Diabetes Meal Plan Generator Frontend...
echo.

REM Change to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    echo.
)

REM Start the frontend server
echo Starting React development server on http://localhost:3000
echo The browser should open automatically
echo Press Ctrl+C to stop the server
echo.
npm start

pause 