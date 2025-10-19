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
from utils.spark_session import get_or_create_spark_session

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
    
    def __init__(self, nominal_columns: List[str], one_hot: bool = True, spark: Optional[SparkSession] = None):
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
        logger.info(f"\n{'='*60}")
        logger.info(f"NOMINAL ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting nominal encoding for {len(self.nominal_columns)} columns")
        
        df_encoded = df
        stages = []
        
        for column in self.nominal_columns:
            logger.info(f"\n--- Processing column: {column} ---")
            
            # Check for missing values
            missing_count = df_encoded.filter(F.col(column).isNull()).count()
            if missing_count > 0:
                logger.warning(f"  ⚠ Column has {missing_count} missing values before encoding")
                # Fill missing values with a placeholder
                df_encoded = df_encoded.fillna({column: "MISSING"})
            
            # Get unique values
            unique_values = df_encoded.select(column).distinct().count()
            logger.info(f"  Unique values: {unique_values}")
            
            # Create StringIndexer
            indexer = StringIndexer(
                inputCol=column,
                outputCol=f"{column}_index",
                handleInvalid="keep"  # Keeps unseen labels as index = numLabels
            )
            
            # Fit the indexer
            indexer_model = indexer.fit(df_encoded)
            self.indexers[column] = indexer_model
            
            # Get the mapping
            labels = indexer_model.labels
            encoder_dict = {label: idx for idx, label in enumerate(labels)}
            self.encoder_dicts[column] = encoder_dict
            
            # Save encoder dictionary with proper metadata
            encoder_path = os.path.join('artifacts/encode', f"{column}_encoder.json")
            encoder_metadata = {
                'categories': labels,
                'encoding_type': 'one_hot' if self.one_hot else 'label',
                'mappings': encoder_dict
            }
            with open(encoder_path, "w") as f:
                json.dump(encoder_metadata, f, indent=2)
            logger.info(f"  ✓ Saved encoder to {encoder_path}")
            
            # Apply indexing
            df_encoded = indexer_model.transform(df_encoded)
            
            if self.one_hot:
                # Apply one-hot encoding - create individual binary columns
                for i, category in enumerate(labels):
                    binary_col_name = f"{column}_{category}"
                    df_encoded = df_encoded.withColumn(
                        binary_col_name, 
                        F.when(F.col(f"{column}_index") == i, 1).otherwise(0)
                    )
                
                # Drop intermediate index column and original column
                df_encoded = df_encoded.drop(column, f"{column}_index")
                logger.info(f"  ✓ Applied one-hot encoding to column '{column}' → {len(labels)} binary columns")
            else:
                # Replace original column with index
                df_encoded = df_encoded.drop(column).withColumnRenamed(f"{column}_index", column)
                logger.info(f"  ✓ Successfully encoded column '{column}' with {len(labels)} categories")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ NOMINAL ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded
    
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
        logger.info(f"\n{'='*60}")
        logger.info(f"ORDINAL ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting ordinal encoding for {len(self.ordinal_mappings)} columns")
        
        df_encoded = df
        
        for column, mapping in self.ordinal_mappings.items():
            logger.info(f"\n--- Processing column: {column} ---")
            logger.info(f"  Mapping: {mapping}")
            
            # Get initial value distribution
            value_counts = df_encoded.groupBy(column).count().collect()
            initial_dist = {row[column]: row['count'] for row in value_counts}
            logger.info(f"  Before encoding: {initial_dist}")
            
            # Check for missing values
            missing_count = df_encoded.filter(F.col(column).isNull()).count()
            if missing_count > 0:
                logger.warning(f"  ⚠ Column has {missing_count} missing values before encoding")
            
            # Create mapping expression
            mapping_expr = F.when(F.col(column).isNull(), None)
            for value, code in mapping.items():
                mapping_expr = mapping_expr.when(F.col(column) == value, code)
            
            # Apply mapping
            df_encoded = df_encoded.withColumn(f"{column}_encoded", mapping_expr)
            
            # Check for unmapped values
            unmapped_count = df_encoded.filter(
                F.col(f"{column}_encoded").isNull() & F.col(column).isNotNull()
            ).count()
            if unmapped_count > 0:
                logger.warning(f"  ⚠ Column has {unmapped_count} unmapped values after encoding")
                # Optionally handle unmapped values
                df_encoded = df_encoded.withColumn(
                    f"{column}_encoded",
                    F.when(
                        F.col(f"{column}_encoded").isNull() & F.col(column).isNotNull(),
                        -1  # Default value for unmapped
                    ).otherwise(F.col(f"{column}_encoded"))
                )
            
            # Replace original column
            df_encoded = df_encoded.drop(column).withColumnRenamed(f"{column}_encoded", column)
            
            # Log encoded value distribution
            encoded_counts = df_encoded.groupBy(column).count().collect()
            encoded_dist = {row[column]: row['count'] for row in encoded_counts}
            logger.info(f"  ✓ Encoded with {len(mapping)} categories")
            logger.info(f"  After encoding: {encoded_dist}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ ORDINAL ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded


class OneHotEncodingStrategy(FeatureEncodingStrategy):
    """
    One-hot encoding strategy for categorical variables.
    Creates binary columns for each category.
    """
    
    def __init__(self, categorical_columns: List[str], max_categories: int = 50, 
                 spark: Optional[SparkSession] = None):
        """
        Initialize one-hot encoding strategy.
        
        Args:
            categorical_columns: List of column names to encode
            max_categories: Maximum number of categories to encode per column
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.categorical_columns = categorical_columns
        self.max_categories = max_categories
        logger.info(f"OneHotEncodingStrategy initialized for columns: {categorical_columns}")
    
    def encode(self, df: DataFrame) -> DataFrame:
        """
        Apply one-hot encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with one-hot encoded columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ONE-HOT ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        
        df_encoded = df
        
        for column in self.categorical_columns:
            # Get unique values
            unique_count = df_encoded.select(column).distinct().count()
            
            if unique_count > self.max_categories:
                logger.warning(f"Column {column} has {unique_count} categories, exceeding max {self.max_categories}")
                continue
            
            # Use StringIndexer + OneHotEncoder
            indexer = StringIndexer(inputCol=column, outputCol=f"{column}_index")
            encoder = OneHotEncoder(inputCol=f"{column}_index", outputCol=f"{column}_vec")
            
            # Create pipeline
            pipeline = Pipeline(stages=[indexer, encoder])
            pipeline_model = pipeline.fit(df_encoded)
            df_encoded = pipeline_model.transform(df_encoded)
            
            # Drop intermediate columns
            df_encoded = df_encoded.drop(column, f"{column}_index")
            
            logger.info(f"✓ One-hot encoded column '{column}' with {unique_count} categories")
        
        logger.info(f"✓ ONE-HOT ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded