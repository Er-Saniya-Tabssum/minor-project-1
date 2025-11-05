import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os

class UPIDataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        
    def load_data(self, file_path):
        """Load the UPI transaction dataset"""
        try:
            df = pd.read_csv(file_path)
            print(f"Dataset loaded successfully: {df.shape}")
            return df
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return None
    
    def engineer_features(self, df):
        """Create additional features for better fraud detection"""
        df = df.copy()
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Amount-based features
        df['amount_log'] = np.log1p(df['amount'])
        df['amount_zscore'] = (df['amount'] - df['avg_amount_last_week']) / (df['avg_amount_last_week'] + 1e-6)
        
        # Risk indicators
        df['high_amount_flag'] = (df['amount'] > df['avg_amount_last_week'] * 3).astype(int)
        df['micro_amount_flag'] = (df['amount'] < 100).astype(int)
        df['new_receiver_flag'] = (df['receiver_age_days'] < 30).astype(int)
        df['high_risk_receiver'] = (df['receiver_fraud_reports'] > 2).astype(int)
        
        # Device and location features
        df['location_risk'] = (df['geo_distance_from_last_txn'] > 50).astype(int)
        df['quick_transaction'] = (df['time_between_upi_open_and_pay'] < 10).astype(int)
        df['slow_otp_entry'] = (df['otp_entry_delay'] > 30).astype(int)
        
        # Frequency-based features
        df['high_frequency_flag'] = (df['transaction_frequency_last_24h'] > 5).astype(int)
        
        # Night time transactions (potential risk indicator)
        df['night_transaction'] = ((df['hour'] >= 23) | (df['hour'] <= 5)).astype(int)
        
        return df
    
    def prepare_features(self, df):
        """Prepare features for ML model training"""
        
        # Categorical columns to encode
        categorical_cols = ['transaction_type', 'os_version']
        
        # Encode categorical variables
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Select numerical features for training
        feature_cols = [
            'amount', 'transaction_time', 'transaction_frequency_last_24h',
            'avg_amount_last_week', 'geo_distance_from_last_txn',
            'receiver_age_days', 'receiver_fraud_reports', 'unique_senders_to_receiver',
            'time_between_upi_open_and_pay', 'otp_entry_delay', 'is_unusual_hour',
            'amount_deviation_from_avg', 'amount_log', 'amount_zscore',
            'high_amount_flag', 'micro_amount_flag', 'new_receiver_flag',
            'high_risk_receiver', 'location_risk', 'quick_transaction',
            'slow_otp_entry', 'high_frequency_flag', 'night_transaction',
            'is_weekend', 'transaction_type_encoded', 'os_version_encoded'
        ]
        
        self.feature_columns = feature_cols
        X = df[feature_cols].copy()
        
        # Handle any missing values
        X = X.fillna(0)
        
        return X
    
    def split_data(self, X, y, test_size=0.2, random_state=42):
        """Split data into train and test sets"""
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    
    def fit_scaler(self, X_train):
        """Fit the scaler on training data"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        return X_train_scaled
    
    def transform_data(self, X):
        """Transform data using fitted scaler"""
        return self.scaler.transform(X)
    
    def save_preprocessor(self, save_path):
        """Save the preprocessor objects"""
        os.makedirs(save_path, exist_ok=True)
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(save_path, 'scaler.pkl'))
        
        # Save label encoders
        joblib.dump(self.label_encoders, os.path.join(save_path, 'label_encoders.pkl'))
        
        # Save feature columns
        joblib.dump(self.feature_columns, os.path.join(save_path, 'feature_columns.pkl'))
        
        print(f"Preprocessor saved to {save_path}")
    
    def load_preprocessor(self, load_path):
        """Load the preprocessor objects"""
        try:
            self.scaler = joblib.load(os.path.join(load_path, 'scaler.pkl'))
            self.label_encoders = joblib.load(os.path.join(load_path, 'label_encoders.pkl'))
            self.feature_columns = joblib.load(os.path.join(load_path, 'feature_columns.pkl'))
            print(f"Preprocessor loaded from {load_path}")
            return True
        except Exception as e:
            print(f"Error loading preprocessor: {e}")
            return False
    
    def preprocess_single_transaction(self, transaction_data):
        """Preprocess a single transaction for real-time prediction"""
        # Convert to DataFrame if it's a dict
        if isinstance(transaction_data, dict):
            df = pd.DataFrame([transaction_data])
        else:
            df = transaction_data.copy()
        
        # Engineer features
        df = self.engineer_features(df)
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Scale features
        X_scaled = self.transform_data(X)
        
        return X_scaled

def main():
    """Main preprocessing pipeline"""
    
    # Initialize preprocessor
    preprocessor = UPIDataPreprocessor()
    
    # Load data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'upi_transactions.csv')
    df = preprocessor.load_data(data_path)
    
    if df is None:
        return
    
    print("\nOriginal dataset shape:", df.shape)
    print("Fraud rate:", df['is_fraud'].mean())
    
    # Engineer features
    df_engineered = preprocessor.engineer_features(df)
    print("After feature engineering:", df_engineered.shape)
    
    # Prepare features
    X = preprocessor.prepare_features(df_engineered)
    y = df_engineered['is_fraud']
    
    print("Feature matrix shape:", X.shape)
    print("Features:", X.columns.tolist())
    
    # Split data
    X_train, X_test, y_train, y_test = preprocessor.split_data(X, y)
    print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Fit scaler and transform training data
    X_train_scaled = preprocessor.fit_scaler(X_train)
    X_test_scaled = preprocessor.transform_data(X_test)
    
    print("Data scaling completed")
    
    # Save preprocessor
    project_root = os.path.dirname(current_dir)
    models_dir = os.path.join(project_root, 'models')
    preprocessor.save_preprocessor(models_dir)
    
    # Save processed data
    np.save(os.path.join(current_dir, 'X_train_scaled.npy'), X_train_scaled)
    np.save(os.path.join(current_dir, 'X_test_scaled.npy'), X_test_scaled)
    np.save(os.path.join(current_dir, 'y_train.npy'), y_train)
    np.save(os.path.join(current_dir, 'y_test.npy'), y_test)
    
    print("Processed data saved successfully!")
    
    # Display basic statistics
    print("\nDataset Statistics:")
    print(f"Total transactions: {len(df)}")
    print(f"Fraud transactions: {y.sum()}")
    print(f"Fraud rate: {y.mean():.2%}")
    print(f"Training fraud rate: {y_train.mean():.2%}")
    print(f"Test fraud rate: {y_test.mean():.2%}")

if __name__ == "__main__":
    main()