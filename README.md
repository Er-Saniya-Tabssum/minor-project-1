# �️ Trustify: Securing Every UPI Payment with AI

A comprehensive AI/ML-based fraud detection system for UPI (Unified Payments Interface) transactions. Trustify analyzes transaction patterns, device data, receiver risk, and behavioral factors in real-time to assign fraud probability scores and make automated decisions (Allow/Verify/Block).

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![XGBoost](https://img.shields.io/badge/XGBoost-1.7.6-orange.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📊 Key Features

- **Real-time Fraud Detection**: Process transactions in milliseconds with 93%+ accuracy
- **ML-Powered**: Uses XGBoost classifier with 26 engineered features
- **Smart Decision Engine**: Implements business rules with Allow/Verify/Block actions
- **REST API**: Production-ready Flask API for easy integration
- **Comprehensive Analytics**: Detailed fraud scoring with confidence levels and reasoning
- **Scalable Architecture**: Modular design supports high-throughput processing
- **Business Rule Engine**: Configurable thresholds and custom risk indicators

## 🎯 System Performance

Based on our synthetic dataset testing:

| Metric | Value |
|--------|-------|
| **Accuracy** | 93.35% |
| **ROC AUC Score** | 99.15% |
| **Fraud Detection Rate** | 97.95% |
| **False Positive Rate** | 7.32% |
| **Average Response Time** | 13ms |
| **Throughput** | 1000+ transactions/second |

## 🏗️ Architecture

```
UPI Fraud Detection System
├── Data Layer
│   ├── Synthetic dataset generation
│   ├── Feature engineering (26 features)
│   └── Data preprocessing & scaling
├── ML Layer
│   ├── XGBoost classifier
│   ├── Model training & evaluation
│   └── Model persistence
├── Business Logic Layer
│   ├── Decision engine (thresholds)
│   ├── Business rules processor
│   └── Action processor
├── API Layer
│   ├── REST endpoints
│   ├── Request validation
│   └── Response formatting
└── Utilities
    ├── Demo system
    ├── Test suite
    └── Performance monitoring
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd upi_fraud_detection
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Generate training data**
```bash
python data/generate_dataset.py
```

4. **Preprocess data**
```bash
python data/preprocess_data.py
```

5. **Train the model**
```bash
python models/train_model.py
```

6. **Run the demo**
```bash
python demo.py
```

## 🌐 API Usage

### Start the API Server

```bash
python api/fraud_api.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### 1. Health Check
```bash
GET /
```

#### 2. Single Fraud Detection
```bash
POST /api/detect-fraud
Content-Type: application/json

{
  "transaction_id": "TXN_001",
  "sender_id": "user_123@upi",
  "receiver_id": "merchant_456@upi",
  "amount": 2500.0,
  "transaction_time": 14,
  "transaction_frequency_last_24h": 3,
  "avg_amount_last_week": 2000.0,
  "transaction_type": "Send",
  "device_id": "device_123",
  "os_version": "Android_13",
  "ip_address": "192.168.1.100",
  "current_latitude": 28.6139,
  "current_longitude": 77.2090,
  "geo_distance_from_last_txn": 5.2,
  "receiver_age_days": 365,
  "receiver_fraud_reports": 0,
  "unique_senders_to_receiver": 150,
  "time_between_upi_open_and_pay": 25.0,
  "otp_entry_delay": 12.0,
  "is_unusual_hour": 0,
  "amount_deviation_from_avg": 0.25,
  "timestamp": "2025-10-08 14:30:00"
}
```

**Response:**
```json
{
  "transaction_id": "TXN_001",
  "fraud_detection": {
    "fraud_score": 0.0245,
    "risk_level": "LOW",
    "action": "ALLOW",
    "reasoning": "Fraud score: 0.0245 | Final action: ALLOW",
    "confidence": 1.0,
    "timestamp": "2025-10-08T14:30:00"
  },
  "action_response": {
    "status": "success",
    "action": "ALLOW",
    "message": "Transaction approved successfully",
    "user_message": "Your transaction has been processed",
    "next_steps": ["complete_transaction"],
    "fraud_score": 0.0245,
    "risk_level": "LOW"
  },
  "processing_time": "2025-10-08T14:30:00.123456"
}
```

#### 3. Batch Processing
```bash
POST /api/batch-detect
Content-Type: application/json

[
  {transaction_data_1},
  {transaction_data_2},
  ...
]
```

#### 4. Model Information
```bash
GET /api/model-info
```

#### 5. Update Thresholds
```bash
POST /api/update-thresholds
Content-Type: application/json

{
  "allow": 0.3,
  "block": 0.8
}
```

## 🎯 Decision Logic

The system uses a three-tier decision framework:

### Fraud Score Thresholds

| Score Range | Risk Level | Action | Description |
|-------------|------------|--------|-------------|
| 0.0 - 0.4 | 🟢 LOW | ✅ **ALLOW** | Process transaction normally |
| 0.4 - 0.7 | 🟡 MEDIUM | ⚠️ **VERIFY** | Request additional verification (OTP/Biometric) |
| 0.7 - 1.0 | 🔴 HIGH | 🚫 **BLOCK** | Block transaction, manual review required |

### Business Rules

The system applies additional business rules on top of ML predictions:

1. **High Amount Rule**: Transactions >5x user's average → Upgrade to VERIFY
2. **New Receiver Rule**: New receivers (<7 days) with high amounts → VERIFY
3. **Multiple Risk Indicators**: 3+ risk factors → Upgrade action
4. **VIP Protection**: VIP users get downgraded from BLOCK to VERIFY
5. **Night Micro-transactions**: Small amounts at night → VERIFY

### Risk Indicators

- Unusual transaction hours
- New/different device
- Distant geographical location
- High transaction frequency
- High-risk receiver (fraud reports)
- Quick transaction completion
- Delayed OTP entry

## 📊 Features Used

The ML model uses 26 engineered features across 5 categories:

### Transaction Details
- `amount`, `transaction_time`, `transaction_frequency_last_24h`
- `avg_amount_last_week`, `transaction_type`

### Device & Network
- `device_id`, `os_version`, `ip_address`
- `geo_distance_from_last_txn`

### Receiver Information
- `receiver_age_days`, `receiver_fraud_reports`
- `unique_senders_to_receiver`

### Behavioral Patterns
- `time_between_upi_open_and_pay`, `otp_entry_delay`
- `is_unusual_hour`, `amount_deviation_from_avg`

### Engineered Features
- `amount_log`, `amount_zscore`, `high_amount_flag`
- `micro_amount_flag`, `new_receiver_flag`, `high_risk_receiver`
- `location_risk`, `quick_transaction`, `slow_otp_entry`
- `high_frequency_flag`, `night_transaction`, `is_weekend`

## 🧪 Testing

### Run Unit Tests
```bash
python tests/test_fraud_detection.py
```

### Run Demo
```bash
python demo.py
```

The demo includes:
- 5 test scenarios (normal, verify, fraud, micro-fraud, VIP)
- Performance metrics
- Stress testing capability
- Both API and direct pipeline modes

### Test Scenarios

1. **Normal Transaction**: ₹1,500 at 2 PM → ✅ ALLOW
2. **Verification Required**: ₹8,000 at 10 PM to new receiver → ⚠️ VERIFY  
3. **High-Risk Fraud**: ₹50,000 at 3 AM to suspicious receiver → 🚫 BLOCK
4. **Micro-fraud**: ₹5 at 2 AM from distant location → ⚠️ VERIFY
5. **VIP Transaction**: ₹25,000 suspicious pattern but VIP user → ⚠️ VERIFY

## 📁 Project Structure

```
upi_fraud_detection/
├── data/
│   ├── generate_dataset.py          # Synthetic data generation
│   ├── preprocess_data.py           # Data preprocessing pipeline
│   ├── upi_transactions.csv         # Generated dataset
│   └── *.npy                        # Processed training data
├── models/
│   ├── train_model.py               # ML model training
│   ├── fraud_pipeline.py            # Complete prediction pipeline
│   ├── decision_engine.py           # Business logic & decisions
│   ├── fraud_detection_model.pkl    # Trained XGBoost model
│   └── *.pkl                        # Model artifacts
├── api/
│   └── fraud_api.py                 # Flask REST API
├── config/
│   └── config.py                    # Configuration settings
├── tests/
│   └── test_fraud_detection.py      # Unit tests
├── demo.py                          # Interactive demo
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## ⚙️ Configuration

Key configuration options in `config/config.py`:

```python
# Decision Thresholds
FRAUD_THRESHOLDS = {
    'allow': 0.4,
    'verify': 0.7,
    'block': 0.7
}

# API Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}
```

## 📈 Performance Monitoring

The system provides detailed performance metrics:

- **Response Time**: Average processing time per transaction
- **Throughput**: Transactions processed per second
- **Accuracy Metrics**: Precision, Recall, F1-score
- **Business Metrics**: False positive rate, fraud detection rate
- **Confidence Scores**: Model confidence in predictions

## 🔧 Customization

### Adding New Features

1. Modify `data/preprocess_data.py` to add feature engineering
2. Retrain the model with `models/train_model.py`
3. Update API validation if needed

### Adjusting Business Rules

1. Edit `models/decision_engine.py`
2. Modify the `_apply_business_rules` method
3. Update thresholds in `config/config.py`

### Custom Risk Indicators

Add new risk indicators in the decision engine:

```python
# Check for new risk factor
if transaction_data.get('custom_risk_factor'):
    risk_indicators += 1
    reasoning.append("Custom risk detected")
```

## 🚀 Production Deployment

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "api/fraud_api.py"]
```

### Environment Variables

```bash
export FLASK_ENV=production
export MODEL_PATH=/app/models
export LOG_LEVEL=INFO
```

### Load Balancing

For high-throughput production:

1. Deploy multiple API instances
2. Use nginx/HAProxy for load balancing
3. Consider Redis for caching frequent predictions
4. Implement circuit breakers for resilience

## 📊 Monitoring & Alerts

Recommended monitoring:

- **API Response Times**: Alert if >100ms
- **Error Rates**: Alert if >1%
- **Fraud Detection Rate**: Monitor for drops
- **Model Drift**: Track prediction distribution changes
- **Business Metrics**: Daily fraud loss prevention

## 🔐 Security Considerations

- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Implement API rate limiting in production
- **Logging**: Comprehensive audit trail for all decisions
- **Model Security**: Protect model files and API endpoints
- **Data Privacy**: PII handling and GDPR compliance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Based on real-world UPI fraud detection patterns
- Inspired by industry best practices in financial fraud detection
- Built with modern ML/AI frameworks for production readiness

## 📞 Support

For questions or support:
- Create an issue in the repository
- Contact the development team
- Check the documentation and test examples

---

**⚡ Ready to deploy? Start with the quick start guide above!**

**🔒 Protecting digital payments, one transaction at a time.**