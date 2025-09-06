import os
import joblib
import logging
import time
from typing import Any, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Enhanced model trainer with comprehensive logging and error handling.
    """
    
    def __init__(self):
        """Initialize the model trainer."""
        logger.info("ModelTrainer initialized")
    
    def train(
            self,
            model: BaseEstimator,
            X_train: Union[pd.DataFrame, np.ndarray],
            Y_train: Union[pd.Series, np.ndarray]
            ) -> Tuple[BaseEstimator, float]:
        """
        Train a machine learning model with comprehensive logging.
        
        Args:
            model: The machine learning model to train
            X_train: Training features
            Y_train: Training targets
            
        Returns:
            Tuple of (trained_model, training_score)
            
        Raises:
            ValueError: If input data is invalid
            Exception: For any training errors
        """
        logger.info(f"\n{'='*60}")
        logger.info("MODEL TRAINING")
        logger.info(f"{'='*60}")
        
        # Input validation
        if X_train is None or Y_train is None:
            logger.error("✗ Training data cannot be None")
            raise ValueError("Training data cannot be None")
            
        if len(X_train) == 0 or len(Y_train) == 0:
            logger.error("✗ Training data cannot be empty")
            raise ValueError("Training data cannot be empty")
            
        if len(X_train) != len(Y_train):
            logger.error(f"✗ Feature and target length mismatch: {len(X_train)} vs {len(Y_train)}")
            raise ValueError(f"Feature and target length mismatch: {len(X_train)} vs {len(Y_train)}")
        
        # Log training information
        logger.info(f"Training Configuration:")
        logger.info(f"  • Model Type: {type(model).__name__}")
        logger.info(f"  • Training Samples: {len(X_train):,}")
        logger.info(f"  • Features: {X_train.shape[1] if hasattr(X_train, 'shape') else 'Unknown'}")
        logger.info(f"  • Target Distribution: {np.bincount(Y_train) if hasattr(np, 'bincount') else 'N/A'}")
        
        try:
            # Start training
            logger.info("Starting model training...")
            start_time = time.time()
            
            model.fit(X_train, Y_train)
            
            training_time = time.time() - start_time
            logger.info(f"✓ Model training completed in {training_time:.2f} seconds")
            
            # Calculate training score
            logger.info("Calculating training score...")
            train_score = model.score(X_train, Y_train)
            logger.info(f"✓ Training Score: {train_score:.4f}")
            
            logger.info("✓ Model training successful!")
            logger.info(f"{'='*60}\n")
            
            return model, train_score
            
        except Exception as e:
            logger.error(f"✗ Model training failed: {str(e)}")
            raise
    
    def save_model(self, model: BaseEstimator, filepath: str) -> None:
        """
        Save a trained model to disk with validation and logging.
        
        Args:
            model: The trained model to save
            filepath: Path where to save the model
            
        Raises:
            ValueError: If model is None or filepath is invalid
            Exception: For any saving errors
        """
        logger.info(f"\n{'='*60}")
        logger.info("MODEL SAVING")
        logger.info(f"{'='*60}")
        
        # Input validation
        if model is None:
            logger.error("✗ Cannot save None model")
            raise ValueError("Cannot save None model")
            
        if not filepath or not isinstance(filepath, str):
            logger.error("✗ Invalid filepath provided")
            raise ValueError("Invalid filepath provided")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            logger.info(f"Saving model to: {filepath}")
            start_time = time.time()
            
            joblib.dump(model, filepath)
            
            save_time = time.time() - start_time
            file_size = os.path.getsize(filepath) / (1024**2)  # MB
            
            logger.info(f"✓ Model saved successfully!")
            logger.info(f"  • File Path: {filepath}")
            logger.info(f"  • File Size: {file_size:.2f} MB")
            logger.info(f"  • Save Time: {save_time:.2f} seconds")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"✗ Failed to save model: {str(e)}")
            raise

    def load_model(self, filepath: str) -> BaseEstimator:
        """
        Load a trained model from disk with validation and logging.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            The loaded model
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: For any loading errors
        """
        logger.info(f"\n{'='*60}")
        logger.info("MODEL LOADING")
        logger.info(f"{'='*60}")
        
        # Input validation
        if not filepath or not isinstance(filepath, str):
            logger.error("✗ Invalid filepath provided")
            raise ValueError("Invalid filepath provided")
            
        if not os.path.exists(filepath):
            logger.error(f"✗ Model file not found: {filepath}")
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        try:
            logger.info(f"Loading model from: {filepath}")
            start_time = time.time()
            
            model = joblib.load(filepath)
            
            load_time = time.time() - start_time
            file_size = os.path.getsize(filepath) / (1024**2)  # MB
            
            logger.info(f"✓ Model loaded successfully!")
            logger.info(f"  • Model Type: {type(model).__name__}")
            logger.info(f"  • File Size: {file_size:.2f} MB")
            logger.info(f"  • Load Time: {load_time:.2f} seconds")
            logger.info(f"{'='*60}\n")
            
            return model
            
        except Exception as e:
            logger.error(f"✗ Failed to load model: {str(e)}")
            raise