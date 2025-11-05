from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from datetime import datetime
import traceback

# Import our fraud detection pipeline
from models.fraud_pipeline import FraudDetectionPipeline, create_sample_transaction
from config.config import API_CONFIG

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize fraud detection pipeline
fraud_pipeline = None

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

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'UPI Fraud Detection API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'pipeline_loaded': fraud_pipeline is not None and fraud_pipeline.is_loaded
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
        
        transaction_data = request.get_json()
        
        if not transaction_data:
            return jsonify({
                'error': 'No transaction data provided',
                'status': 'error'
            }), 400
        
        # Add timestamp if not provided
        if 'timestamp' not in transaction_data:
            transaction_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Predict fraud
        result = fraud_pipeline.predict_fraud(transaction_data)
        
        # Return result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"Fraud detection error: {e}")
        logger.error(traceback.format_exc())
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
        return jsonify(model_info), 200
        
    except Exception as e:
        logger.error(f"Model info error: {e}")
        return jsonify({
            'error': 'Failed to get model information',
            'status': 'error'
        }), 500

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

@app.route('/api/test-fraud-detection', methods=['GET'])
def test_fraud_detection():
    """Test endpoint that runs fraud detection on sample data"""
    
    try:
        if not fraud_pipeline or not fraud_pipeline.is_loaded:
            return jsonify({
                'error': 'Fraud detection service not available',
                'status': 'error'
            }), 503
        
        # Create sample transactions
        normal_transaction = create_sample_transaction()
        
        # High-risk transaction
        high_risk_transaction = create_sample_transaction()
        high_risk_transaction.update({
            'transaction_id': 'TEST_HIGH_RISK',
            'amount': 50000.0,
            'transaction_time': 2,
            'receiver_age_days': 3,
            'receiver_fraud_reports': 8,
            'geo_distance_from_last_txn': 500,
            'is_unusual_hour': 1
        })
        
        # Process both transactions
        normal_result = fraud_pipeline.predict_fraud(normal_transaction)
        high_risk_result = fraud_pipeline.predict_fraud(high_risk_transaction)
        
        return jsonify({
            'status': 'success',
            'test_results': {
                'normal_transaction': normal_result,
                'high_risk_transaction': high_risk_result
            },
            'summary': {
                'normal_action': normal_result['action_response']['action'],
                'normal_score': normal_result['fraud_detection']['fraud_score'],
                'high_risk_action': high_risk_result['action_response']['action'],
                'high_risk_score': high_risk_result['fraud_detection']['fraud_score']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Test fraud detection error: {e}")
        return jsonify({
            'error': 'Test failed',
            'status': 'error',
            'details': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'available_endpoints': [
            'GET /',
            'POST /api/detect-fraud',
            'POST /api/batch-detect',
            'GET /api/model-info',
            'POST /api/update-thresholds',
            'GET /api/sample-transaction',
            'GET /api/test-fraud-detection'
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

if __name__ == '__main__':
    
    print("=== UPI Fraud Detection API ===")
    print("Initializing fraud detection pipeline...")
    
    # Initialize the pipeline
    if initialize_pipeline():
        print("✅ Pipeline loaded successfully!")
        print(f"🚀 Starting API server on {API_CONFIG['host']}:{API_CONFIG['port']}")
        print("\nAvailable endpoints:")
        print("  GET  /                     - Health check")
        print("  POST /api/detect-fraud     - Single fraud detection")
        print("  POST /api/batch-detect     - Batch fraud detection")
        print("  GET  /api/model-info       - Model information")
        print("  POST /api/update-thresholds - Update thresholds")
        print("  GET  /api/sample-transaction - Get sample data")
        print("  GET  /api/test-fraud-detection - Test with sample data")
        print("\n" + "="*50)
        
        # Start the Flask app
        app.run(
            host=API_CONFIG['host'],
            port=API_CONFIG['port'],
            debug=API_CONFIG['debug']
        )
    else:
        print("❌ Failed to initialize fraud detection pipeline!")
        print("Please check that the model files exist and are properly trained.")