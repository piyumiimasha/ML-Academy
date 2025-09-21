import json
import logging
import os
import joblib, sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from spark_session import get_or_create_spark_session
from spark_utils import spark_to_pandas

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from config import get_binning_config, get_encoding_config
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

""" 
{
  "RowNumber": 1,
  "CustomerId": 15634602,
  "Firstname": "Grace",
  "Lastname": "Williams",
  "CreditScore": 619,
  "Geography": "France",
  "Gender": "Female",
  "Age": 42,
  "Tenure": 2,
  "Balance": 0,
  "NumOfProducts": 1,
  "HasCrCard": 1,
  "IsActiveMember": 1,
  "EstimatedSalary": 101348.88,
}

"""
class ModelInference:
    """
    Enhanced model inference class with comprehensive logging and error handling.
    """
    
    def __init__(self, model_path: str, use_spark: bool = False, spark: Optional[SparkSession] = None):
        """
        Initialize the model inference system.
        
        Args:
            model_path: Path to the trained model file
            use_spark: Whether to use PySpark for preprocessing (default: False for single records)
            spark: Optional SparkSession instance
            
        Raises:
            ValueError: If model_path is invalid
            FileNotFoundError: If model file doesn't exist
        """
        logger.info(f"\n{'='*60}")
        logger.info("INITIALIZING MODEL INFERENCE")
        logger.info(f"{'='*60}")
        
        if not model_path or not isinstance(model_path, str):
            logger.error("✗ Invalid model path provided")
            raise ValueError("Invalid model path provided")
            
        self.model_path = model_path
        self.encoders = {}
        self.model = None
        self.use_spark = use_spark
        self.spark = spark if spark else (get_or_create_spark_session() if use_spark else None)
        
        logger.info(f"Model Path: {model_path}")
        logger.info(f"Processing Engine: {'PySpark' if use_spark else 'Pandas'}")
        
        try:
            # Load model and configurations
            self.load_model()
            self.binning_config = get_binning_config()
            self.encoding_config = get_encoding_config()
            
            logger.info("✓ Model inference system initialized successfully")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize model inference: {str(e)}")
            raise

    def load_model(self) -> None:
        """
        Load the trained model from disk with validation.
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: For any loading errors
        """
        logger.info("Loading trained model...")
        
        if not os.path.exists(self.model_path):
            logger.error(f"✗ Model file not found: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            import time
            start_time = time.time()
            
            # Check if it's a PySpark model (directory) or scikit-learn model (file)
            if os.path.isdir(self.model_path):
                # PySpark model
                logger.info("Detected PySpark model directory")
                if not self.use_spark:
                    # Initialize Spark session for PySpark model
                    self.use_spark = True
                    self.spark = get_or_create_spark_session()
                
                from pyspark.ml import PipelineModel
                self.model = PipelineModel.load(self.model_path)
                self.model_type = 'pyspark'
                logger.info("✓ PySpark model loaded successfully")
                
            else:
                # Scikit-learn model
                logger.info("Detected scikit-learn model file")
                self.model = joblib.load(self.model_path)
                self.model_type = 'sklearn'
                file_size = os.path.getsize(self.model_path) / (1024**2)  # MB
                logger.info(f"  • File Size: {file_size:.2f} MB")
                logger.info("✓ Scikit-learn model loaded successfully")
            
            load_time = time.time() - start_time
            logger.info(f"  • Model Type: {type(self.model).__name__}")
            logger.info(f"  • Load Time: {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"✗ Failed to load model: {str(e)}")
            raise

    def load_encoders(self, encoders_dir: str) -> None:
        """
        Load feature encoders from directory with validation and logging.
        
        Args:
            encoders_dir: Directory containing encoder JSON files
            
        Raises:
            FileNotFoundError: If encoders directory doesn't exist
            Exception: For any loading errors
        """
        logger.info(f"\n{'='*50}")
        logger.info("LOADING FEATURE ENCODERS")
        logger.info(f"{'='*50}")
        
        if not os.path.exists(encoders_dir):
            logger.error(f"✗ Encoders directory not found: {encoders_dir}")
            raise FileNotFoundError(f"Encoders directory not found: {encoders_dir}")
        
        try:
            encoder_files = [f for f in os.listdir(encoders_dir) if f.endswith('_encoder.json')]
            
            if not encoder_files:
                logger.warning("⚠ No encoder files found in directory")
                return
            
            logger.info(f"Found {len(encoder_files)} encoder files")
            
            for file in encoder_files:
                feature_name = file.split('_encoder.json')[0]
                file_path = os.path.join(encoders_dir, file)
                
                with open(file_path, 'r') as f:
                    encoder_data = json.load(f)
                    self.encoders[feature_name] = encoder_data
                    
                logger.info(f"  ✓ Loaded encoder for '{feature_name}': {len(encoder_data)} mappings")
            
            logger.info(f"✓ All encoders loaded successfully")
            logger.info(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"✗ Failed to load encoders: {str(e)}")
            raise

    def preprocess_input(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocess input data for model prediction with comprehensive logging.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Preprocessed DataFrame ready for prediction
            
        Raises:
            ValueError: If input data is invalid
            Exception: For any preprocessing errors
        """
        logger.info(f"\n{'='*50}")
        logger.info("PREPROCESSING INPUT DATA")
        logger.info(f"{'='*50}")
        
        if not data or not isinstance(data, dict):
            logger.error("✗ Input data must be a non-empty dictionary")
            raise ValueError("Input data must be a non-empty dictionary")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([data])
            logger.info(f"✓ Input data converted to DataFrame: {df.shape}")
            logger.info(f"  • Input features: {list(df.columns)}")
            
            # Apply encoders
            if self.encoders:
                logger.info("Applying feature encoders...")
                for col, encoder in self.encoders.items():
                    if col in df.columns:
                        original_value = df[col].iloc[0]
                        df[col] = df[col].map(encoder)
                        encoded_value = df[col].iloc[0]
                        logger.info(f"  ✓ Encoded '{col}': {original_value} → {encoded_value}")
                    else:
                        logger.warning(f"  ⚠ Column '{col}' not found in input data")
            else:
                logger.info("No encoders available - skipping encoding step")

            # Apply feature binning
            if 'CreditScore' in df.columns:
                logger.info("Applying feature binning for CreditScore...")
                original_score = df['CreditScore'].iloc[0]
                
                ############### PANDAS CODES ###########################
                # Create pandas-compatible binning logic for single records
                def bin_credit_score(score):
                    if score <= 580:
                        return "Poor"
                    elif score <= 669:
                        return "Fair"
                    elif score <= 739:
                        return "Good"
                    elif score <= 799:
                        return "Very Good"
                    else:
                        return "Excellent"
                
                df['CreditScoreBins'] = df['CreditScore'].apply(bin_credit_score)
                df = df.drop('CreditScore', axis=1)  # Remove original column
                
                ############### PYSPARK CODES ###########################
                # Note: For single record inference, pandas is more efficient
                # PySpark binning would be used for batch processing
                
                binned_score = df['CreditScoreBins'].iloc[0]
                logger.info(f"  ✓ CreditScore binned: {original_score} → {binned_score}")
            else:
                logger.warning("  ⚠ CreditScore not found - skipping binning")

            # Apply ordinal encoding
            if 'CreditScoreBins' in df.columns:
                logger.info("Applying ordinal encoding for CreditScoreBins...")
                
                ############### PANDAS CODES ###########################
                # Define ordinal mapping for credit score bins
                ordinal_mapping = {
                    'Poor': 0,
                    'Fair': 1, 
                    'Good': 2,
                    'Very Good': 3,
                    'Excellent': 4
                }
                original_value = df['CreditScoreBins'].iloc[0]
                df['CreditScoreBins'] = df['CreditScoreBins'].map(ordinal_mapping)
                
                ############### PYSPARK CODES ###########################
                # Note: For single record inference, pandas mapping is more efficient
                # PySpark ordinal encoding would be used for batch processing
                
                encoded_value = df['CreditScoreBins'].iloc[0]
                logger.info(f"  ✓ CreditScoreBins encoded: {original_value} → {encoded_value}")
            else:
                logger.warning("  ⚠ CreditScoreBins not found - skipping ordinal encoding")

            # Drop unnecessary columns
            drop_columns = ['RowNumber', 'CustomerId', 'Firstname', 'Lastname']
            existing_drop_columns = [col for col in drop_columns if col in df.columns]
            
            if existing_drop_columns:
                df = df.drop(columns=existing_drop_columns)
                logger.info(f"  ✓ Dropped columns: {existing_drop_columns}")
            
            # Reorder columns to match training data
            expected_columns = ['Age', 'Tenure', 'NumOfProducts', 'HasCrCard', 'IsActiveMember', 
                              'Geography', 'Gender', 'CreditScoreBins', 'Balance', 'EstimatedSalary']
            
            # Check if all expected columns are present
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"  ⚠ Missing columns: {missing_columns}")
            
            # Reorder columns to match training order
            available_columns = [col for col in expected_columns if col in df.columns]
            df = df[available_columns]
            
            logger.info(f"✓ Preprocessing completed - Final shape: {df.shape}")
            logger.info(f"  • Final features (reordered): {list(df.columns)}")
            logger.info(f"{'='*50}\n")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Preprocessing failed: {str(e)}")
            raise
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Make prediction on input data with comprehensive logging.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Dictionary containing prediction status and confidence
            
        Raises:
            ValueError: If input data is invalid
            Exception: For any prediction errors
        """
        logger.info(f"\n{'='*60}")
        logger.info("MAKING PREDICTION")
        logger.info(f"{'='*60}")
        
        if not data:
            logger.error("✗ Input data cannot be empty")
            raise ValueError("Input data cannot be empty")
        
        if self.model is None:
            logger.error("✗ Model not loaded")
            raise ValueError("Model not loaded")
        
        try:
            # Preprocess input data
            processed_data = self.preprocess_input(data)
            
            # Make prediction based on model type
            logger.info("Generating predictions...")
            
            if hasattr(self, 'model_type') and self.model_type == 'pyspark':
                # PySpark model prediction
                spark_df = self.spark.createDataFrame(processed_data)
                predictions = self.model.transform(spark_df)
                
                # Get prediction and probability
                prediction_row = predictions.select("prediction", "probability").collect()[0]
                prediction = int(prediction_row.prediction)
                
                # Extract probability for positive class (index 1)
                probability_vector = prediction_row.probability
                probability = float(probability_vector[1])
                
            else:
                # Scikit-learn model prediction
                y_pred = self.model.predict(processed_data)
                y_proba = self.model.predict_proba(processed_data)[:, 1]
                
                prediction = int(y_pred[0])
                probability = float(y_proba[0])
            
            status = 'Churn' if prediction == 1 else 'Retain'
            confidence = round(probability * 100, 2)
            
            result = {
                "Status": status,
                "Confidence": f"{confidence}%"
            }
            
            logger.info("✓ Prediction completed:")
            logger.info(f"  • Raw Prediction: {prediction}")
            logger.info(f"  • Raw Probability: {probability:.4f}")
            logger.info(f"  • Final Status: {status}")
            logger.info(f"  • Confidence: {confidence}%")
            logger.info(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Prediction failed: {str(e)}")
            raise