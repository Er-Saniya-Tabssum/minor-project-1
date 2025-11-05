import joblib
import numpy as np
from datetime import datetime
import logging
import os

from data.preprocess_data import UPIDataPreprocessor
from models.train_model import UPIFraudMLModel
from models.decision_engine import FraudDecisionEngine, FraudActionProcessor

class FraudDetectionPipeline:
    """
    Complete fraud detection pipeline that integrates preprocessing, 
    model prediction, and decision making.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize the fraud detection pipeline.
        
        Args:
            model_path (str): Path to the trained model and preprocessor
        """
        if model_path is None:
            # Get the absolute path to the models directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = current_dir
        else:
            self.model_path = model_path
        
        # Initialize components
        self.preprocessor = UPIDataPreprocessor()
        self.ml_model = UPIFraudMLModel()
        self.decision_engine = FraudDecisionEngine()
        self.action_processor = FraudActionProcessor()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load models and preprocessors
        self.is_loaded = self._load_models()
    
    def _load_models(self):
        """Load trained model and preprocessor"""
        try:
            # Load preprocessor
            if not self.preprocessor.load_preprocessor(self.model_path):
                self.logger.error("Failed to load preprocessor")
                return False
            
            # Load ML model
            if not self.ml_model.load_model(self.model_path):
                self.logger.error("Failed to load ML model")
                return False
            
            self.logger.info("Fraud detection pipeline loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False
    
    def predict_fraud(self, transaction_data):
        """
        Complete fraud detection for a single transaction.
        
        Args:
            transaction_data (dict): Transaction data with all required fields
            
        Returns:
            dict: Complete fraud detection result
        """
        
        if not self.is_loaded:
            raise RuntimeError("Fraud detection pipeline not properly loaded")
        
        try:
            # Step 1: Validate input data
            self._validate_transaction_data(transaction_data)
            
            # Step 2: Preprocess transaction data
            X_processed = self.preprocessor.preprocess_single_transaction(transaction_data)
            
            # Step 3: Predict fraud probability
            fraud_score = self.ml_model.predict_fraud_probability(X_processed)[0]
            
            # Debug: Log the fraud score
            self.logger.info(f"Raw fraud score: {fraud_score}")
            
            # Ensure fraud score is in valid range
            fraud_score = max(0.0, min(1.0, float(fraud_score)))
            
            # Step 4: Make decision
            decision_result = self.decision_engine.make_decision(fraud_score, transaction_data)
            
            # Step 5: Process action
            action_response = self.action_processor.process_action(decision_result, transaction_data)
            
            # Step 6: Combine results
            final_result = {
                'transaction_id': transaction_data.get('transaction_id', 'unknown'),
                'fraud_detection': decision_result,
                'action_response': action_response,
                'processing_time': datetime.now().isoformat()
            }
            
            self.logger.info(f"Fraud detection completed for transaction {transaction_data.get('transaction_id')}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error in fraud detection: {e}")
            return self._create_error_response(str(e), transaction_data)
    
    def _validate_transaction_data(self, transaction_data):
        """Validate required fields in transaction data"""
        
        required_fields = [
            'sender_id', 'receiver_id', 'amount', 'transaction_time',
            'device_id', 'ip_address'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in transaction_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate data types and ranges
        if not isinstance(transaction_data['amount'], (int, float)) or transaction_data['amount'] <= 0:
            raise ValueError("Amount must be a positive number")
        
        if not (0 <= transaction_data['transaction_time'] <= 23):
            raise ValueError("Transaction time must be between 0 and 23")
    
    def _create_error_response(self, error_message, transaction_data):
        """Create error response for failed predictions"""
        return {
            'transaction_id': transaction_data.get('transaction_id', 'unknown'),
            'status': 'error',
            'error': error_message,
            'action_response': {
                'status': 'error',
                'action': 'BLOCK',
                'message': 'Unable to process transaction due to technical error',
                'user_message': 'Transaction could not be processed. Please try again later.',
                'next_steps': ['retry_later', 'contact_support']
            },
            'processing_time': datetime.now().isoformat()
        }
    
    def get_model_info(self):
        """Get information about loaded models"""
        if not self.is_loaded:
            return {'status': 'Models not loaded'}
        
        return {
            'status': 'loaded',
            'model_path': self.model_path,
            'features': len(self.preprocessor.feature_columns),
            'feature_names': self.preprocessor.feature_columns,
            'thresholds': self.decision_engine.get_threshold_info()
        }
    
    def batch_predict(self, transactions_list):
        """
        Process multiple transactions in batch.
        
        Args:
            transactions_list (list): List of transaction dictionaries
            
        Returns:
            list: List of fraud detection results
        """
        
        results = []
        for i, transaction in enumerate(transactions_list):
            try:
                # Add transaction ID if not present
                if 'transaction_id' not in transaction:
                    transaction['transaction_id'] = f"BATCH_{i+1:04d}"
                
                result = self.predict_fraud(transaction)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error processing transaction {i}: {e}")
                results.append(self._create_error_response(str(e), transaction))
        
        return results
    
    def update_thresholds(self, new_thresholds):
        """Update fraud detection thresholds"""
        return self.decision_engine.update_thresholds(new_thresholds)

def create_sample_transaction():
    """Create a sample transaction for testing"""
    from datetime import datetime
    import random
    
    return {
        'transaction_id': f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'sender_id': 'user_123@upi',
        'receiver_id': 'merchant_456@upi', 
        'amount': 2500.0,
        'transaction_time': datetime.now().hour,
        'transaction_frequency_last_24h': 3,
        'avg_amount_last_week': 2000.0,
        'transaction_type': 'Send',
        'device_id': 'device_123',
        'os_version': 'Android_13',
        'ip_address': '192.168.1.100',
        'current_latitude': 28.6139,
        'current_longitude': 77.2090,
        'geo_distance_from_last_txn': 5.2,
        'receiver_age_days': 365,
        'receiver_fraud_reports': 0,
        'unique_senders_to_receiver': 150,
        'time_between_upi_open_and_pay': 25.0,
        'otp_entry_delay': 12.0,
        'is_unusual_hour': 0,
        'amount_deviation_from_avg': 0.25,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    """Test the fraud detection pipeline"""
    
    # Initialize pipeline
    pipeline = FraudDetectionPipeline()
    
    if not pipeline.is_loaded:
        print("Failed to load fraud detection pipeline!")
        return
    
    print("=== UPI Fraud Detection Pipeline Test ===")
    
    # Get model info
    model_info = pipeline.get_model_info()
    print(f"Pipeline Status: {model_info['status']}")
    print(f"Number of features: {model_info['features']}")
    
    # Test with sample transaction
    print("\n=== Testing with Sample Transaction ===")
    sample_transaction = create_sample_transaction()
    
    print("Sample Transaction:")
    for key, value in sample_transaction.items():
        print(f"  {key}: {value}")
    
    # Predict fraud
    result = pipeline.predict_fraud(sample_transaction)
    
    print("\n=== Fraud Detection Result ===")
    print(f"Transaction ID: {result['transaction_id']}")
    print(f"Fraud Score: {result['fraud_detection']['fraud_score']}")
    print(f"Risk Level: {result['fraud_detection']['risk_level']}")
    print(f"Action: {result['action_response']['action']}")
    print(f"Status: {result['action_response']['status']}")
    print(f"Message: {result['action_response']['message']}")
    print(f"Reasoning: {result['fraud_detection']['reasoning']}")
    
    # Test with high-risk transaction
    print("\n=== Testing with High-Risk Transaction ===")
    high_risk_transaction = create_sample_transaction()
    high_risk_transaction.update({
        'amount': 50000.0,  # Very high amount
        'transaction_time': 2,  # Night time
        'receiver_age_days': 5,  # New receiver
        'receiver_fraud_reports': 5,  # High-risk receiver
        'geo_distance_from_last_txn': 200,  # Distant location
        'is_unusual_hour': 1
    })
    
    high_risk_result = pipeline.predict_fraud(high_risk_transaction)
    
    print(f"High-Risk Transaction Result:")
    print(f"Fraud Score: {high_risk_result['fraud_detection']['fraud_score']}")
    print(f"Risk Level: {high_risk_result['fraud_detection']['risk_level']}")
    print(f"Action: {high_risk_result['action_response']['action']}")
    print(f"Reasoning: {high_risk_result['fraud_detection']['reasoning']}")

if __name__ == "__main__":
    main()