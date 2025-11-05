# UPI Fraud Detection System Configuration

# Decision Thresholds
FRAUD_THRESHOLDS = {
    'allow': 0.4,      # Allow if fraud_score < 0.4
    'verify': 0.7,     # Verify/OTP if 0.4 <= fraud_score < 0.7
    'block': 0.7       # Block if fraud_score >= 0.7
}

# Risk Levels
RISK_LEVELS = {
    'LOW': {'min': 0.0, 'max': 0.4, 'action': 'ALLOW', 'color': 'green'},
    'MEDIUM': {'min': 0.4, 'max': 0.7, 'action': 'VERIFY', 'color': 'orange'},
    'HIGH': {'min': 0.7, 'max': 1.0, 'action': 'BLOCK', 'color': 'red'}
}

import os

# Get the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Model Configuration
MODEL_CONFIG = {
    'model_path': os.path.join(project_root, 'models'),
    'preprocessor_path': os.path.join(project_root, 'models'),
    'confidence_threshold': 0.8  # Minimum confidence for predictions
}

# API Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': True
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': os.path.join(project_root, 'logs', 'fraud_detection.log') if os.path.exists(os.path.join(project_root, 'logs')) else 'fraud_detection.log'
}