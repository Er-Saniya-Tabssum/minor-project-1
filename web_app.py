from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import os
from datetime import datetime
import traceback
import json

# Import our fraud detection pipeline
from models.fraud_pipeline import FraudDetectionPipeline, create_sample_transaction
from config.config import API_CONFIG

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes (important for frontend)
CORS(app, origins=["*"])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize fraud detection pipeline
fraud_pipeline = None

# Statistics tracking
api_stats = {
    'total_requests': 0,
    'successful_predictions': 0,
    'failed_predictions': 0,
    'actions': {
        'ALLOW': 0,
        'VERIFY': 0,
        'BLOCK': 0
    },
    'start_time': datetime.now()
}

def initialize_pipeline():
    """Initialize the fraud detection pipeline"""
    global fraud_pipeline
    try:
        fraud_pipeline = FraudDetectionPipeline()
        if fraud_pipeline.is_loaded:
            logger.info("Fraud detection pipeline initialized successfully")
            return True
        else:
            logger.error("Failed to load fraud detection pipeline")
            return False
    except Exception as e:
        logger.error(f"Error initializing pipeline: {e}")
        return False

def update_stats(result=None, success=True):
    """Update API statistics"""
    api_stats['total_requests'] += 1
    
    if success:
        api_stats['successful_predictions'] += 1
        if result and 'action_response' in result:
            action = result['action_response']['action']
            if action in api_stats['actions']:
                api_stats['actions'][action] += 1
    else:
        api_stats['failed_predictions'] += 1

# ============= STATIC FILE SERVING =============

@app.route('/')
def serve_frontend():
    """Serve the frontend HTML file"""
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        return jsonify({
            'error': 'Frontend not found',
            'message': 'Please ensure the frontend files are in the frontend/ directory',
            'status': 'error'
        }), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    try:
        return send_from_directory('frontend', filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

# ============= API ENDPOINTS =============

@app.route('/api', methods=['GET'])
def api_info():
    """API information and available endpoints"""
    return jsonify({
        'service': 'Trustify: Securing Every UPI Payment with AI',
        'version': '1.0.0',
        'description': 'AI-powered fraud detection system for secure UPI transactions',
        'endpoints': {
            'GET /api': 'This endpoint - API information',
            'GET /api/health': 'Health check',
            'POST /api/detect-fraud': 'Single transaction fraud detection',
            'POST /api/batch-detect': 'Batch fraud detection',
            'GET /api/model-info': 'ML model information',
            'GET /api/statistics': 'API usage statistics',
            'POST /api/update-thresholds': 'Update fraud thresholds',
            'GET /api/sample-transaction': 'Get sample transaction data',
            'GET /api/test-scenarios': 'Get test scenarios',
            'GET /api/test-fraud-detection': 'Test with sample data',
            'POST /api/reset-stats': 'Reset statistics'
        },
        'documentation': 'Open http://localhost:5001 for web interface',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    uptime = datetime.now() - api_stats['start_time']
    
    return jsonify({
        'status': 'healthy',
        'service': 'Trustify: Securing Every UPI Payment with AI',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'pipeline_loaded': fraud_pipeline is not None and fraud_pipeline.is_loaded,
        'uptime_seconds': int(uptime.total_seconds()),
        'statistics': api_stats
    })

@app.route('/api/detect-fraud', methods=['POST'])
def detect_fraud():
    """
    Main fraud detection endpoint.
    
    Expects JSON payload with transaction data.
    Returns fraud detection result with action recommendation.
    """
    
    try:
        # Check if pipeline is loaded
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            update_stats(success=False)
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        # Get JSON data from request
        if not request.is_json:
            update_stats(success=False)
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'error'
            }), 400
        
        transaction_data = request.get_json()
        
        if not transaction_data:
            update_stats(success=False)
            return jsonify({
                'error': 'No transaction data provided',
                'status': 'error'
            }), 400
        
        # Add timestamp if not provided
        if 'timestamp' not in transaction_data:
            transaction_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Predict fraud
        result = fraud_pipeline.predict_fraud(transaction_data)
        
        # Update statistics
        update_stats(result, success=True)
        
        # Return result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        update_stats(success=False)
        return jsonify({
            'error': str(e),
            'status': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"Fraud detection error: {e}")
        logger.error(traceback.format_exc())
        update_stats(success=False)
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/batch-detect', methods=['POST'])
def batch_detect_fraud():
    """
    Batch fraud detection endpoint.
    
    Expects JSON array of transaction objects.
    Returns array of fraud detection results.
    """
    
    try:
        # Check if pipeline is loaded
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'error'
            }), 400
        
        transactions_data = request.get_json()
        
        if not isinstance(transactions_data, list):
            return jsonify({
                'error': 'Request must be a JSON array of transactions',
                'status': 'error'
            }), 400
        
        if len(transactions_data) == 0:
            return jsonify({
                'error': 'No transactions provided',
                'status': 'error'
            }), 400
        
        if len(transactions_data) > 100:  # Limit batch size
            return jsonify({
                'error': 'Batch size too large (max 100 transactions)',
                'status': 'error'
            }), 400
        
        # Process batch
        results = fraud_pipeline.batch_predict(transactions_data)
        
        # Update statistics for batch
        for result in results:
            update_stats(result, success='error' not in result)
        
        # Return results
        return jsonify({
            'status': 'success',
            'total_transactions': len(transactions_data),
            'results': results,
            'processing_time': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Batch fraud detection error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    """Get information about the loaded model"""
    
    try:
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        model_info = fraud_pipeline.get_model_info()
        model_info['api_statistics'] = api_stats
        
        return jsonify(model_info), 200
        
    except Exception as e:
        logger.error(f"Model info error: {e}")
        return jsonify({
            'error': 'Failed to get model information',
            'status': 'error'
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get API usage statistics"""
    
    uptime = datetime.now() - api_stats['start_time']
    
    enhanced_stats = {
        **api_stats,
        'uptime_seconds': int(uptime.total_seconds()),
        'uptime_formatted': str(uptime).split('.')[0],  # Remove microseconds
        'success_rate': (api_stats['successful_predictions'] / max(api_stats['total_requests'], 1)) * 100,
        'requests_per_minute': api_stats['total_requests'] / max(uptime.total_seconds() / 60, 1)
    }
    
    return jsonify(enhanced_stats), 200

@app.route('/api/update-thresholds', methods=['POST'])
def update_thresholds():
    """Update fraud detection thresholds"""
    
    try:
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'error'
            }), 400
        
        new_thresholds = request.get_json()
        
        if fraud_pipeline.update_thresholds(new_thresholds):
            return jsonify({
                'status': 'success',
                'message': 'Thresholds updated successfully',
                'new_thresholds': fraud_pipeline.decision_engine.get_threshold_info()
            }), 200
        else:
            return jsonify({
                'error': 'Invalid threshold values',
                'status': 'error'
            }), 400
            
    except Exception as e:
        logger.error(f"Threshold update error: {e}")
        return jsonify({
            'error': 'Failed to update thresholds',
            'status': 'error'
        }), 500

@app.route('/api/sample-transaction', methods=['GET'])
def get_sample_transaction():
    """Get a sample transaction for testing"""
    
    sample = create_sample_transaction()
    return jsonify({
        'status': 'success',
        'sample_transaction': sample,
        'description': 'Sample transaction data for testing the fraud detection API'
    }), 200

@app.route('/api/test-scenarios', methods=['GET'])
def get_test_scenarios():
    """Get predefined test scenarios"""
    
    scenarios = [
        {
            'name': 'Normal Transaction',
            'description': 'Typical legitimate transaction',
            'data': {
                'transaction_id': 'TEST_NORMAL_001',
                'sender_id': 'user123@upi',
                'receiver_id': 'merchant456@upi',
                'amount': 1500.0,
                'transaction_time': 14,
                'transaction_frequency_last_24h': 3,
                'avg_amount_last_week': 2000.0,
                'transaction_type': 'Send',
                'device_id': 'device_123',
                'os_version': 'Android_13',
                'ip_address': '192.168.1.100',
                'current_latitude': 28.6139,
                'current_longitude': 77.2090,
                'geo_distance_from_last_txn': 2.5,
                'receiver_age_days': 365,
                'receiver_fraud_reports': 0,
                'unique_senders_to_receiver': 150,
                'time_between_upi_open_and_pay': 25.0,
                'otp_entry_delay': 12.0,
                'is_unusual_hour': 0,
                'amount_deviation_from_avg': 0.25,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        {
            'name': 'Suspicious Transaction',
            'description': 'Transaction requiring verification',
            'data': {
                'transaction_id': 'TEST_SUSPICIOUS_001',
                'sender_id': 'user456@upi',
                'receiver_id': 'merchant789@upi',
                'amount': 8000.0,
                'transaction_time': 22,
                'transaction_frequency_last_24h': 5,
                'avg_amount_last_week': 2000.0,
                'transaction_type': 'Send',
                'device_id': 'device_456',
                'os_version': 'Android_12',
                'ip_address': '192.168.1.101',
                'current_latitude': 28.7139,
                'current_longitude': 77.3090,
                'geo_distance_from_last_txn': 25.0,
                'receiver_age_days': 15,
                'receiver_fraud_reports': 1,
                'unique_senders_to_receiver': 50,
                'time_between_upi_open_and_pay': 15.0,
                'otp_entry_delay': 20.0,
                'is_unusual_hour': 1,
                'amount_deviation_from_avg': 3.0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        {
            'name': 'High-Risk Fraud',
            'description': 'Likely fraudulent transaction',
            'data': {
                'transaction_id': 'TEST_FRAUD_001',
                'sender_id': 'user789@upi',
                'receiver_id': 'suspicious123@upi',
                'amount': 50000.0,
                'transaction_time': 3,
                'transaction_frequency_last_24h': 15,
                'avg_amount_last_week': 2000.0,
                'transaction_type': 'Send',
                'device_id': 'device_unknown',
                'os_version': 'Android_13',
                'ip_address': '192.168.1.200',
                'current_latitude': 19.0760,
                'current_longitude': 72.8777,
                'geo_distance_from_last_txn': 500.0,
                'receiver_age_days': 2,
                'receiver_fraud_reports': 8,
                'unique_senders_to_receiver': 5,
                'time_between_upi_open_and_pay': 3.0,
                'otp_entry_delay': 60.0,
                'is_unusual_hour': 1,
                'amount_deviation_from_avg': 24.0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    ]
    
    return jsonify({
        'status': 'success',
        'scenarios': scenarios,
        'total_scenarios': len(scenarios)
    }), 200

@app.route('/api/test-fraud-detection', methods=['GET'])
def test_fraud_detection():
    """Test endpoint that runs fraud detection on sample data"""
    
    try:
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        # Get test scenarios
        response = get_test_scenarios()
        scenarios_data = response[0].get_json()
        
        test_results = []
        
        for scenario in scenarios_data['scenarios']:
            try:
                result = fraud_pipeline.predict_fraud(scenario['data'])
                test_results.append({
                    'scenario_name': scenario['name'],
                    'scenario_description': scenario['description'],
                    'result': result
                })
                
                # Update stats
                update_stats(result, success=True)
                
            except Exception as e:
                test_results.append({
                    'scenario_name': scenario['name'],
                    'scenario_description': scenario['description'],
                    'error': str(e)
                })
                update_stats(success=False)
        
        return jsonify({
            'status': 'success',
            'test_results': test_results,
            'summary': {
                'total_tests': len(test_results),
                'successful_tests': len([r for r in test_results if 'error' not in r])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Test fraud detection error: {e}")
        return jsonify({
            'error': 'Test failed',
            'status': 'error',
            'details': str(e)
        }), 500

@app.route('/api/reset-stats', methods=['POST'])
def reset_statistics():
    """Reset API statistics"""
    
    global api_stats
    api_stats = {
        'total_requests': 0,
        'successful_predictions': 0,
        'failed_predictions': 0,
        'actions': {
            'ALLOW': 0,
            'VERIFY': 0,
            'BLOCK': 0
        },
        'start_time': datetime.now()
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Statistics reset successfully'
    }), 200

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'available_endpoints': [
            'GET /',
            'GET /api/health',
            'POST /api/detect-fraud',
            'POST /api/batch-detect',
            'GET /api/model-info',
            'GET /api/statistics',
            'POST /api/update-thresholds',
            'GET /api/sample-transaction',
            'GET /api/test-scenarios',
            'GET /api/test-fraud-detection',
            'POST /api/reset-stats'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'status': 'error'
    }), 405

if __name__ == '__main__':
    
    print("=== Trustify: Securing Every UPI Payment with AI ===")
    print("Initializing fraud detection pipeline...")
    
    # Initialize the pipeline
    if initialize_pipeline():
        print("✅ Pipeline loaded successfully!")
        print(f"🚀 Starting web application on http://{API_CONFIG['host']}:{API_CONFIG['port']}")
        print("\nAvailable endpoints:")
        print("  GET  /                     - Web Interface")
        print("  GET  /api/health           - Health check")
        print("  POST /api/detect-fraud     - Single fraud detection")
        print("  POST /api/batch-detect     - Batch fraud detection")
        print("  GET  /api/model-info       - Model information")
        print("  GET  /api/statistics       - API statistics")
        print("  POST /api/update-thresholds - Update thresholds")
        print("  GET  /api/sample-transaction - Get sample data")
        print("  GET  /api/test-scenarios   - Get test scenarios")
        print("  GET  /api/test-fraud-detection - Test with sample data")
        print("  POST /api/reset-stats      - Reset statistics")
        print("\n" + "="*60)
        print("🌐 Open http://localhost:5001 in your browser to use the web interface!")
        print("="*60)
        
        # Start the Flask app
        app.run(
            host=API_CONFIG['host'],
            port=API_CONFIG['port'],
            debug=API_CONFIG['debug']
        )
    else:
        print("❌ Failed to initialize fraud detection pipeline!")
        print("Please check that the model files exist and are properly trained.")