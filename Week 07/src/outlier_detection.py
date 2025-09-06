"""
Outlier detection strategies for both pandas and PySpark DataFrames.
Students can compare IQR-based outlier detection implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple
import pandas as pd  # Keep for educational comparison
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType
from spark_session import get_or_create_spark_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OutlierDetectionStrategy(ABC):
    """Abstract base class for outlier detection strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def detect_outliers(self, df: DataFrame, columns: List[str]) -> DataFrame:
        """
        Detect outliers in specified columns.
        
        Args:
            df: DataFrame (PySpark or pandas)
            columns: List of column names to check for outliers
            
        Returns:
            DataFrame with additional boolean columns indicating outliers
        """
        pass
    
    @abstractmethod
    def get_outlier_bounds(self, df: DataFrame, columns: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Get outlier bounds for specified columns.
        
        Args:
            df: DataFrame (PySpark or pandas)
            columns: List of column names
            
        Returns:
            Dictionary mapping column names to (lower_bound, upper_bound) tuples
        """
        pass


class IQROutlierDetection(OutlierDetectionStrategy):
    """IQR-based outlier detection strategy."""
    
    def __init__(self, threshold: float = 1.5, spark: Optional[SparkSession] = None):
        """
        Initialize IQR outlier detection.
        
        Args:
            threshold: IQR multiplier for outlier bounds (default: 1.5)
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.threshold = threshold
        logger.info(f"Initialized IQROutlierDetection with threshold: {threshold}")
    
    def get_outlier_bounds(self, df: DataFrame, columns: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Calculate outlier bounds using IQR method.
        
        Args:
            df: PySpark DataFrame
            columns: List of column names
            
        Returns:
            Dictionary mapping column names to (lower_bound, upper_bound) tuples
        """
        bounds = {}
        
        for col in columns:
            ############### PANDAS CODES ###########################
            # Q1 = df[col].quantile(0.25)
            # Q3 = df[col].quantile(0.75)
            # IQR = Q3 - Q1
            
            ############### PYSPARK CODES ###########################
            
        
        return bounds
    
    def detect_outliers(self, df: DataFrame, columns: List[str]) -> DataFrame:
        """
        Detect outliers using IQR method.
        
        Args:
            df: PySpark DataFrame
            columns: List of column names to check for outliers
            
        Returns:
            DataFrame with additional boolean columns '{col}_outlier' indicating outliers
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OUTLIER DETECTION - IQR METHOD (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting IQR outlier detection for columns: {columns}")
        
        # Get outlier bounds
        bounds = self.get_outlier_bounds(df, columns)
        
        # Add outlier indicator columns
        result_df = df
        total_outliers = 0
        
        for col in columns:
            logger.info(f"\n--- Processing column: {col} ---")
            
            ############### PANDAS CODES ###########################
            # df[col] = df[col].astype(float)
            
            ############### PYSPARK CODES ###########################
            # PySpark handles type conversions automatically
            
            lower_bound, upper_bound = bounds[col]
            
            # Create outlier indicator column
            outlier_col = f"{col}_outlier"
            
            ############### PANDAS CODES ###########################
            # outliers[col] = (df[col] < lower_bound) | (df[col] > upper_bound)
            # outlier_count = outliers[col].sum()
            # total_rows = len(df)
            
            ############### PYSPARK CODES ###########################

        
        logger.info(f"\n{'='*60}")
        logger.info(f'✓ OUTLIER DETECTION COMPLETE - Total outlier instances: {total_outliers}')
        logger.info(f"{'='*60}\n")
        
        return result_df


class OutlierDetector:
    """Main outlier detector class that uses different strategies."""
    
    def __init__(self, strategy: OutlierDetectionStrategy):
        """
        Initialize outlier detector with a specific strategy.
        
        Args:
            strategy: OutlierDetectionStrategy instance
        """
        self._strategy = strategy
        logger.info(f"OutlierDetector initialized with strategy: {strategy.__class__.__name__}")
    
    def detect_outliers(self, df: DataFrame, selected_columns: List[str]) -> DataFrame:
        """
        Detect outliers in selected columns.
        
        Args:
            df: DataFrame (PySpark or pandas)
            selected_columns: List of column names to check
            
        Returns:
            DataFrame with outlier indicator columns
        """
        logger.info(f"Detecting outliers in {len(selected_columns)} columns")
        return self._strategy.detect_outliers(df, selected_columns)
    
    def handle_outliers(self, df: DataFrame, selected_columns: List[str], 
                       method: str = 'remove', min_outliers: int = 2) -> DataFrame:
        """
        Handle outliers using specified method.
        
        Args:
            df: DataFrame (PySpark or pandas)
            selected_columns: List of column names to check
            method: Method to handle outliers ('remove' or 'cap')
            min_outliers: Minimum number of outlier columns to remove a row
            
        Returns:
            DataFrame with outliers handled
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OUTLIER HANDLING - {method.upper()} (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Handling outliers using method: {method}")
        
        ############### PANDAS CODES ###########################
        # initial_rows = len(df)
        
        ############### PYSPARK CODES ###########################

        
        if method == 'remove':
            # Add outlier indicator columns
            df_with_outliers = self.detect_outliers(df, selected_columns)
            
            # Count outliers per row
            outlier_columns = [f"{col}_outlier" for col in selected_columns]
            
            ############### PANDAS CODES ###########################
            # outlier_count = outliers.sum(axis=1)
            # rows_to_remove = outlier_count >= min_outliers
            # cleaned_df = df[~rows_to_remove]
            
            ############### PYSPARK CODES ###########################
            
            
            ############### PANDAS CODES ###########################
            # rows_removed = rows_to_remove.sum()
            
            ############### PYSPARK CODES ###########################
            pass
            
        elif method == 'cap':
            pass
            
        else:
            raise ValueError(f"Unknown outlier handling method: {method}")
        
        logger.info(f"{'='*60}\n")
        return cleaned_df