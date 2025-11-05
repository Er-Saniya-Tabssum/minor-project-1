#!/usr/bin/env python3
"""
UPI Fraud Detection System Demo
This script demonstrates the complete fraud detection system with various test scenarios.
"""

import sys
import os
import requests
import json
import time
from datetime import datetime, timedelta
import threading
import random

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import our components
from models.fraud_pipeline import FraudDetectionPipeline, create_sample_transaction

class UPIFraudDetectionDemo:
    def __init__(self, use_api=False, api_url="http://localhost:5000"):
        """
        Initialize the demo.
        
        Args:
            use_api (bool): Whether to use the REST API or direct pipeline
            api_url (str): API base URL if using API mode
        """
        self.use_api = use_api
        self.api_url = api_url
        self.pipeline = None
        
        if not use_api:
            # Initialize direct pipeline
            print("Initializing fraud detection pipeline...")
            self.pipeline = FraudDetectionPipeline()
            if not self.pipeline.is_loaded:
                raise RuntimeError("Failed to load fraud detection pipeline")
    
    def predict_fraud(self, transaction_data):
        """Predict fraud using either API or direct pipeline"""
        
        if self.use_api:
            # Use REST API
            try:
                response = requests.post(
                    f"{self.api_url}/api/detect-fraud",
                    json=transaction_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {'error': f'API call failed: {e}'}
        else:
            # Use direct pipeline
            return self.pipeline.predict_fraud(transaction_data)
    
    def create_test_scenarios(self):
        """Create various test scenarios"""
        
        scenarios = []
        
        # Scenario 1: Normal legitimate transaction
        normal_txn = create_sample_transaction()
        normal_txn.update({
            'transaction_id': 'DEMO_NORMAL_001',
            'amount': 1500.0,
            'transaction_time': 14,  # Afternoon
            'receiver_age_days': 365,
            'receiver_fraud_reports': 0,
            'geo_distance_from_last_txn': 2.5,
            'is_unusual_hour': 0
        })
        scenarios.append(('Normal Transaction', normal_txn))
        
        # Scenario 2: Slightly suspicious transaction (should trigger verification)
        verify_txn = create_sample_transaction()
        verify_txn.update({
            'transaction_id': 'DEMO_VERIFY_001',
            'amount': 8000.0,  # Higher than average
            'transaction_time': 22,  # Late night
            'receiver_age_days': 15,  # Relatively new receiver
            'receiver_fraud_reports': 1,
            'geo_distance_from_last_txn': 25.0,
            'is_unusual_hour': 1
        })
        scenarios.append(('Verification Required', verify_txn))
        
        # Scenario 3: High-risk fraudulent transaction (should be blocked)
        fraud_txn = create_sample_transaction()
        fraud_txn.update({
            'transaction_id': 'DEMO_FRAUD_001',
            'amount': 50000.0,  # Very high amount
            'transaction_time': 3,  # Early morning
            'receiver_age_days': 2,  # Very new receiver
            'receiver_fraud_reports': 8,  # High-risk receiver
            'geo_distance_from_last_txn': 500.0,  # Very distant
            'transaction_frequency_last_24h': 15,  # High frequency
            'is_unusual_hour': 1,
            'time_between_upi_open_and_pay': 3.0,  # Quick transaction
            'otp_entry_delay': 60.0  # Slow OTP entry
        })
        scenarios.append(('Fraudulent Transaction', fraud_txn))
        
        # Scenario 4: Micro-transaction fraud
        micro_fraud_txn = create_sample_transaction()
        micro_fraud_txn.update({
            'transaction_id': 'DEMO_MICRO_FRAUD_001',
            'amount': 5.0,  # Very small amount
            'transaction_time': 2,  # Night time
            'receiver_age_days': 1,  # Brand new receiver
            'receiver_fraud_reports': 0,
            'geo_distance_from_last_txn': 200.0,  # Distant location
            'transaction_frequency_last_24h': 25,  # Very high frequency
            'is_unusual_hour': 1
        })
        scenarios.append(('Micro-transaction Fraud', micro_fraud_txn))
        
        # Scenario 5: VIP user transaction (business rule example)
        vip_txn = create_sample_transaction()
        vip_txn.update({
            'transaction_id': 'DEMO_VIP_001',
            'amount': 25000.0,
            'transaction_time': 1,
            'receiver_age_days': 5,
            'receiver_fraud_reports': 3,
            'user_type': 'vip',  # VIP user
            'geo_distance_from_last_txn': 100.0,
            'is_unusual_hour': 1
        })
        scenarios.append(('VIP User Transaction', vip_txn))
        
        return scenarios
    
    def run_demo(self):
        """Run the complete demo"""
        
        print("="*60)
        print("🔒 UPI FRAUD DETECTION SYSTEM DEMO")
        print("="*60)
        print(f"Mode: {'REST API' if self.use_api else 'Direct Pipeline'}")
        if self.use_api:
            print(f"API URL: {self.api_url}")
        print()
        
        # Create test scenarios
        scenarios = self.create_test_scenarios()
        
        results = []
        
        print("📊 Running fraud detection on test scenarios...\n")
        
        for i, (scenario_name, transaction_data) in enumerate(scenarios, 1):
            
            print(f"Scenario {i}: {scenario_name}")
            print("-" * 40)
            
            # Show key transaction details
            print(f"💰 Amount: ₹{transaction_data['amount']:,.2f}")
            print(f"🕐 Time: {transaction_data['transaction_time']}:00")
            print(f"📍 Distance: {transaction_data['geo_distance_from_last_txn']} km")
            print(f"👤 Receiver Age: {transaction_data['receiver_age_days']} days")
            print(f"⚠️  Receiver Reports: {transaction_data['receiver_fraud_reports']}")
            
            # Predict fraud
            start_time = time.time()
            result = self.predict_fraud(transaction_data)
            processing_time = time.time() - start_time
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                print()
                continue
            
            # Extract results
            if 'fraud_detection' in result:
                fraud_score = result['fraud_detection']['fraud_score']
                risk_level = result['fraud_detection']['risk_level']
                reasoning = result['fraud_detection']['reasoning']
                action = result['action_response']['action']
                status = result['action_response']['status']
                message = result['action_response']['message']
            else:
                # Handle error response format
                fraud_score = 'N/A'
                risk_level = 'ERROR'
                reasoning = result.get('error', 'Unknown error')
                action = 'ERROR'
                status = 'error'
                message = result.get('error', 'Processing failed')
            
            # Display results with emojis
            action_emoji = {
                'ALLOW': '✅',
                'VERIFY': '⚠️',
                'BLOCK': '🚫',
                'ERROR': '❌'
            }
            
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🔴',
                'ERROR': '❌'
            }
            
            print(f"\n🎯 FRAUD DETECTION RESULT:")
            print(f"   {action_emoji.get(action, '❓')} Action: {action}")
            print(f"   📊 Fraud Score: {fraud_score}")
            print(f"   {risk_emoji.get(risk_level, '❓')} Risk Level: {risk_level}")
            print(f"   ⏱️  Processing Time: {processing_time:.3f}s")
            print(f"   💬 Message: {message}")
            print(f"   📝 Reasoning: {reasoning}")
            
            results.append({
                'scenario': scenario_name,
                'action': action,
                'fraud_score': fraud_score,
                'risk_level': risk_level,
                'processing_time': processing_time
            })
            
            print("\n" + "="*60 + "\n")
            
            # Small delay for better readability
            time.sleep(1)
        
        # Summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results):
        """Print demo summary"""
        
        print("📈 DEMO SUMMARY")
        print("="*60)
        
        action_counts = {}
        risk_counts = {}
        total_time = 0
        
        for result in results:
            action = result['action']
            risk = result['risk_level']
            
            action_counts[action] = action_counts.get(action, 0) + 1
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            if isinstance(result['processing_time'], (int, float)):
                total_time += result['processing_time']
        
        print(f"📊 Total Scenarios Tested: {len(results)}")
        print(f"⏱️  Total Processing Time: {total_time:.3f}s")
        print(f"🚀 Average Processing Time: {total_time/len(results):.3f}s per transaction")
        
        print("\n🎯 Action Distribution:")
        for action, count in action_counts.items():
            emoji = {'ALLOW': '✅', 'VERIFY': '⚠️', 'BLOCK': '🚫', 'ERROR': '❌'}.get(action, '❓')
            percentage = (count / len(results)) * 100
            print(f"   {emoji} {action}: {count} ({percentage:.1f}%)")
        
        print("\n🎨 Risk Level Distribution:")
        for risk, count in risk_counts.items():
            emoji = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴', 'ERROR': '❌'}.get(risk, '❓')
            percentage = (count / len(results)) * 100
            print(f"   {emoji} {risk}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("🔒 UPI Fraud Detection System is ready for production use.")
    
    def run_stress_test(self, num_transactions=100):
        """Run a stress test with multiple transactions"""
        
        print(f"\n🧪 STRESS TEST: Processing {num_transactions} transactions...")
        print("="*60)
        
        start_time = time.time()
        results = []
        
        for i in range(num_transactions):
            # Create random transaction
            txn = create_sample_transaction()
            txn['transaction_id'] = f'STRESS_TEST_{i+1:04d}'
            
            # Randomize some parameters to create variety
            txn['amount'] = random.uniform(100, 10000)
            txn['transaction_time'] = random.randint(0, 23)
            txn['receiver_age_days'] = random.randint(1, 365)
            txn['receiver_fraud_reports'] = random.choice([0, 0, 0, 1, 2, 5])
            
            # Process transaction
            result = self.predict_fraud(txn)
            
            if 'fraud_detection' in result:
                results.append({
                    'transaction_id': txn['transaction_id'],
                    'action': result['action_response']['action'],
                    'fraud_score': result['fraud_detection']['fraud_score']
                })
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"✅ Processed {i+1}/{num_transactions} transactions...")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        actions = [r['action'] for r in results]
        allow_count = actions.count('ALLOW')
        verify_count = actions.count('VERIFY')
        block_count = actions.count('BLOCK')
        
        print(f"\n📊 STRESS TEST RESULTS:")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"🚀 Throughput: {len(results)/total_time:.1f} transactions/second")
        print(f"⚡ Average Response Time: {total_time/len(results)*1000:.1f}ms")
        print(f"✅ ALLOW: {allow_count} ({allow_count/len(results)*100:.1f}%)")
        print(f"⚠️  VERIFY: {verify_count} ({verify_count/len(results)*100:.1f}%)")
        print(f"🚫 BLOCK: {block_count} ({block_count/len(results)*100:.1f}%)")
        
        return results

def main():
    """Main demo function"""
    
    print("🚀 Starting UPI Fraud Detection Demo...")
    
    # Choose demo mode
    use_api = input("\nUse REST API mode? (y/n) [default: n]: ").lower().strip() == 'y'
    
    try:
        # Initialize demo
        demo = UPIFraudDetectionDemo(use_api=use_api)
        
        # Run main demo
        demo.run_demo()
        
        # Ask for stress test
        stress_test = input("\nRun stress test? (y/n) [default: n]: ").lower().strip() == 'y'
        
        if stress_test:
            num_txns = input("Number of transactions [default: 100]: ").strip()
            num_txns = int(num_txns) if num_txns.isdigit() else 100
            demo.run_stress_test(num_txns)
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()