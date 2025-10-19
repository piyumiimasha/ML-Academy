import os
import time
import joblib
import logging
import numpy as np
import pandas as pd
from typing import Any, Tuple, Union
from sklearn.base import BaseEstimator

# PySpark imports
from pyspark.sql import DataFrame, SparkSession
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Original ModelTrainer for scikit-learn models.
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
        Train a machine learning model.
        
        Args:
            model: The machine learning model to train
            X_train: Training features
            Y_train: Training targets
            
        Returns:
            Tuple of (trained_model, training_score)
        """
        logger.info("Starting model training...")
        start_time = time.time()
        
        model.fit(X_train, Y_train)
        
        training_time = time.time() - start_time
        train_score = model.score(X_train, Y_train)
        
        logger.info(f"✓ Model training completed in {training_time:.2f} seconds")
        logger.info(f"✓ Training Score: {train_score:.4f}")
        
        return model, train_score
    
    def save_model(self, model: BaseEstimator, filepath: str) -> None:
        """Save a trained model to disk."""
        if model is None:
            raise ValueError("Cannot save None model")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(model, filepath)
        logger.info(f"✓ Model saved to: {filepath}")

    def load_model(self, filepath: str) -> BaseEstimator:
        """Load a trained model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model = joblib.load(filepath)
        logger.info(f"✓ Model loaded from: {filepath}")
        return model

class SparkModelTrainer:
    """
    PySpark MLlib model trainer - simplified to match original ModelTrainer structure.
    """
    
    def __init__(self, spark_session: SparkSession = None):
        """Initialize the PySpark model trainer."""
        self.spark = spark_session or SparkSession.getActiveSession()
        if self.spark is None:
            raise ValueError("No active SparkSession found.")
        logger.info("SparkModelTrainer initialized")
    
    def train(
            self,
            model,
            train_data: DataFrame,
            feature_columns: list
            ) -> Tuple[PipelineModel, dict]:
        """
        Train a PySpark MLlib model.
        
        Args:
            model: PySpark MLlib model (e.g., RandomForestClassifier)
            train_data: Training DataFrame with features and label columns
            feature_columns: List of feature column names
            
        Returns:
            Tuple of (trained_pipeline, training_metrics)
        """
        logger.info("Starting PySpark model training...")
        start_time = time.time()
        
        # Create feature vector assembler
        assembler = VectorAssembler(
            inputCols=feature_columns,
            outputCol="features"
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, model])
        
        # Fit the pipeline
        trained_pipeline = pipeline.fit(train_data)
        
        training_time = time.time() - start_time
        
        # Calculate training metrics
        train_predictions = trained_pipeline.transform(train_data)
        train_count = train_data.count()
        
        metrics = {
            'training_time': training_time,
            'training_samples': train_count
        }
        
        logger.info(f"✓ PySpark model training completed in {training_time:.2f} seconds")
        logger.info(f"✓ Training samples: {train_count:,}")
        
        return trained_pipeline, metrics
    
    def save_model(self, model: PipelineModel, filepath: str) -> None:
        """Save a trained PySpark model to disk."""
        if model is None:
            raise ValueError("Cannot save None model")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        model.write().overwrite().save(filepath)
        logger.info(f"✓ PySpark model saved to: {filepath}")

    def load_model(self, filepath: str) -> PipelineModel:
        """Load a trained PySpark model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model directory not found: {filepath}")
        
        from pyspark.ml import PipelineModel
        model = PipelineModel.load(filepath)
        logger.info(f"✓ PySpark model loaded from: {filepath}")
        return model