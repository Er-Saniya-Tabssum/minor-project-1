import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from faker import Faker
import os

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

class UPIDatasetGenerator:
    def __init__(self, num_transactions=50000):
        self.num_transactions = num_transactions
        self.device_ids = [f"device_{i}" for i in range(1, 10001)]
        self.user_ids = [f"user_{i}@upi" for i in range(1, 15001)]
        self.receiver_ids = [f"receiver_{i}@upi" for i in range(1, 8001)]
        
        # Create some high-risk receivers (10% of total)
        self.high_risk_receivers = random.sample(self.receiver_ids, int(len(self.receiver_ids) * 0.1))
        
    def generate_transaction_data(self):
        """Generate synthetic UPI transaction dataset"""
        
        data = []
        start_date = datetime.now() - timedelta(days=365)
        
        # Create user historical patterns
        user_patterns = {}
        for user in self.user_ids:
            user_patterns[user] = {
                'avg_amount': abs(np.random.normal(2000, 800)),
                'typical_hours': np.random.choice(range(24), size=np.random.randint(3, 8)),
                'preferred_device': random.choice(self.device_ids),
                'home_location': (float(fake.latitude()), float(fake.longitude())),
                'account_age_days': np.random.randint(30, 1095)
            }
        
        # Create receiver patterns
        receiver_patterns = {}
        for receiver in self.receiver_ids:
            receiver_patterns[receiver] = {
                'account_age_days': np.random.randint(1, 730),
                'fraud_reports': np.random.choice([0, 1, 2, 3, 5, 8], p=[0.7, 0.15, 0.08, 0.04, 0.02, 0.01]),
                'unique_senders': np.random.randint(1, 500)
            }
            
            # High-risk receivers have more fraud reports
            if receiver in self.high_risk_receivers:
                receiver_patterns[receiver]['fraud_reports'] = np.random.choice([3, 5, 8, 12], p=[0.4, 0.3, 0.2, 0.1])
                receiver_patterns[receiver]['account_age_days'] = np.random.randint(1, 30)  # Newer accounts
        
        print("Generating transactions...")
        
        for i in range(self.num_transactions):
            if i % 5000 == 0:
                print(f"Generated {i} transactions...")
                
            # Basic transaction info
            sender_id = random.choice(self.user_ids)
            receiver_id = random.choice(self.receiver_ids)
            
            # Transaction timestamp
            transaction_date = start_date + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # User patterns
            user_pattern = user_patterns[sender_id]
            receiver_pattern = receiver_patterns[receiver_id]
            
            # Determine if this is a fraud transaction (10% fraud rate)
            is_fraud = random.random() < 0.1
            
            # Transaction amount - fraudulent transactions tend to be higher or very low
            if is_fraud:
                if random.random() < 0.6:  # High amount fraud
                    amount = np.random.normal(abs(user_pattern['avg_amount']) * 5, abs(user_pattern['avg_amount']))
                else:  # Micro fraud
                    amount = np.random.uniform(1, 50)
            else:
                avg_amt = abs(user_pattern['avg_amount'])
                amount = np.random.normal(avg_amt, avg_amt * 0.3)
            
            amount = max(1, amount)  # Ensure positive amount
            
            # Device info
            if is_fraud and random.random() < 0.4:  # 40% of frauds use new device
                device_id = random.choice(self.device_ids)
            else:
                device_id = user_pattern['preferred_device']
            
            # Transaction time analysis
            transaction_hour = transaction_date.hour
            is_unusual_hour = transaction_hour not in user_pattern['typical_hours']
            
            if is_fraud:
                # Fraudulent transactions more likely at unusual hours
                if random.random() < 0.6:
                    transaction_hour = random.choice([1, 2, 3, 4, 22, 23])
            
            # Location data
            if is_fraud and random.random() < 0.5:  # 50% of frauds from different location
                current_lat = float(fake.latitude())
                current_long = float(fake.longitude())
            else:
                # Normal location with some variance
                current_lat = float(user_pattern['home_location'][0]) + np.random.normal(0, 0.01)
                current_long = float(user_pattern['home_location'][1]) + np.random.normal(0, 0.01)
            
            # Calculate distance from home location
            home_lat, home_long = float(user_pattern['home_location'][0]), float(user_pattern['home_location'][1])
            geo_distance = self._calculate_distance(home_lat, home_long, current_lat, current_long)
            
            # Transaction frequency (simulate last 24h)
            if is_fraud:
                freq_24h = np.random.poisson(8)  # Higher frequency for fraud
            else:
                freq_24h = np.random.poisson(2)  # Normal frequency
            
            # Behavioral features
            time_between_open_and_pay = np.random.normal(30, 15) if not is_fraud else np.random.normal(5, 2)
            otp_entry_delay = np.random.normal(15, 5) if not is_fraud else np.random.normal(45, 20)
            
            # Increase fraud likelihood for high-risk receivers
            if receiver_id in self.high_risk_receivers and not is_fraud:
                if random.random() < 0.3:  # 30% chance to make it fraud
                    is_fraud = True
            
            # Create transaction record
            transaction = {
                'transaction_id': f"TXN_{i+1:06d}",
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'amount': round(amount, 2),
                'transaction_time': transaction_hour,
                'transaction_frequency_last_24h': freq_24h,
                'avg_amount_last_week': round(user_pattern['avg_amount'], 2),
                'transaction_type': random.choice(['Send', 'Send', 'Send', 'Request']),  # Mostly sends
                'device_id': device_id,
                'os_version': random.choice(['Android_12', 'Android_13', 'iOS_15', 'iOS_16']),
                'ip_address': fake.ipv4(),
                'current_latitude': round(current_lat, 6),
                'current_longitude': round(current_long, 6),
                'geo_distance_from_last_txn': round(geo_distance, 2),
                'receiver_age_days': receiver_pattern['account_age_days'],
                'receiver_fraud_reports': receiver_pattern['fraud_reports'],
                'unique_senders_to_receiver': receiver_pattern['unique_senders'],
                'time_between_upi_open_and_pay': round(max(1, time_between_open_and_pay), 2),
                'otp_entry_delay': round(max(1, otp_entry_delay), 2),
                'is_unusual_hour': 1 if is_unusual_hour else 0,
                'amount_deviation_from_avg': round(abs(amount - user_pattern['avg_amount']) / user_pattern['avg_amount'], 3),
                'timestamp': transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                'is_fraud': 1 if is_fraud else 0
            }
            
            data.append(transaction)
        
        return pd.DataFrame(data)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km"""
        # Haversine formula
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c

def main():
    # Create output directory
    output_dir = '/Users/deepak/Downloads/project/upi_fraud_detection/data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate dataset
    generator = UPIDatasetGenerator(num_transactions=50000)
    df = generator.generate_transaction_data()
    
    # Save dataset
    output_path = os.path.join(output_dir, 'upi_transactions.csv')
    df.to_csv(output_path, index=False)
    
    print(f"\nDataset generated successfully!")
    print(f"Total transactions: {len(df)}")
    print(f"Fraud transactions: {df['is_fraud'].sum()}")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")
    print(f"Saved to: {output_path}")
    
    # Display sample data
    print("\nSample data:")
    print(df.head())
    
    print("\nDataset info:")
    print(df.info())

if __name__ == "__main__":
    main()