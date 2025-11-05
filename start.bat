@echo off
REM UPI Fraud Detection System Startup Script for Windows

echo 🔒 UPI Fraud Detection System - Windows Startup Script
echo ==============================================

REM Set environment variables
set PYTHONPATH=%~dp0

REM Function to check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

REM Check if in correct directory
if not exist "web_app.py" (
    echo ❌ Please run this script from the upi_fraud_detection directory
    pause
    exit /b 1
)

REM Check dependencies
echo 📦 Checking dependencies...
python -c "import flask, flask_cors, pandas, numpy, sklearn, xgboost, joblib" 2>nul
if errorlevel 1 (
    echo ❌ Missing dependencies. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo ✅ All dependencies found
)

REM Check if model exists
if not exist "models\fraud_detection_model.pkl" (
    echo ❌ Model not found. Training model...
    
    REM Generate data
    if not exist "data\upi_transactions.csv" (
        echo 📊 Generating training data...
        python data\generate_dataset.py
    )
    
    REM Preprocess data
    if not exist "data\X_train_scaled.npy" (
        echo 🔧 Preprocessing data...
        python data\preprocess_data.py
    )
    
    REM Train model
    echo 🎯 Training model...
    python models\train_model.py
    
    if errorlevel 1 (
        echo ❌ Model training failed
        pause
        exit /b 1
    ) else (
        echo ✅ Model trained successfully
    )
) else (
    echo ✅ Model files found
)

REM Start the application
echo 🚀 Starting UPI Fraud Detection Web Application...
echo.
echo Opening in browser automatically...
echo If browser doesn't open, navigate to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo ==============================================
echo.

REM Open browser
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Start the web application
python web_app.py

pause