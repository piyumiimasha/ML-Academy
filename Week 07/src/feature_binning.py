"""
Feature binning strategies for both pandas and PySpark DataFrames.
Students can compare custom binning implementations and learn PySpark's Bucketizer.
"""


import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd  # Keep for educational comparison
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import Bucketizer
from spark_session import get_or_create_spark_session


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)




class FeatureBinningStrategy(ABC):
    """Abstract base class for feature binning strategies."""
    
    ############### PANDAS CODES ###########################
    # @abstractmethod
    # def bin_feature(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
    #     pass
    
    ############### PYSPARK CODES ###########################
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def bin_feature(self, df: DataFrame, column: str) -> DataFrame:
        """
        Bin a feature column.
        
        Args:
            df: PySpark DataFrame
            column: Column name to bin
            
        Returns:
            DataFrame with binned feature
        """
        pass




class CustomBinningStrategy(FeatureBinningStrategy):
    """Custom binning strategy with named bins."""
    
    ############### PANDAS CODES ###########################
    # def __init__(self, bin_definitions):
    #     self.bin_definitions = bin_definitions
    #     logger.info(f"CustomBinningStratergy initialized with bins: {list(bin_definitions.keys())}")
    #
    # def bin_feature(self, df, column):
    #     logger.info(f"\n{'='*60}")
    #     logger.info(f"FEATURE BINNING - {column.upper()}")
    #     logger.info(f"{'='*60}")
    #     logger.info(f"Starting binning for column: {column}")
    #     initial_unique = df[column].nunique()
    #     value_range = (df[column].min(), df[column].max())
    #     logger.info(f"  Unique values: {initial_unique}, Range: [{value_range[0]:.2f}, {value_range[1]:.2f}]")
    #     
    #     def assign_bin(value):
    #         if value == 850:
    #             return "Excellent"
    #         
    #         for bin_label, bin_range in self.bin_definitions.items():
    #             if len(bin_range) == 2:
    #                 if bin_range[0] <= value <= bin_range[1]:
    #                     return bin_label
    #             elif len(bin_range) == 1:
    #                 if value >= bin_range[0]:
    #                     return bin_label 
    #         
    #         if value > 850:
    #             return "Invalid"
    #         
    #         return "Invalid"
    #     
    #     df[f'{column}Bins'] = df[column].apply(assign_bin)
    #     
    #     # Log binning results
    #     bin_counts = df[f'{column}Bins'].value_counts()
    #     logger.info(f"\nBinning Results:")
    #     for bin_name, count in bin_counts.items():
    #         logger.info(f"  ✓ {bin_name}: {count} ({count/len(df)*100:.2f}%)")
    #     
    #     invalid_count = (df[f'{column}Bins'] == "Invalid").sum()
    #     if invalid_count > 0:
    #         logger.warning(f"  ⚠ Found {invalid_count} invalid values in column '{column}'")
    #         
    #     del df[column]
    #     logger.info(f"✓ Original column '{column}' removed, replaced with '{column}Bins'")
    #     logger.info(f"{'='*60}\n")
    #
    #     return df
    
    ############### PYSPARK CODES ###########################
    def __init__(self, bin_definitions: Dict[str, List[float]], spark: Optional[SparkSession] = None):
        """
        Initialize custom binning strategy.
        
        Args:
            bin_definitions: Dictionary mapping bin names to [min, max] ranges
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.bin_definitions = bin_definitions
        logger.info(f"CustomBinningStratergy initialized with bins: {list(bin_definitions.keys())}")
    
    def bin_feature(self, df: DataFrame, column: str) -> DataFrame:
        """
        Apply custom binning to a feature column.
        
        Args:
            df: PySpark DataFrame
            column: Column name to bin
            
        Returns:
            DataFrame with original column replaced by binned version
        """
        bin_column = f'{column}Bins'


        case_expr = F.when(F.col(column) == 850, "Excellent")




        for bin_label, bin_range in self.bin_definitions.items():
            if len(bin_range) == 2:
                case_expr = case_expr.when(
                                        (F.col(column) >= bin_range[0]) & F.col(column) <= bin_range[1], 
                                        bin_label
                                        )
            elif len(bin_range) == 1:
                case_expr = case_expr.when(
                                        (F.col(column) >= bin_range[0]), 
                                        bin_label
                                        )


        df_binned = df.withColumn(bin_column, case_expr)
        df_binned = df_binned.drop(column)


        return df_binned
