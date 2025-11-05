import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, precision_recall_curve
from sklearn.model_selection import cross_val_score, GridSearchCV
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os

class UPIFraudMLModel:
    def __init__(self):
        self.model = None
        self.best_params = None
        self.feature_importance = None
        
    def load_data(self):
        """Load preprocessed training and test data"""
        try:
            # Get the project root directory (parent of models directory)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            data_dir = os.path.join(project_root, 'data')
            
            X_train = np.load(os.path.join(data_dir, 'X_train_scaled.npy'))
            X_test = np.load(os.path.join(data_dir, 'X_test_scaled.npy'))
            y_train = np.load(os.path.join(data_dir, 'y_train.npy'))
            y_test = np.load(os.path.join(data_dir, 'y_test.npy'))
            
            print(f"Training data: {X_train.shape}")
            print(f"Test data: {X_test.shape}")
            
            return X_train, X_test, y_train, y_test
        except Exception as e:
            print(f"Error loading data: {e}")
            return None, None, None, None
    
    def train_model(self, X_train, y_train, use_grid_search=False):
        """Train XGBoost model with optional hyperparameter tuning"""
        
        print("Training XGBoost model...")
        
        if use_grid_search:
            print("Performing hyperparameter tuning...")
            
            # Define parameter grid
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5, 6],
                'learning_rate': [0.01, 0.1, 0.2],
                'scale_pos_weight': [5, 10, 15]
            }
            
            # Initialize XGBoost classifier
            xgb_model = xgb.XGBClassifier(
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            )
            
            # Grid search with cross-validation
            grid_search = GridSearchCV(
                xgb_model, 
                param_grid, 
                cv=3, 
                scoring='roc_auc',
                n_jobs=-1, 
                verbose=1
            )
            
            grid_search.fit(X_train, y_train)
            
            self.best_params = grid_search.best_params_
            self.model = grid_search.best_estimator_
            
            print(f"Best parameters: {self.best_params}")
            print(f"Best CV score: {grid_search.best_score_:.4f}")
            
        else:
            # Use default parameters optimized for fraud detection
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.1,
                scale_pos_weight=10,  # Handle class imbalance
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            )
            
            self.model.fit(X_train, y_train)
        
        # Get feature importance
        self.feature_importance = self.model.feature_importances_
        
        print("Model training completed!")
        return self.model
    
    def evaluate_model(self, X_test, y_test, feature_names=None):
        """Comprehensive model evaluation"""
        
        if self.model is None:
            print("Model not trained yet!")
            return
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]
        
        # Basic metrics
        print("=== Model Evaluation Results ===")
        print(f"Test Accuracy: {self.model.score(X_test, y_test):.4f}")
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # Calculate fraud detection specific metrics
        tn, fp, fn, tp = cm.ravel()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\nFraud Detection Metrics:")
        print(f"Precision (% of predicted frauds that are actual frauds): {precision:.4f}")
        print(f"Recall (% of actual frauds detected): {recall:.4f}")
        print(f"Specificity (% of legit transactions correctly identified): {specificity:.4f}")
        print(f"F1-Score: {f1_score:.4f}")
        
        # Create visualizations
        self.plot_evaluation_metrics(y_test, y_prob, feature_names)
        
        return {
            'accuracy': self.model.score(X_test, y_test),
            'roc_auc': roc_auc_score(y_test, y_prob),
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'confusion_matrix': cm
        }
    
    def plot_evaluation_metrics(self, y_test, y_prob, feature_names=None):
        """Create evaluation plots with LARGER SIZE"""
        
        # BIGGER FIGURE SIZE - Increased from (15, 12) to (20, 16)
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        
        # Set larger font sizes globally
        plt.rcParams.update({'font.size': 12})
        
        # ROC Curve with BIGGER STYLING
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        auc_score = roc_auc_score(y_test, y_prob)
        
        axes[0, 0].plot(fpr, tpr, color='darkorange', lw=4, label=f'ROC curve (AUC = {auc_score:.2f})')
        axes[0, 0].plot([0, 1], [0, 1], color='navy', lw=3, linestyle='--')
        axes[0, 0].set_xlim([0.0, 1.0])
        axes[0, 0].set_ylim([0.0, 1.05])
        axes[0, 0].set_xlabel('False Positive Rate', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('True Positive Rate', fontsize=14, fontweight='bold')
        axes[0, 0].set_title('ROC Curve', fontsize=18, fontweight='bold', pad=20)
        axes[0, 0].legend(loc="lower right", fontsize=12)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(labelsize=11)
        
        # Precision-Recall Curve with BIGGER STYLING
        precision, recall, _ = precision_recall_curve(y_test, y_prob)
        
        axes[0, 1].plot(recall, precision, color='blue', lw=4)
        axes[0, 1].fill_between(recall, precision, alpha=0.2, color='blue')
        axes[0, 1].set_xlabel('Recall', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('Precision', fontsize=14, fontweight='bold')
        axes[0, 1].set_title('Precision-Recall Curve', fontsize=18, fontweight='bold', pad=20)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].tick_params(labelsize=11)
        
        # Feature Importance with BIGGER BARS and STYLING
        if feature_names and self.feature_importance is not None:
            # Get top 15 features
            feature_imp_df = pd.DataFrame({
                'feature': feature_names,
                'importance': self.feature_importance
            }).sort_values('importance', ascending=False).head(15)
            
            # Create colorful bars
            colors = plt.cm.viridis(np.linspace(0, 1, len(feature_imp_df)))
            bars = axes[1, 0].barh(range(len(feature_imp_df)), feature_imp_df['importance'], 
                                 height=0.8, color=colors, edgecolor='black', linewidth=1)
            axes[1, 0].set_yticks(range(len(feature_imp_df)))
            axes[1, 0].set_yticklabels(feature_imp_df['feature'], fontsize=11)
            axes[1, 0].set_xlabel('Feature Importance', fontsize=14, fontweight='bold')
            axes[1, 0].set_title('Top 15 Feature Importance', fontsize=18, fontweight='bold', pad=20)
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].tick_params(labelsize=11)
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                axes[1, 0].text(width + 0.001, bar.get_y() + bar.get_height()/2, 
                              f'{width:.3f}', ha='left', va='center', fontsize=10, fontweight='bold')
        
        # Fraud Score Distribution with BIGGER STYLING
        fraud_scores = y_prob[y_test == 1]
        legit_scores = y_prob[y_test == 0]
        
        axes[1, 1].hist(legit_scores, bins=60, alpha=0.7, label='Legitimate', 
                       color='green', edgecolor='darkgreen', linewidth=1)
        axes[1, 1].hist(fraud_scores, bins=60, alpha=0.7, label='Fraud', 
                       color='red', edgecolor='darkred', linewidth=1)
        axes[1, 1].set_xlabel('Fraud Probability Score', fontsize=14, fontweight='bold')
        axes[1, 1].set_ylabel('Frequency', fontsize=14, fontweight='bold')
        axes[1, 1].set_title('Distribution of Fraud Scores', fontsize=18, fontweight='bold', pad=20)
        axes[1, 1].legend(fontsize=12, loc='upper right')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].tick_params(labelsize=11)
        
        # Add more spacing between subplots
        plt.tight_layout(pad=4.0)
        
        # Add a main title for the entire figure
        fig.suptitle('🎯 UPI Fraud Detection Model - Performance Analytics', 
                    fontsize=24, fontweight='bold', y=0.98)
        
        # Save plot with HIGHER DPI for better quality
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plot_path = os.path.join(current_dir, 'model_evaluation.png')
        plt.savefig(plot_path, dpi=400, bbox_inches='tight', facecolor='white', 
                   edgecolor='none', pad_inches=0.2)
        print(f"📊 High-quality evaluation plots saved to: {plot_path}")
        
        plt.show()
    
    def save_model(self, model_path):
        """Save the trained model"""
        if self.model is None:
            print("No model to save!")
            return
        
        os.makedirs(model_path, exist_ok=True)
        
        # Save XGBoost model
        model_file = os.path.join(model_path, 'fraud_detection_model.pkl')
        joblib.dump(self.model, model_file)
        
        # Save additional info
        model_info = {
            'best_params': self.best_params,
            'feature_importance': self.feature_importance.tolist() if self.feature_importance is not None else None
        }
        
        info_file = os.path.join(model_path, 'model_info.pkl')
        joblib.dump(model_info, info_file)
        
        print(f"Model saved to: {model_file}")
        print(f"Model info saved to: {info_file}")
    
    def load_model(self, model_path):
        """Load a trained model"""
        try:
            model_file = os.path.join(model_path, 'fraud_detection_model.pkl')
            self.model = joblib.load(model_file)
            
            info_file = os.path.join(model_path, 'model_info.pkl')
            model_info = joblib.load(info_file)
            
            self.best_params = model_info.get('best_params')
            self.feature_importance = np.array(model_info.get('feature_importance', []))
            
            print(f"Model loaded from: {model_file}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict_fraud_probability(self, X):
        """Predict fraud probability for new transactions"""
        if self.model is None:
            raise ValueError("Model not trained or loaded!")
        
        return self.model.predict_proba(X)[:, 1]

def main():
    """Main training pipeline"""
    
    # Initialize model
    fraud_model = UPIFraudMLModel()
    
    # Load data
    X_train, X_test, y_train, y_test = fraud_model.load_data()
    
    if X_train is None:
        print("Failed to load data!")
        return
    
    # Load feature names
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        feature_names = joblib.load(os.path.join(current_dir, 'feature_columns.pkl'))
    except:
        feature_names = None
    
    print(f"Dataset info:")
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Features: {X_train.shape[1]}")
    print(f"Fraud rate in training: {y_train.mean():.2%}")
    print(f"Fraud rate in test: {y_test.mean():.2%}")
    
    # Train model (set use_grid_search=True for hyperparameter tuning)
    fraud_model.train_model(X_train, y_train, use_grid_search=False)
    
    # Evaluate model
    metrics = fraud_model.evaluate_model(X_test, y_test, feature_names)
    
    # Save model
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fraud_model.save_model(current_dir)
    
    print("\n=== Training Complete ===")
    print("Model ready for deployment!")

if __name__ == "__main__":
    main()