"""
Feature encoding strategies for PySpark DataFrames.
Supports nominal encoding (StringIndexer, OneHotEncoder) and ordinal encoding.
"""

import logging
import os
import json
from enum import Enum
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer, OneHotEncoder, IndexToString
from pyspark.ml import Pipeline
from spark_session import get_or_create_spark_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureEncodingStrategy(ABC):
    """Abstract base class for feature encoding strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def encode(self, df: DataFrame) -> DataFrame:
        """
        Encode features in the DataFrame.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded features
        """
        pass


class VariableType(str, Enum):
    """Enumeration of variable types."""
    NOMINAL = 'nominal'
    ORDINAL = 'ordinal'


class NominalEncodingStrategy(FeatureEncodingStrategy):
    """
    Nominal encoding strategy using StringIndexer.
    Creates numeric indices for categorical values.
    """
    
    def __init__(self, nominal_columns: List[str], one_hot: bool = False, spark: Optional[SparkSession] = None):
        """
        Initialize nominal encoding strategy.
        
        Args:
            nominal_columns: List of column names to encode
            one_hot: Whether to apply one-hot encoding after indexing
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.nominal_columns = nominal_columns
        self.one_hot = one_hot
        self.encoder_dicts = {}
        self.indexers = {}
        self.encoders = {}
        os.makedirs('artifacts/encode', exist_ok=True)
        logger.info(f"NominalEncodingStrategy initialized for columns: {nominal_columns}")
        logger.info(f"One-hot encoding: {one_hot}")
    
    def encode(self, df: DataFrame) -> DataFrame:
        """
        Apply nominal encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded columns
        """
        pass
    
    def get_encoder_dicts(self) -> Dict[str, Dict[str, int]]:
        """Get the encoder dictionaries for all columns."""
        return self.encoder_dicts
    
    def get_indexers(self) -> Dict[str, StringIndexer]:
        """Get the fitted StringIndexer models."""
        return self.indexers


class OrdinalEncodingStrategy(FeatureEncodingStrategy):
    """
    Ordinal encoding strategy with custom ordering.
    Maps categorical values to ordered numeric values.
    """
    
    def __init__(self, ordinal_mappings: Dict[str, Dict[str, int]], spark: Optional[SparkSession] = None):
        """
        Initialize ordinal encoding strategy.
        
        Args:
            ordinal_mappings: Dictionary mapping column names to value->order mappings
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.ordinal_mappings = ordinal_mappings
        logger.info(f"OrdinalEncodingStrategy initialized for columns: {list(ordinal_mappings.keys())}")
    
    def encode(self, df: DataFrame) -> DataFrame:
        """
        Apply ordinal encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded columns
        """
        pass