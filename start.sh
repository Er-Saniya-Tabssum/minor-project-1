#!/bin/bash

# UPI Fraud Detection System Startup Script

echo "🔒 UPI Fraud Detection System - Startup Script"
echo "=============================================="

# Set environment variables
export PYTHONPATH="/Users/deepak/Downloads/project/upi_fraud_detection"

# Function to check if Python3 is available
check_python() {
    if command -v python3 &> /dev/null; then
        echo "✅ Python3 found: $(python3 --version)"
        return 0
    else
        echo "❌ Python3 not found. Please install Python 3.9+"
        return 1
    fi
}

# Function to check if required packages are installed
check_dependencies() {
    echo "📦 Checking dependencies..."
    
    python3 -c "
import sys
required_packages = ['flask', 'pandas', 'numpy', 'xgboost', 'joblib']
missing_packages = []

for package in required_packages:
    try:
        if package == 'flask':
            import flask
        elif package == 'pandas':
            import pandas
        elif package == 'numpy':
            import numpy
        elif package == 'xgboost':
            import xgboost
        elif package == 'joblib':
            import joblib
    except ImportError:
        missing_packages.append(package)

# Check scikit-learn separately
try:
    import sklearn
except ImportError:
    missing_packages.append('scikit-learn')

# Check flask-cors separately
try:
    import flask_cors
except ImportError:
    missing_packages.append('flask-cors')

if missing_packages:
    print(f'❌ Missing packages: {missing_packages}')
    print('Please run: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ All dependencies found')
"
    
    return $?
}

# Function to check if model files exist
check_models() {
    echo "🤖 Checking model files..."
    
    MODEL_DIR="/Users/deepak/Downloads/project/upi_fraud_detection/models"
    DATA_DIR="/Users/deepak/Downloads/project/upi_fraud_detection/data"
    
    if [ ! -f "$MODEL_DIR/fraud_detection_model.pkl" ]; then
        echo "❌ Model not found. Training model..."
        cd "/Users/deepak/Downloads/project/upi_fraud_detection"
        
        # Generate data if not exists
        if [ ! -f "$DATA_DIR/upi_transactions.csv" ]; then
            echo "📊 Generating training data..."
            PYTHONPATH="$PYTHONPATH" python3 data/generate_dataset.py
        fi
        
        # Preprocess data if not exists
        if [ ! -f "$DATA_DIR/X_train_scaled.npy" ]; then
            echo "🔧 Preprocessing data..."
            PYTHONPATH="$PYTHONPATH" python3 data/preprocess_data.py
        fi
        
        # Train model
        echo "🎯 Training model..."
        PYTHONPATH="$PYTHONPATH" python3 models/train_model.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Model trained successfully"
        else
            echo "❌ Model training failed"
            return 1
        fi
    else
        echo "✅ Model files found"
    fi
    
    return 0
}

# Function to start the web application
start_app() {
    echo "🚀 Starting UPI Fraud Detection Web Application..."
    echo ""
    echo "Opening in browser automatically..."
    echo "If browser doesn't open, navigate to: http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop the application"
    echo "=============================================="
    echo ""
    
    # Change to project directory
    cd "/Users/deepak/Downloads/project/upi_fraud_detection"
    
    # Open browser in background (macOS)
    if command -v open &> /dev/null; then
        sleep 3 && open "http://localhost:5000" &
    fi
    
    # Start the web application
    PYTHONPATH="$PYTHONPATH" python3 web_app.py
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start     Start the web application (default)"
    echo "  check     Check system requirements only"
    echo "  train     Train/retrain the model"
    echo "  demo      Run the demo script"
    echo "  test      Run tests"
    echo "  help      Show this help message"
    echo ""
}

# Function to run demo
run_demo() {
    echo "🎮 Running fraud detection demo..."
    cd "/Users/deepak/Downloads/project/upi_fraud_detection"
    echo "n" | PYTHONPATH="$PYTHONPATH" python3 demo.py
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    cd "/Users/deepak/Downloads/project/upi_fraud_detection"
    PYTHONPATH="$PYTHONPATH" python3 tests/test_fraud_detection.py
}

# Function to train model
train_model() {
    echo "🎯 Training/Retraining model..."
    cd "/Users/deepak/Downloads/project/upi_fraud_detection"
    
    # Generate fresh data
    echo "📊 Generating fresh training data..."
    PYTHONPATH="$PYTHONPATH" python3 data/generate_dataset.py
    
    # Preprocess data
    echo "🔧 Preprocessing data..."
    PYTHONPATH="$PYTHONPATH" python3 data/preprocess_data.py
    
    # Train model
    echo "🎯 Training model..."
    PYTHONPATH="$PYTHONPATH" python3 models/train_model.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Model training completed successfully"
    else
        echo "❌ Model training failed"
        return 1
    fi
}

# Main execution
main() {
    local command="${1:-start}"
    
    case "$command" in
        "start")
            if check_python && check_dependencies && check_models; then
                start_app
            else
                echo "❌ Startup checks failed. Please fix the issues above."
                exit 1
            fi
            ;;
        "check")
            echo "🔍 Running system checks..."
            check_python && check_dependencies && check_models
            if [ $? -eq 0 ]; then
                echo "✅ All checks passed. System is ready!"
            else
                echo "❌ Some checks failed. Please fix the issues above."
                exit 1
            fi
            ;;
        "train")
            if check_python && check_dependencies; then
                train_model
            else
                echo "❌ Prerequisites not met for training."
                exit 1
            fi
            ;;
        "demo")
            if check_python && check_dependencies && check_models; then
                run_demo
            else
                echo "❌ Prerequisites not met for demo."
                exit 1
            fi
            ;;
        "test")
            if check_python && check_dependencies; then
                run_tests
            else
                echo "❌ Prerequisites not met for testing."
                exit 1
            fi
            ;;
        "help")
            show_usage
            ;;
        *)
            echo "❌ Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"