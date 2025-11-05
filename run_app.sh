#!/bin/bash

# UPI Fraud Detection - Simple Run Script
echo "🚀 Starting UPI Fraud Detection System..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: web_app.py not found!"
    echo "Please run this script from the upi_fraud_detection directory"
    exit 1
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    exit 1
fi

echo "✅ Python 3 found"

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, pandas, numpy, xgboost, sklearn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All dependencies found"
else
    echo "❌ Some dependencies missing. Installing..."
    pip3 install flask pandas numpy xgboost scikit-learn flask-cors
fi

# Kill any existing process on port 5001
echo "🔧 Cleaning up existing processes..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

echo ""
echo "🌟 Starting UPI Fraud Detection Web Application..."
echo "📱 Frontend + Backend + ML Model all connected"
echo ""
echo "🔗 Once started, open: http://localhost:5001"
echo "⚡ Press Ctrl+C to stop the application"
echo ""
echo "=========================================="

# Start the application
python3 web_app.py