import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Union
import pandas as pd  # Keep pandas import for educational purposes
from pyspark.sql import DataFrame, SparkSession
from utils.spark_session import get_or_create_spark_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataIngestor(ABC):
    """Abstract base class for data ingestion supporting both pandas and PySpark."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """
        Initialize DataIngestor with a SparkSession.
        
        Args:
            spark: Optional SparkSession. If not provided, will create/get one.
        """
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def ingest(self, file_path_or_link: str) -> DataFrame:
        """
        Ingest data from the specified path.
        
        Args:
            file_path_or_link: Path to the data file
            
        Returns:
            DataFrame (PySpark or pandas depending on implementation)
        """
        pass


class DataIngestorCSV(DataIngestor):
    """CSV data ingestion implementation."""
    
    def ingest(self, file_path_or_link: str, **options) -> DataFrame:
        """
        Ingest CSV data using PySpark.
        
        Args:
            file_path_or_link: Path to the CSV file
            **options: Additional options for CSV reading
            
        Returns:
            PySpark DataFrame
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA INGESTION - CSV (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting CSV data ingestion from: {file_path_or_link}")
        
        try:
            # Default CSV options
            csv_options = {
                "header": "true",
                "inferSchema": "true",
                "ignoreLeadingWhiteSpace": "true",
                "ignoreTrailingWhiteSpace": "true",
                "nullValue": "",
                "nanValue": "NaN",
                "escape": '"',
                "quote": '"'
            }
            csv_options.update(options)
            
            ############### PANDAS CODES ###########################
            # df = pd.read_csv(file_path_or_link)
            
            ############### PYSPARK CODES ###########################
            # Read CSV file
            df = self.spark.read.options(**csv_options).csv(file_path_or_link)
            
            # Get DataFrame info
            row_count = df.count()
            columns = df.columns
            
            # Calculate approximate memory usage
            # Note: This is an estimate as PySpark distributes data
            sample_size = min(1000, row_count)
            if row_count > 0:
                sample_df = df.limit(sample_size).toPandas()
                memory_per_row = sample_df.memory_usage(deep=True).sum() / sample_size
                estimated_memory = (memory_per_row * row_count) / 1024**2
            else:
                estimated_memory = 0
            
            ############### PANDAS CODES ###########################
            # logger.info(f"✓ Successfully loaded CSV data - Shape: {df.shape}, Columns: {list(df.columns)}")
            # logger.info(f"✓ Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            ############### PYSPARK CODES ###########################
            logger.info(f"✓ Successfully loaded CSV data - Shape: ({row_count}, {len(columns)})")
            logger.info(f"✓ Columns: {columns}")
            logger.info(f"✓ Estimated memory usage: {estimated_memory:.2f} MB")
            logger.info(f"✓ Partitions: {df.rdd.getNumPartitions()}")
            
            logger.info(f"{'='*60}\n")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Failed to load CSV data from {file_path_or_link}: {str(e)}")
            logger.info(f"{'='*60}\n")
            raise


class DataIngestorExcel(DataIngestor):
    """Excel data ingestion implementation."""
    
    def ingest(self, file_path_or_link: str, sheet_name: Optional[str] = None, **options) -> DataFrame:
        """
        Ingest Excel data using PySpark.
        Note: This implementation converts Excel to CSV format internally as PySpark
        doesn't have native Excel support. For production use, consider using
        spark-excel library.
        
        Args:
            file_path_or_link: Path to the Excel file
            sheet_name: Name of the sheet to read (optional)
            **options: Additional options
            
        Returns:
            PySpark DataFrame
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA INGESTION - EXCEL (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting Excel data ingestion from: {file_path_or_link}")
        
        try:
            # For Excel files, we need to use pandas as an intermediary
            # In production, consider using spark-excel library
            logger.info("⚠ Note: Using pandas for Excel reading, then converting to PySpark")
            
            ############### PANDAS CODES ###########################
            # df = pd.read_excel(file_path_or_link)
            
            ############### PYSPARK CODES ###########################
            # Read Excel with pandas first
            pandas_df = pd.read_excel(file_path_or_link, sheet_name=sheet_name)
            
            # Convert to PySpark DataFrame
            df = self.spark.createDataFrame(pandas_df)
            
            # Get DataFrame info
            row_count = df.count()
            columns = df.columns
            
            ############### PANDAS CODES ###########################
            # logger.info(f"✓ Successfully loaded Excel data - Shape: {df.shape}, Columns: {list(df.columns)}")
            # logger.info(f"✓ Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            ############### PYSPARK CODES ###########################
            logger.info(f"✓ Successfully loaded Excel data - Shape: ({row_count}, {len(columns)})")
            logger.info(f"✓ Columns: {columns}")
            logger.info(f"✓ Partitions: {df.rdd.getNumPartitions()}")
            
            logger.info(f"{'='*60}\n")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Failed to load Excel data from {file_path_or_link}: {str(e)}")
            logger.info(f"{'='*60}\n")
            raise


class DataIngestorParquet(DataIngestor):
    """PySpark Parquet data ingestion implementation (new for PySpark)."""
    
    def ingest(self, file_path_or_link: str, **options) -> DataFrame:
        """
        Ingest Parquet data using PySpark.
        Note: Parquet is a columnar format optimized for big data processing.
        
        Args:
            file_path_or_link: Path to the Parquet file or directory
            **options: Additional options for Parquet reading
            
        Returns:
            PySpark DataFrame
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA INGESTION - PARQUET (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting Parquet data ingestion from: {file_path_or_link}")
        
        try:
            # Read Parquet file(s)
            df = self.spark.read.options(**options).parquet(file_path_or_link)
            
            # Get DataFrame info
            row_count = df.count()
            columns = df.columns
            
            # Parquet files are already compressed and optimized
            logger.info(f"✓ Successfully loaded Parquet data - Shape: ({row_count}, {len(columns)})")
            logger.info(f"✓ Columns: {columns}")
            logger.info(f"✓ Partitions: {df.rdd.getNumPartitions()}")
            logger.info(f"✓ Schema: {df.schema.simpleString()}")
            logger.info(f"{'='*60}\n")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Failed to load Parquet data from {file_path_or_link}: {str(e)}")
            logger.info(f"{'='*60}\n")
            raise


class DataIngestorFactory:
    """Factory class to create appropriate data ingestor based on file type."""
    
    @staticmethod
    def get_ingestor(file_path: str, spark: Optional[SparkSession] = None) -> DataIngestor:
        """
        Get appropriate data ingestor based on file extension.
        
        Args:
            file_path: Path to the data file
            spark: Optional SparkSession
            
        Returns:
            DataIngestor: Appropriate ingestor instance
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.csv':
            return DataIngestorCSV(spark)
        elif file_extension in ['.xlsx', '.xls']:
            return DataIngestorExcel(spark)
        elif file_extension == '.parquet':
            return DataIngestorParquet(spark)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")