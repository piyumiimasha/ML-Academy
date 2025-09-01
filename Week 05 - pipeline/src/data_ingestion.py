import os
import pandas as pd
import logging
from abc import ABC, abstractmethod


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)




class DataIngestor(ABC):
    @abstractmethod
    def ingest(self, file_path_or_link: str) ->pd.DataFrame:
        pass


class DataIngestorCSV(DataIngestor):
    def ingest(self, file_path_or_link):
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA INGESTION - CSV")
        logger.info(f"{'='*60}")
        logger.info(f"Starting CSV data ingestion from: {file_path_or_link}")
        try:
            df = pd.read_csv(file_path_or_link)
            logger.info(f"✓ Successfully loaded CSV data - Shape: {df.shape}, Columns: {list(df.columns)}")
            logger.info(f"✓ Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            logger.info(f"{'='*60}\n")
            return df
        except Exception as e:
            logger.error(f"✗ Failed to load CSV data from {file_path_or_link}: {str(e)}")
            logger.info(f"{'='*60}\n")
            raise
    
class DataIngestorExcel(DataIngestor):
    def ingest(self, file_path_or_link):
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA INGESTION - EXCEL")
        logger.info(f"{'='*60}")
        logger.info(f"Starting Excel data ingestion from: {file_path_or_link}")
        try:
            df = pd.read_excel(file_path_or_link)
            logger.info(f"✓ Successfully loaded Excel data - Shape: {df.shape}, Columns: {list(df.columns)}")
            logger.info(f"✓ Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            logger.info(f"{'='*60}\n")
            return df
        except Exception as e:
            logger.error(f"✗ Failed to load Excel data from {file_path_or_link}: {str(e)}")
            logger.info(f"{'='*60}\n")
            raise
