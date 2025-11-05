import numpy as np
from datetime import datetime
import logging
from config.config import FRAUD_THRESHOLDS, RISK_LEVELS

class FraudDecisionEngine:
    """
    Decision engine that determines the action to take based on fraud probability score.
    Implements the business logic for fraud detection as per the UPI guide.
    """
    
    def __init__(self, thresholds=None):
        """
        Initialize the decision engine with fraud thresholds.
        
        Args:
            thresholds (dict): Custom thresholds for fraud decisions
        """
        self.thresholds = thresholds or FRAUD_THRESHOLDS
        self.risk_levels = RISK_LEVELS
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def make_decision(self, fraud_score, transaction_data=None):
        """
        Make a decision based on fraud score and additional business rules.
        
        Args:
            fraud_score (float): Fraud probability score (0-1)
            transaction_data (dict): Additional transaction context
            
        Returns:
            dict: Decision result with action, risk level, and reasoning
        """
        
        # Validate fraud score
        if not isinstance(fraud_score, (int, float)):
            raise ValueError("Fraud score must be a number")
        
        if fraud_score < 0 or fraud_score > 1:
            raise ValueError(f"Fraud score must be between 0 and 1, got {fraud_score}")
        
        # Determine base action from fraud score
        base_action = self._get_base_action(fraud_score)
        risk_level = self._get_risk_level(fraud_score)
        
        # Apply additional business rules if transaction data is provided
        final_action, reasoning = self._apply_business_rules(
            base_action, fraud_score, transaction_data
        )
        
        # Create decision result
        decision_result = {
            'fraud_score': round(fraud_score, 4),
            'risk_level': risk_level,
            'action': final_action,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat(),
            'confidence': self._calculate_confidence(fraud_score)
        }
        
        # Log the decision
        self._log_decision(decision_result, transaction_data)
        
        return decision_result
    
    def _get_base_action(self, fraud_score):
        """Determine base action from fraud score"""
        if fraud_score < self.thresholds['allow']:
            return 'ALLOW'
        elif fraud_score < self.thresholds['block']:
            return 'VERIFY'
        else:
            return 'BLOCK'
    
    def _get_risk_level(self, fraud_score):
        """Determine risk level from fraud score"""
        for level, config in self.risk_levels.items():
            if config['min'] <= fraud_score < config['max']:
                return level
        return 'HIGH'  # Default to HIGH for edge cases
    
    def _apply_business_rules(self, base_action, fraud_score, transaction_data):
        """
        Apply additional business rules to refine the decision.
        
        Args:
            base_action (str): Base action from fraud score
            fraud_score (float): Fraud probability score
            transaction_data (dict): Transaction context
            
        Returns:
            tuple: (final_action, reasoning)
        """
        
        reasoning = [f"Fraud score: {fraud_score:.4f}"]
        final_action = base_action
        
        if transaction_data is None:
            reasoning.append(f"Base action: {base_action}")
            return final_action, " | ".join(reasoning)
        
        # Business Rule 1: High amount transactions need extra verification
        amount = transaction_data.get('amount', 0)
        avg_amount = transaction_data.get('avg_amount_last_week', 0)
        
        if amount > avg_amount * 5 and final_action == 'ALLOW':
            final_action = 'VERIFY'
            reasoning.append("High amount transaction (>5x average)")
        
        # Business Rule 2: New receiver with significant amount
        receiver_age = transaction_data.get('receiver_age_days', 365)
        if receiver_age < 7 and amount > 10000 and final_action == 'ALLOW':
            final_action = 'VERIFY'
            reasoning.append("New receiver (<7 days) with high amount")
        
        # Business Rule 3: Multiple high-risk indicators
        risk_indicators = 0
        
        # Check for unusual hour
        if transaction_data.get('is_unusual_hour', 0) == 1:
            risk_indicators += 1
            reasoning.append("Unusual transaction hour")
        
        # Check for new device
        if transaction_data.get('device_id') != transaction_data.get('preferred_device'):
            risk_indicators += 1
            reasoning.append("New/different device")
        
        # Check for location anomaly
        if transaction_data.get('geo_distance_from_last_txn', 0) > 100:
            risk_indicators += 1
            reasoning.append("Distant location")
        
        # Check for high frequency
        if transaction_data.get('transaction_frequency_last_24h', 0) > 10:
            risk_indicators += 1
            reasoning.append("High transaction frequency")
        
        # Check for high-risk receiver
        if transaction_data.get('receiver_fraud_reports', 0) > 3:
            risk_indicators += 1
            reasoning.append("High-risk receiver")
        
        # Apply rule based on risk indicators
        if risk_indicators >= 3 and final_action == 'ALLOW':
            final_action = 'VERIFY'
            reasoning.append(f"Multiple risk indicators ({risk_indicators})")
        elif risk_indicators >= 4 and final_action == 'VERIFY':
            final_action = 'BLOCK'
            reasoning.append(f"Too many risk indicators ({risk_indicators})")
        
        # Business Rule 4: VIP/Whitelist protection (example)
        user_type = transaction_data.get('user_type', 'regular')
        if user_type == 'vip' and final_action == 'BLOCK':
            final_action = 'VERIFY'
            reasoning.append("VIP user - downgraded to verification")
        
        # Business Rule 5: Micro transactions during night
        transaction_hour = transaction_data.get('transaction_time', 12)
        if amount < 50 and (transaction_hour <= 5 or transaction_hour >= 23):
            if final_action == 'ALLOW':
                final_action = 'VERIFY'
                reasoning.append("Micro transaction during night hours")
        
        reasoning.append(f"Final action: {final_action}")
        return final_action, " | ".join(reasoning)
    
    def _calculate_confidence(self, fraud_score):
        """
        Calculate confidence level based on how close the score is to thresholds.
        Scores close to thresholds have lower confidence.
        """
        
        # Distance from nearest threshold
        threshold_distances = [
            abs(fraud_score - self.thresholds['allow']),
            abs(fraud_score - self.thresholds['block'])
        ]
        
        min_distance = min(threshold_distances)
        
        # Convert distance to confidence (higher distance = higher confidence)
        # Max confidence when distance >= 0.2, min confidence when distance = 0
        confidence = min(1.0, min_distance / 0.2)
        
        return round(confidence, 3)
    
    def _log_decision(self, decision_result, transaction_data):
        """Log the decision for audit trail"""
        
        transaction_id = 'Unknown'
        if transaction_data:
            transaction_id = transaction_data.get('transaction_id', 'Unknown')
        
        log_message = (
            f"Decision for transaction {transaction_id}: "
            f"Action={decision_result['action']}, "
            f"Score={decision_result['fraud_score']}, "
            f"Risk={decision_result['risk_level']}, "
            f"Confidence={decision_result['confidence']}"
        )
        
        self.logger.info(log_message)
    
    def get_threshold_info(self):
        """Get information about current thresholds"""
        return {
            'thresholds': self.thresholds,
            'risk_levels': self.risk_levels
        }
    
    def update_thresholds(self, new_thresholds):
        """Update fraud thresholds (for dynamic adjustment)"""
        if self._validate_thresholds(new_thresholds):
            old_thresholds = self.thresholds.copy()
            self.thresholds.update(new_thresholds)
            
            self.logger.info(f"Thresholds updated from {old_thresholds} to {self.thresholds}")
            return True
        else:
            self.logger.error(f"Invalid thresholds: {new_thresholds}")
            return False
    
    def _validate_thresholds(self, thresholds):
        """Validate threshold values"""
        if not isinstance(thresholds, dict):
            return False
        
        for key, value in thresholds.items():
            if key in self.thresholds:
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    return False
                    
        # Ensure logical order: allow < verify ≤ block
        test_thresholds = self.thresholds.copy()
        test_thresholds.update(thresholds)
        
        return test_thresholds['allow'] < test_thresholds['block']

class FraudActionProcessor:
    """
    Processes the decided action and provides appropriate responses.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_action(self, decision_result, transaction_data=None):
        """
        Process the fraud decision and return appropriate response.
        
        Args:
            decision_result (dict): Result from FraudDecisionEngine
            transaction_data (dict): Original transaction data
            
        Returns:
            dict: Processed response with user messages and next steps
        """
        
        action = decision_result['action']
        fraud_score = decision_result['fraud_score']
        
        if action == 'ALLOW':
            return self._process_allow(decision_result, transaction_data)
        elif action == 'VERIFY':
            return self._process_verify(decision_result, transaction_data)
        elif action == 'BLOCK':
            return self._process_block(decision_result, transaction_data)
        else:
            return self._process_unknown(decision_result, transaction_data)
    
    def _process_allow(self, decision_result, transaction_data):
        """Process ALLOW action"""
        return {
            'status': 'success',
            'action': 'ALLOW',
            'message': 'Transaction approved successfully',
            'user_message': 'Your transaction has been processed',
            'next_steps': ['complete_transaction'],
            'fraud_score': decision_result['fraud_score'],
            'risk_level': decision_result['risk_level']
        }
    
    def _process_verify(self, decision_result, transaction_data):
        """Process VERIFY action"""
        return {
            'status': 'pending',
            'action': 'VERIFY',
            'message': 'Additional verification required',
            'user_message': 'Please complete additional verification for security',
            'next_steps': ['send_otp', 'request_verification'],
            'verification_methods': ['SMS_OTP', 'EMAIL_OTP', 'BIOMETRIC'],
            'fraud_score': decision_result['fraud_score'],
            'risk_level': decision_result['risk_level']
        }
    
    def _process_block(self, decision_result, transaction_data):
        """Process BLOCK action"""
        return {
            'status': 'blocked',
            'action': 'BLOCK',
            'message': 'Transaction blocked due to security concerns',
            'user_message': 'Transaction could not be processed. Please contact customer support if you believe this is an error.',
            'next_steps': ['contact_support', 'manual_review'],
            'support_reference': f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'fraud_score': decision_result['fraud_score'],
            'risk_level': decision_result['risk_level']
        }
    
    def _process_unknown(self, decision_result, transaction_data):
        """Process unknown action"""
        return {
            'status': 'error',
            'action': 'UNKNOWN',
            'message': 'Unable to process transaction',
            'user_message': 'Technical error occurred. Please try again later.',
            'next_steps': ['retry_later', 'contact_support'],
            'fraud_score': decision_result['fraud_score'],
            'risk_level': decision_result.get('risk_level', 'UNKNOWN')
        }