@echo off
echo ========================================
echo Starting ML Service for Suspicious Behavior Detection
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if model file exists
if not exist "models\best.pt" (
    echo WARNING: Model file not found: models\best.pt
    echo Please ensure the trained model is in the models folder
    echo.
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import ultralytics" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
)

echo.
echo Starting ML Service on port 5001...
echo Press Ctrl+C to stop the service
echo.
echo ========================================
echo.

python app.py

pause

