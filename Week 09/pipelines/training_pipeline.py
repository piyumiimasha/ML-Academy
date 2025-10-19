import os
import sys
import logging
import pandas as pd
import numpy as np
from data_pipeline import data_pipeline
from typing import Dict, Any, Optional
from pyspark.sql import SparkSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.spark_session import create_spark_session, stop_spark_session
from utils.spark_utils import spark_to_pandas

# Import both sklearn and PySpark model components
from model_training import ModelTrainer, SparkModelTrainer
from model_evaluation import ModelEvaluator, SparkModelEvaluator
from model_building import XGboostModelBuilder, SparkRandomForestModelBuilder

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from mlflow_utils import MLflowTracker, create_mlflow_run_tags
from config import get_model_config, get_data_paths
import mlflow

logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def training_pipeline(
                    data_path: str = 'data/raw/ChurnModelling.csv',
                    model_params: Optional[Dict[str, Any]] = None,
                    test_size: float = 0.2, 
                    random_state: int = 42,
                    model_path: str = 'artifacts/models/churn_analysis.joblib',
                    data_format: str = 'csv',
                    training_engine: str = 'pyspark'  # 'sklearn' or 'pyspark'
                    ):
    """
    Execute model training pipeline with either scikit-learn or PySpark MLlib.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"STARTING TRAINING PIPELINE - ENGINE: {training_engine.upper()}")
    logger.info(f"{'='*80}")

    # Run data pipeline first
    data_pipeline()

    # Initialize Spark session (needed for both data loading and PySpark training)
    spark = create_spark_session("ChurnPredictionTrainingPipeline")
    
    try:
        # MLflow setup
        mlflow_tracker = MLflowTracker()
        run_tags = create_mlflow_run_tags(
            'training_pipeline', {
                'training_engine': training_engine,
                'model_path': model_path,
                'data_format': data_format
            }
        )
        run = mlflow_tracker.start_run(run_name='training_pipeline', tags=run_tags)

        # Load processed data
        logger.info("Loading processed training data...")
        data_paths = get_data_paths()
        
        if data_format == 'parquet':
            X_train = spark.read.parquet(data_paths['X_train'] + '.parquet')
            X_test = spark.read.parquet(data_paths['X_test'] + '.parquet')
            Y_train = spark.read.parquet(data_paths['Y_train'] + '.parquet')
            Y_test = spark.read.parquet(data_paths['Y_test'] + '.parquet')
            
            # Convert to pandas for sklearn or keep as Spark for PySpark
            if training_engine == 'sklearn':
                X_train = spark_to_pandas(X_train)
                X_test = spark_to_pandas(X_test)
                Y_train = spark_to_pandas(Y_train)
                Y_test = spark_to_pandas(Y_test)
        else:
            # Load CSV data
            X_train = pd.read_csv(data_paths['X_train'])
            X_test = pd.read_csv(data_paths['X_test'])
            Y_train = pd.read_csv(data_paths['Y_train'])
            Y_test = pd.read_csv(data_paths['Y_test'])

        logger.info(f"✓ Data loaded successfully")

        # Train model based on engine
        if training_engine == 'pyspark':
            evaluation_results = _train_pyspark_model(
                spark, X_train, X_test, Y_train, Y_test, model_params, model_path
            )
        else:
            evaluation_results = _train_sklearn_model(
                X_train, X_test, Y_train, Y_test, model_params, model_path
            )

        # Log results to MLflow
        mlflow.log_metrics({
            'accuracy': evaluation_results.get('accuracy', 0),
            'precision': evaluation_results.get('precision', 0),
            'recall': evaluation_results.get('recall', 0),
            'f1_score': evaluation_results.get('f1', 0)
        })

        logger.info("✓ Training pipeline completed successfully!")
        return evaluation_results

    except Exception as e:
        logger.error(f"✗ Training pipeline failed: {str(e)}")
        raise
    finally:
        stop_spark_session(spark)


def _train_sklearn_model(X_train, X_test, Y_train, Y_test, model_params, model_path):
    """Train model using scikit-learn."""
    logger.info("Training with scikit-learn...")
    
    # Build model
    model_builder = XGboostModelBuilder(**model_params)
    model = model_builder.build_model()

    # Train model
    trainer = ModelTrainer()
    model, training_score = trainer.train(model, X_train, Y_train.squeeze())
    
    # Save model
    trainer.save_model(model, model_path)
    
    # Evaluate model
    evaluator = ModelEvaluator(model, 'XGboost')
    evaluation_results = evaluator.evaluate(X_test, Y_test)
    
    return evaluation_results


def _train_pyspark_model(spark, X_train, X_test, Y_train, Y_test, model_params, model_path):
    """Train model using PySpark MLlib."""
    logger.info("Training with PySpark MLlib...")
    
    # Convert pandas to Spark DataFrames if needed
    if isinstance(X_train, pd.DataFrame):
        # Combine features and labels
        train_pandas = X_train.copy()
        train_pandas['label'] = Y_train.squeeze()
        train_spark_df = spark.createDataFrame(train_pandas)
        
        test_pandas = X_test.copy()
        test_pandas['label'] = Y_test.squeeze()
        test_spark_df = spark.createDataFrame(test_pandas)
        
        feature_columns = X_train.columns.tolist()
    else:
        # Already Spark DataFrames
        train_spark_df = X_train
        test_spark_df = X_test
        feature_columns = [col for col in X_train.columns if col != 'label']
    
    # Build PySpark model
    model_builder = SparkRandomForestModelBuilder(**model_params)
    model = model_builder.build_model()
    
    # Train model
    trainer = SparkModelTrainer(spark)
    trained_pipeline, training_metrics = trainer.train(
        model, train_spark_df, feature_columns
    )
    
    # Save model
    trainer.save_model(trained_pipeline, model_path)
    
    # Evaluate model
    evaluator = SparkModelEvaluator(trained_pipeline, 'SparkRandomForest')
    evaluation_results = evaluator.evaluate(test_spark_df)
    
    return evaluation_results


if __name__ == '__main__':
    model_config = get_model_config()
    training_engine = model_config.get('training_engine', 'pyspark')
    
    if training_engine == 'pyspark':
        model_params = model_config.get('pyspark_model_types', {}).get('spark_random_forest', {})
        model_path = 'artifacts/models/spark_random_forest_model'
    else:
        model_params = model_config.get('model_params', {})
        model_path = 'artifacts/models/sklearn_model.joblib'
    
    training_pipeline(
        model_params=model_params,
        model_path=model_path,
        training_engine=training_engine
    )