import os
import sys
import logging
import json
from typing import Dict, Optional, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.ml import Pipeline, PipelineModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from spark_session import create_spark_session, stop_spark_session
from spark_utils import save_dataframe, spark_to_pandas, get_dataframe_info, check_missing_values
from data_ingestion import DataIngestorCSV
from handle_missing_values import DropMissingValuesStrategy, FillMissingValuesStrategy, GenderImputer
from outlier_detection import OutlierDetector, IQROutlierDetection
from feature_binning import CustomBinningStrategy
from feature_encoding import OrdinalEncodingStrategy, NominalEncodingStrategy
from feature_scaling import MinMaxScalingStrategy
from data_splitter import SimpleTrainTestSplitStrategy
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from config import get_data_paths, get_columns, get_missing_values_config, get_outlier_config, get_binning_config, get_encoding_config, get_scaling_config, get_splitting_config
from mlflow_utils import MLflowTracker, setup_mlflow_autolog, create_mlflow_run_tags
import mlflow


def log_stage_metrics(df: DataFrame, stage: str, additional_metrics: Dict = None, spark: SparkSession = None):
    """Log key metrics for each processing stage."""
    try:
        # Calculate missing values count efficiently
        missing_counts = []
        for col in df.columns:
            missing_counts.append(df.filter(F.col(col).isNull()).count())
        total_missing = sum(missing_counts)
        
        metrics = {
                    f'{stage}_rows': df.count(),
                    f'{stage}_columns': len(df.columns),
                    f'{stage}_missing_values': total_missing,
                    f'{stage}_partitions': df.rdd.getNumPartitions()
                    }
        
        if additional_metrics:
            metrics.update({f'{stage}_{k}': v for k, v in additional_metrics.items()})
        
        mlflow.log_metrics(metrics)
        logger.info(f"✓ Metrics logged for {stage}: ({metrics[f'{stage}_rows']}, {metrics[f'{stage}_columns']})")
        
    except Exception as e:
        logger.error(f"✗ Failed to log metrics for {stage}: {str(e)}")


def save_processed_data(
                        X_train: DataFrame, 
                        X_test: DataFrame, 
                        Y_train: DataFrame, 
                        Y_test: DataFrame,
                        output_format: str = "both"
                        ) -> Dict[str, str]:
    """
    Save processed data in specified format(s).
    
    Args:
        X_train, X_test, Y_train, Y_test: PySpark DataFrames
        output_format: "csv", "parquet", or "both"
        
    Returns:
        Dictionary of output paths
    """
    os.makedirs('artifacts/data', exist_ok=True)
    paths = {}
    
    if output_format in ["csv", "both"]:
        # Save as CSV
        logger.info("Saving data in CSV format...")
        
        # Convert to pandas and save
        X_train_pd = spark_to_pandas(X_train)
        X_test_pd = spark_to_pandas(X_test)
        Y_train_pd = spark_to_pandas(Y_train)
        Y_test_pd = spark_to_pandas(Y_test)
        
        paths['X_train_csv'] = 'artifacts/data/X_train.csv'
        paths['X_test_csv'] = 'artifacts/data/X_test.csv'
        paths['Y_train_csv'] = 'artifacts/data/Y_train.csv'
        paths['Y_test_csv'] = 'artifacts/data/Y_test.csv'
        
        X_train_pd.to_csv(paths['X_train_csv'], index=False)
        X_test_pd.to_csv(paths['X_test_csv'], index=False)
        Y_train_pd.to_csv(paths['Y_train_csv'], index=False)
        Y_test_pd.to_csv(paths['Y_test_csv'], index=False)
        
        logger.info("✓ CSV files saved")
    
    if output_format in ["parquet", "both"]:
        # Save as Parquet
        logger.info("Saving data in Parquet format...")
        
        paths['X_train_parquet'] = 'artifacts/data/X_train.parquet'
        paths['X_test_parquet'] = 'artifacts/data/X_test.parquet'
        paths['Y_train_parquet'] = 'artifacts/data/Y_train.parquet'
        paths['Y_test_parquet'] = 'artifacts/data/Y_test.parquet'
        
        save_dataframe(X_train, paths['X_train_parquet'], format='parquet')
        save_dataframe(X_test, paths['X_test_parquet'], format='parquet')
        save_dataframe(Y_train, paths['Y_train_parquet'], format='parquet')
        save_dataframe(Y_test, paths['Y_test_parquet'], format='parquet')
        
        logger.info("✓ Parquet files saved")
    
    return paths


def data_pipeline(
    data_path: str = 'data/raw/ChurnModelling.csv',
    target_column: str = 'Exited',
    test_size: float = 0.2,
    force_rebuild: bool = False,
    output_format: str = "both"
) -> Dict[str, np.ndarray]:
    """
    Execute comprehensive data processing pipeline with PySpark and MLflow tracking.
    
    Args:
        data_path: Path to the raw data file
        target_column: Name of the target column
        test_size: Proportion of data to use for testing
        force_rebuild: Whether to force rebuild of existing artifacts
        output_format: Output format - "csv", "parquet", or "both"
        
    Returns:
        Dictionary containing processed train/test splits as numpy arrays
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"STARTING PYSPARK DATA PIPELINE")
    logger.info(f"{'='*80}")
    
    # Input validation
    if not os.path.exists(data_path):
        logger.error(f"✗ Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if not 0 < test_size < 1:
        logger.error(f"✗ Invalid test_size: {test_size}")
        raise ValueError(f"Invalid test_size: {test_size}")
    
    # Initialize Spark session
    spark = create_spark_session("ChurnPredictionDataPipeline")
    
    try:
        # Load configurations
        data_paths = get_data_paths()
        columns = get_columns()
        outlier_config = get_outlier_config()
        binning_config = get_binning_config()
        encoding_config = get_encoding_config()
        scaling_config = get_scaling_config()
        splitting_config = get_splitting_config()
        
        # Initialize MLflow tracking
        mlflow_tracker = MLflowTracker()
        run_tags = create_mlflow_run_tags('data_pipeline_pyspark', {
            'data_source': data_path,
            'force_rebuild': str(force_rebuild),
            'target_column': target_column,
            'output_format': output_format,
            'processing_engine': 'pyspark'
        })
        run = mlflow_tracker.start_run(run_name='data_pipeline_pyspark', tags=run_tags)
        
        # Create artifacts directory
        run_artifacts_dir = os.path.join('artifacts', 'mlflow_run_artifacts', run.info.run_id)
        os.makedirs(run_artifacts_dir, exist_ok=True)
        
        # Check for existing artifacts (CSV format for compatibility)
        x_train_path = os.path.join('artifacts', 'data', 'X_train.csv')
        x_test_path = os.path.join('artifacts', 'data', 'X_test.csv')
        y_train_path = os.path.join('artifacts', 'data', 'Y_train.csv')
        y_test_path = os.path.join('artifacts', 'data', 'Y_test.csv')
        
        artifacts_exist = all(os.path.exists(p) for p in [x_train_path, x_test_path, y_train_path, y_test_path])
        
        if artifacts_exist and not force_rebuild:
            logger.info("✓ Loading existing processed data artifacts")
            X_train = pd.read_csv(x_train_path)
            X_test = pd.read_csv(x_test_path)
            Y_train = pd.read_csv(y_train_path)
            Y_test = pd.read_csv(y_test_path)
            
            mlflow_tracker.log_data_pipeline_metrics({
                'total_samples': len(X_train) + len(X_test),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'processing_engine': 'existing_artifacts'
            })
            mlflow_tracker.end_run()
            
            logger.info("✓ Data pipeline completed using existing artifacts")
            return {
                'X_train': X_train.values,
                'X_test': X_test.values,
                'Y_train': Y_train.values.ravel(),
                'Y_test': Y_test.values.ravel()
            }
        
        # Process data from scratch with PySpark
        logger.info("Processing data from scratch with PySpark...")
        
        # Data ingestion
        logger.info(f"\n{'='*80}")
        logger.info(f"DATA INGESTION STEP")
        logger.info(f"{'='*80}")
        ingestor = DataIngestorCSV(spark)
        df = ingestor.ingest(data_path)
        logger.info(f"✓ Raw data loaded: {get_dataframe_info(df)}")
        
        # Log raw data metrics
        log_stage_metrics(df, 'raw', spark=spark)
        
        # Validate target column
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Handle missing values
        logger.info(f"\n{'='*80}")
        logger.info(f"HANDLING MISSING VALUES STEP")
        logger.info(f"{'='*80}")
        initial_count = df.count()
        
        # Drop critical missing values
        drop_handler = DropMissingValuesStrategy(critical_columns=columns['critical_columns'], spark=spark)
        df = drop_handler.handle(df)
        
        # Fill Age column
        age_handler = FillMissingValuesStrategy(method='mean', relevant_column='Age', spark=spark)
        df = age_handler.handle(df)
        
        # Fill Gender column (skip API-based imputation for now, use simple fill)
        df = df.fillna({'Gender': 'Unknown'})
        
        rows_removed = initial_count - df.count()
        log_stage_metrics(df, 'missing_handled', {'rows_removed': rows_removed}, spark)
        logger.info(f"✓ Missing values handled: {initial_count} → {df.count()}")
        
        # Outlier detection
        logger.info(f"\n{'='*80}")
        logger.info(f"OUTLIER DETECTION STEP")
        logger.info(f"{'='*80}")
        initial_count = df.count()
        outlier_detector = OutlierDetector(strategy=IQROutlierDetection(spark=spark))
        df = outlier_detector.handle_outliers(df, columns['outlier_columns'], method='remove')
        
        outliers_removed = initial_count - df.count()
        log_stage_metrics(df, 'outliers_removed', {'outliers_removed': outliers_removed}, spark)
        logger.info(f"✓ Outliers removed: {initial_count} → {df.count()}")
        
        # Feature binning
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE BINNING STEP")
        logger.info(f"{'='*80}")
        binning = CustomBinningStrategy(binning_config['credit_score_bins'], spark=spark)
        df = binning.bin_feature(df, 'CreditScore')
        
        # Log binning distribution
        if 'CreditScoreBins' in df.columns:
            bin_dist = df.groupBy('CreditScoreBins').count().collect()
            bin_metrics = {f'credit_score_bin_{row["CreditScoreBins"]}': row['count'] for row in bin_dist}
            mlflow.log_metrics(bin_metrics)
        
        logger.info("✓ Feature binning completed")
        
        # Feature encoding
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE ENCODING STEP")
        logger.info(f"{'='*80}")
        nominal_strategy = NominalEncodingStrategy(encoding_config['nominal_columns'], spark=spark)
        ordinal_strategy = OrdinalEncodingStrategy(encoding_config['ordinal_mappings'], spark=spark)
        
        df = nominal_strategy.encode(df)
        df = ordinal_strategy.encode(df)
        
        log_stage_metrics(df, 'encoded', spark=spark)
        logger.info("✓ Feature encoding completed")
        
        # Feature scaling
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE SCALING STEP")
        logger.info(f"{'='*80}")
        minmax_strategy = MinMaxScalingStrategy(spark=spark)
        df = minmax_strategy.scale(df, scaling_config['columns_to_scale'])
        logger.info("✓ Feature scaling completed")
        
        # Post-processing - drop unnecessary columns
        drop_columns = ['RowNumber', 'CustomerId', 'Firstname', 'Lastname']
        existing_drop_columns = [col for col in drop_columns if col in df.columns]
        if existing_drop_columns:
            df = df.drop(*existing_drop_columns)
            logger.info(f"✓ Dropped columns: {existing_drop_columns}")
        
        # Data splitting
        logger.info(f"\n{'='*80}")
        logger.info(f"DATA SPLITTING STEP")
        logger.info(f"{'='*80}")
        splitting_strategy = SimpleTrainTestSplitStrategy(test_size=splitting_config['test_size'], spark=spark)
        X_train, X_test, Y_train, Y_test = splitting_strategy.split_data(df, target_column)
        
        # Save processed data
        output_paths = save_processed_data(X_train, X_test, Y_train, Y_test, output_format)
        
        logger.info("✓ Data splitting completed")
        logger.info(f"\nDataset shapes after splitting:")
        logger.info(f"  • X_train: {X_train.count()} rows, {len(X_train.columns)} columns")
        logger.info(f"  • X_test:  {X_test.count()} rows, {len(X_test.columns)} columns")
        logger.info(f"  • Y_train: {Y_train.count()} rows, 1 column")
        logger.info(f"  • Y_test:  {Y_test.count()} rows, 1 column")
        logger.info(f"  • Feature columns: {X_train.columns}")
        
        # Save preprocessing pipeline model
        if hasattr(minmax_strategy, 'scaler_models'):
            model_path = os.path.join('artifacts', 'encode', 'fitted_preprocessing_model')
            os.makedirs(model_path, exist_ok=True)
            
            # Save metadata about the preprocessing
            preprocessing_metadata = {
                                    'scaling_columns': scaling_config['columns_to_scale'],
                                    'encoding_columns': encoding_config['nominal_columns'],
                                    'ordinal_mappings': encoding_config['ordinal_mappings'],
                                    'binning_config': binning_config,
                                    'spark_version': spark.version
                                    }
            
            with open(os.path.join(model_path, 'metadata.json'), 'w') as f:
                json.dump(preprocessing_metadata, f, indent=2)
            
            logger.info(f"✓ Saved preprocessing metadata to {model_path}")
        
        # Final metrics and visualizations
        log_stage_metrics(X_train, 'final_train', spark=spark)
        log_stage_metrics(X_test, 'final_test', spark=spark)
        
        # Log comprehensive pipeline metrics
        comprehensive_metrics = {
            'total_samples': X_train.count() + X_test.count(),
            'train_samples': X_train.count(),
            'test_samples': X_test.count(),
            'final_features': len(X_train.columns),
            'processing_engine': 'pyspark',
            'output_format': output_format
        }
        
        # Get class distribution
        train_dist = Y_train.groupBy(target_column).count().collect()
        test_dist = Y_test.groupBy(target_column).count().collect()
        
        for row in train_dist:
            comprehensive_metrics[f'train_class_{row[target_column]}'] = row['count']
        for row in test_dist:
            comprehensive_metrics[f'test_class_{row[target_column]}'] = row['count']
        
        mlflow_tracker.log_data_pipeline_metrics(comprehensive_metrics)
        
        # Log parameters
        mlflow.log_params({
            'final_feature_names': X_train.columns,
            'preprocessing_steps': ['missing_values', 'outlier_detection', 'feature_binning', 
                                  'feature_encoding', 'feature_scaling'],
            'data_pipeline_version': '3.0_pyspark'
        })
        
        # Log artifacts
        for path_key, path_value in output_paths.items():
            if os.path.exists(path_value):
                mlflow.log_artifact(path_value, "processed_datasets")
        
        mlflow_tracker.end_run()
        
        # Convert to numpy arrays for return
        X_train_np = spark_to_pandas(X_train).values
        X_test_np = spark_to_pandas(X_test).values
        Y_train_np = spark_to_pandas(Y_train).values.ravel()
        Y_test_np = spark_to_pandas(Y_test).values.ravel()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"FINAL DATASET SHAPES")
        logger.info(f"{'='*80}")
        logger.info(f"✓ Final dataset shapes:")
        logger.info(f"  • X_train shape: {X_train_np.shape} (rows: {X_train_np.shape[0]}, features: {X_train_np.shape[1]})")
        logger.info(f"  • X_test shape:  {X_test_np.shape} (rows: {X_test_np.shape[0]}, features: {X_test_np.shape[1]})")
        logger.info(f"  • Y_train shape: {Y_train_np.shape} (rows: {Y_train_np.shape[0]})")
        logger.info(f"  • Y_test shape:  {Y_test_np.shape} (rows: {Y_test_np.shape[0]})")
        logger.info(f"  • Total samples: {X_train_np.shape[0] + X_test_np.shape[0]}")
        logger.info(f"  • Train/Test ratio: {X_train_np.shape[0]/(X_train_np.shape[0] + X_test_np.shape[0]):.1%} / {X_test_np.shape[0]/(X_train_np.shape[0] + X_test_np.shape[0]):.1%}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"{'='*80}")
        logger.info("✓ PySpark data pipeline completed successfully!")
        
        return {
                'X_train': X_train_np,
                'X_test': X_test_np,
                'Y_train': Y_train_np,
                'Y_test': Y_test_np
                }
            
    except Exception as e:
        logger.error(f"✗ Data pipeline failed: {str(e)}")
        if 'mlflow_tracker' in locals():
            mlflow_tracker.end_run()
        raise
    finally:
        # Stop Spark session
        stop_spark_session(spark)


if __name__ == "__main__":
    # Run the pipeline
    processed_data = data_pipeline(output_format="both")
    logger.info(f"Pipeline completed. Train samples: {processed_data['X_train'].shape[0]}")