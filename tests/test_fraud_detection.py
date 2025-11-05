#!/usr/bin/env python3
"""
Unit tests for UPI Fraud Detection System
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from models.decision_engine import FraudDecisionEngine, FraudActionProcessor
from models.fraud_pipeline import FraudDetectionPipeline, create_sample_transaction

class TestFraudDecisionEngine(unittest.TestCase):
    """Test cases for FraudDecisionEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = FraudDecisionEngine()
    
    def test_allow_decision(self):
        """Test ALLOW decision for low fraud scores"""
        result = self.engine.make_decision(0.2)
        
        self.assertEqual(result['action'], 'ALLOW')
        self.assertEqual(result['risk_level'], 'LOW')
        self.assertAlmostEqual(result['fraud_score'], 0.2)
        self.assertIn('fraud_score', result['reasoning'])
    
    def test_verify_decision(self):
        """Test VERIFY decision for medium fraud scores"""
        result = self.engine.make_decision(0.5)
        
        self.assertEqual(result['action'], 'VERIFY')
        self.assertEqual(result['risk_level'], 'MEDIUM')
        self.assertAlmostEqual(result['fraud_score'], 0.5)
    
    def test_block_decision(self):
        """Test BLOCK decision for high fraud scores"""
        result = self.engine.make_decision(0.8)
        
        self.assertEqual(result['action'], 'BLOCK')
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertAlmostEqual(result['fraud_score'], 0.8)
    
    def test_invalid_fraud_score(self):
        """Test handling of invalid fraud scores"""
        with self.assertRaises(ValueError):
            self.engine.make_decision(-0.1)
        
        with self.assertRaises(ValueError):
            self.engine.make_decision(1.1)
        
        with self.assertRaises(ValueError):
            self.engine.make_decision("invalid")
    
    def test_business_rules_high_amount(self):
        """Test business rule for high amount transactions"""
        transaction_data = {
            'amount': 10000,
            'avg_amount_last_week': 1000,
            'receiver_age_days': 100,
            'receiver_fraud_reports': 0
        }
        
        result = self.engine.make_decision(0.3, transaction_data)
        self.assertEqual(result['action'], 'VERIFY')  # Should upgrade from ALLOW to VERIFY
        self.assertIn('High amount transaction', result['reasoning'])
    
    def test_business_rules_new_receiver(self):
        """Test business rule for new receiver with high amount"""
        transaction_data = {
            'amount': 15000,
            'avg_amount_last_week': 2000,
            'receiver_age_days': 5,  # Very new receiver
            'receiver_fraud_reports': 0
        }
        
        result = self.engine.make_decision(0.3, transaction_data)
        self.assertEqual(result['action'], 'VERIFY')
        self.assertIn('New receiver', result['reasoning'])
    
    def test_multiple_risk_indicators(self):
        """Test business rule for multiple risk indicators"""
        transaction_data = {
            'amount': 5000,
            'avg_amount_last_week': 2000,
            'is_unusual_hour': 1,
            'geo_distance_from_last_txn': 150,
            'transaction_frequency_last_24h': 12,
            'receiver_fraud_reports': 5,
            'receiver_age_days': 30
        }
        
        result = self.engine.make_decision(0.3, transaction_data)
        # Should upgrade to VERIFY or BLOCK due to multiple risk indicators
        self.assertIn(result['action'], ['VERIFY', 'BLOCK'])
        self.assertIn('risk indicators', result['reasoning'])
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # Score far from thresholds should have high confidence
        result_low = self.engine.make_decision(0.1)
        result_high = self.engine.make_decision(0.9)
        
        self.assertGreater(result_low['confidence'], 0.8)
        self.assertGreater(result_high['confidence'], 0.8)
        
        # Score close to threshold should have lower confidence
        result_threshold = self.engine.make_decision(0.39)  # Close to 0.4 threshold
        self.assertLess(result_threshold['confidence'], 0.5)
    
    def test_threshold_update(self):
        """Test threshold update functionality"""
        new_thresholds = {'allow': 0.3, 'block': 0.8}
        
        self.assertTrue(self.engine.update_thresholds(new_thresholds))
        self.assertEqual(self.engine.thresholds['allow'], 0.3)
        self.assertEqual(self.engine.thresholds['block'], 0.8)
        
        # Test invalid thresholds
        invalid_thresholds = {'allow': 0.8, 'block': 0.3}  # allow > block
        self.assertFalse(self.engine.update_thresholds(invalid_thresholds))

class TestFraudActionProcessor(unittest.TestCase):
    """Test cases for FraudActionProcessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = FraudActionProcessor()
        self.sample_decision = {
            'fraud_score': 0.5,
            'risk_level': 'MEDIUM',
            'action': 'VERIFY'
        }
    
    def test_process_allow_action(self):
        """Test processing of ALLOW action"""
        decision = self.sample_decision.copy()
        decision['action'] = 'ALLOW'
        
        result = self.processor.process_action(decision)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['action'], 'ALLOW')
        self.assertIn('complete_transaction', result['next_steps'])
    
    def test_process_verify_action(self):
        """Test processing of VERIFY action"""
        result = self.processor.process_action(self.sample_decision)
        
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['action'], 'VERIFY')
        self.assertIn('send_otp', result['next_steps'])
        self.assertIn('verification_methods', result)
    
    def test_process_block_action(self):
        """Test processing of BLOCK action"""
        decision = self.sample_decision.copy()
        decision['action'] = 'BLOCK'
        
        result = self.processor.process_action(decision)
        
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['action'], 'BLOCK')
        self.assertIn('contact_support', result['next_steps'])
        self.assertIn('support_reference', result)

class TestSampleTransaction(unittest.TestCase):
    """Test cases for sample transaction creation"""
    
    def test_create_sample_transaction(self):
        """Test sample transaction creation"""
        transaction = create_sample_transaction()
        
        # Check required fields
        required_fields = [
            'transaction_id', 'sender_id', 'receiver_id', 'amount',
            'transaction_time', 'device_id', 'timestamp'
        ]
        
        for field in required_fields:
            self.assertIn(field, transaction)
        
        # Check data types and ranges
        self.assertIsInstance(transaction['amount'], (int, float))
        self.assertGreater(transaction['amount'], 0)
        
        self.assertIsInstance(transaction['transaction_time'], int)
        self.assertGreaterEqual(transaction['transaction_time'], 0)
        self.assertLessEqual(transaction['transaction_time'], 23)
        
        # Check ID formats
        self.assertTrue(transaction['sender_id'].endswith('@upi'))
        self.assertTrue(transaction['receiver_id'].endswith('@upi'))

class TestFraudDetectionIntegration(unittest.TestCase):
    """Integration tests for the complete fraud detection pipeline"""
    
    @patch('models.fraud_pipeline.UPIDataPreprocessor')
    @patch('models.fraud_pipeline.UPIFraudMLModel')
    def test_pipeline_initialization(self, mock_ml_model, mock_preprocessor):
        """Test pipeline initialization with mocked components"""
        # Mock successful loading
        mock_preprocessor.return_value.load_preprocessor.return_value = True
        mock_ml_model.return_value.load_model.return_value = True
        
        pipeline = FraudDetectionPipeline()
        
        self.assertTrue(pipeline.is_loaded)
        mock_preprocessor.return_value.load_preprocessor.assert_called_once()
        mock_ml_model.return_value.load_model.assert_called_once()
    
    def test_transaction_validation(self):
        """Test transaction data validation"""
        pipeline = FraudDetectionPipeline()
        
        # Test missing required fields
        incomplete_transaction = {'amount': 1000}
        
        with patch.object(pipeline, 'is_loaded', True):
            with self.assertRaises(ValueError):
                pipeline._validate_transaction_data(incomplete_transaction)
        
        # Test invalid amount
        invalid_transaction = create_sample_transaction()
        invalid_transaction['amount'] = -100
        
        with patch.object(pipeline, 'is_loaded', True):
            with self.assertRaises(ValueError):
                pipeline._validate_transaction_data(invalid_transaction)
        
        # Test invalid transaction time
        invalid_transaction = create_sample_transaction()
        invalid_transaction['transaction_time'] = 25
        
        with patch.object(pipeline, 'is_loaded', True):
            with self.assertRaises(ValueError):
                pipeline._validate_transaction_data(invalid_transaction)
    
    def test_error_response_creation(self):
        """Test error response creation"""
        pipeline = FraudDetectionPipeline()
        transaction_data = create_sample_transaction()
        
        error_response = pipeline._create_error_response("Test error", transaction_data)
        
        self.assertEqual(error_response['status'], 'error')
        self.assertEqual(error_response['error'], 'Test error')
        self.assertEqual(error_response['action_response']['action'], 'BLOCK')
        self.assertIn('transaction_id', error_response)

class TestPerformance(unittest.TestCase):
    """Performance tests"""
    
    def test_decision_engine_performance(self):
        """Test decision engine performance"""
        engine = FraudDecisionEngine()
        
        import time
        start_time = time.time()
        
        # Process 1000 decisions
        for i in range(1000):
            fraud_score = i / 1000.0  # Scores from 0 to 1
            result = engine.make_decision(fraud_score)
            self.assertIn('action', result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 1000 decisions in less than 1 second
        self.assertLess(processing_time, 1.0)
        
        # Calculate throughput
        throughput = 1000 / processing_time
        print(f"Decision engine throughput: {throughput:.0f} decisions/second")

def run_tests():
    """Run all tests"""
    
    print("🧪 Running UPI Fraud Detection System Tests...")
    print("="*60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestFraudDecisionEngine,
        TestFraudActionProcessor,
        TestSampleTransaction,
        TestFraudDetectionIntegration,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()