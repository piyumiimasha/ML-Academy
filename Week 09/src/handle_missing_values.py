"""
Missing value handling strategies for both pandas and PySpark DataFrames.
Students can see the differences between pandas and PySpark implementations.
"""

import groq
import logging
from enum import Enum
from typing import Optional, List, Union
from dotenv import load_dotenv
from pydantic import BaseModel
from abc import ABC, abstractmethod
import pandas as pd  # Keep for educational comparison
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from pyspark.ml.feature import Imputer
from utils.spark_session import get_or_create_spark_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()


class MissingValueHandlingStrategy(ABC):
    """Abstract base class for missing value handling strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def handle(self, df: DataFrame) -> DataFrame:
        """Handle missing values in the DataFrame."""
        pass


class DropMissingValuesStrategy(MissingValueHandlingStrategy):
    """Strategy to drop rows with missing values in critical columns."""
    
    def __init__(self, critical_columns: List[str] = None, spark: Optional[SparkSession] = None):
        """
        Initialize the drop strategy.
        
        Args:
            critical_columns: List of column names where nulls are not allowed
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.critical_columns = critical_columns or []
        logger.info(f"Initialized DropMissingValuesStrategy for columns: {self.critical_columns}")

    def handle(self, df: DataFrame) -> DataFrame:
        """
        Drop rows with missing values in critical columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with rows dropped
        """
        ############### PANDAS CODES ###########################
        # initial_count = len(df)
        
        ############### PYSPARK CODES ###########################
        initial_count = df.count()
        
        if self.critical_columns:
            ############### PANDAS CODES ###########################
            # df_cleaned = df.dropna(subset=self.critical_columns)
            
            ############### PYSPARK CODES ###########################
            # Drop rows where any critical column has null
            df_cleaned = df.dropna(subset=self.critical_columns)
        else:
            # Drop rows with any null values
            df_cleaned = df.dropna()
        
        ############### PANDAS CODES ###########################
        # final_count = len(df_cleaned)
        # n_dropped = initial_count - final_count
        
        ############### PYSPARK CODES ###########################
        final_count = df_cleaned.count()
        n_dropped = initial_count - final_count
        
        logger.info(f"✓ Dropped {n_dropped} rows with missing values")
        logger.info(f"  • Initial rows: {initial_count}")
        logger.info(f"  • Final rows: {final_count}")
        
        return df_cleaned


class Gender(str, Enum):
    """Gender enumeration."""
    MALE = 'Male'
    FEMALE = 'Female'


class GenderPrediction(BaseModel):
    """Gender prediction model."""
    firstname: str
    lastname: str
    pred_gender: Gender


class GenderImputer:
    """Imputer that uses Groq API to predict gender based on names."""
    
    def __init__(self):
        """Initialize with Groq client."""
        self.groq_client = groq.Groq()
        self._predictions_cache = {}

    def _predict_gender(self, firstname: str, lastname: str) -> str:
        """
        Predict gender using Groq API.
        
        Args:
            firstname: First name
            lastname: Last name
            
        Returns:
            Predicted gender ('Male' or 'Female')
        """
        # Check cache first
        cache_key = f"{firstname}_{lastname}".lower()
        if cache_key in self._predictions_cache:
            return self._predictions_cache[cache_key]
        
        try:
            prompt = f"""
                What is the most likely gender (Male or Female) for someone with the first name '{firstname}'
                and last name '{lastname}' ?

                Your response only consists of one word: Male or Female
                """
            
            response = self.groq_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "user", "content": prompt}],
            )
            
            predicted_gender = response.choices[0].message.content.strip()
            
            # Validate prediction
            prediction = GenderPrediction(
                firstname=firstname, 
                lastname=lastname, 
                pred_gender=predicted_gender
            )
            
            # Cache the result
            self._predictions_cache[cache_key] = prediction.pred_gender
            
            logger.info(f'Predicted gender for {firstname} {lastname}: {prediction.pred_gender}')
            return prediction.pred_gender
            
        except Exception as e:
            logger.error(f"Error predicting gender for {firstname} {lastname}: {str(e)}")
            return None
    
    def impute(self, df: DataFrame) -> DataFrame:
        """
        Impute missing gender values using API predictions.
        
        Args:
            df: PySpark DataFrame with Gender, Firstname, and Lastname columns
            
        Returns:
            DataFrame with imputed gender values
        """
        ############### PANDAS CODES ###########################
        # missing_gender_index = df['Gender'].isnull()
        # for idx in df[missing_gender_index].index:
        #     first_name = df.loc[idx, 'Firstname']
        #     last_name = df.loc[idx, 'Lastname']
        #     gender = self._predict_gender(first_name, last_name)
        #     if gender:
        #         df.loc[idx, 'Gender'] = gender
        
        ############### PYSPARK CODES ###########################
        # Create a UDF for gender prediction
        predict_gender_udf = F.udf(self._predict_gender, StringType())
        
        # Identify rows with missing gender
        missing_gender_df = df.filter(
            F.col('Gender').isNull() | (F.col('Gender') == '')
        ).select('Firstname', 'Lastname')
        
        missing_count = missing_gender_df.count()
        
        if missing_count == 0:
            logger.info("No missing gender values to impute")
            return df
        
        logger.info(f"Imputing {missing_count} missing gender values...")
        
        # Predict genders for missing values
        predictions_df = missing_gender_df.withColumn(
            'PredictedGender',
            predict_gender_udf(F.col('Firstname'), F.col('Lastname'))
        )
        
        # Join predictions back to original dataframe
        df_with_predictions = df.join(
            predictions_df,
            on=['Firstname', 'Lastname'],
            how='left'
        )
        
        # Fill missing gender with predictions
        df_imputed = df_with_predictions.withColumn(
            'Gender',
            F.when(
                F.col('Gender').isNull() | (F.col('Gender') == ''),
                F.col('PredictedGender')
            ).otherwise(F.col('Gender'))
        ).drop('PredictedGender')
        
        logger.info(f"✓ Gender imputation completed for {missing_count} rows")
        
        return df_imputed


class FillMissingValuesStrategy(MissingValueHandlingStrategy):
    """
    Strategy to fill missing values using various methods.
    Supports mean/median/mode filling and custom imputers.
    """
    
    def __init__(
        self, 
        method: str = 'mean', 
        fill_value: Optional[Union[str, float, int]] = None, 
        relevant_column: Optional[str] = None, 
        is_custom_imputer: bool = False,
        custom_imputer: Optional[object] = None,
        spark: Optional[SparkSession] = None
    ):
        """
        Initialize the fill strategy.
        
        Args:
            method: Method to use ('mean', 'median', 'mode', 'constant')
            fill_value: Value to use for constant filling
            relevant_column: Column to fill (if None, fills all numeric columns)
            is_custom_imputer: Whether to use a custom imputer
            custom_imputer: Custom imputer object (must have impute method)
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.method = method
        self.fill_value = fill_value
        self.relevant_column = relevant_column
        self.is_custom_imputer = is_custom_imputer
        self.custom_imputer = custom_imputer

    def handle(self, df: DataFrame) -> DataFrame:
        """
        Fill missing values based on the configured strategy.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with filled values
        """
        if self.is_custom_imputer and self.custom_imputer:
            return self.custom_imputer.impute(df)
        
        if self.relevant_column:
            # Fill specific column
            if self.method == 'mean':
                ############### PANDAS CODES ###########################
                # mean_value = df[self.relevant_column].mean()
                # df_filled = df.fillna({self.relevant_column: mean_value})
                
                ############### PYSPARK CODES ###########################
                # Calculate mean for the column
                mean_value = df.select(F.mean(F.col(self.relevant_column))).collect()[0][0]
                df_filled = df.fillna({self.relevant_column: mean_value})
                
                logger.info(f'✓ Filled missing values in {self.relevant_column} with mean: {mean_value:.2f}')
                
            elif self.method == 'median':
                ############### PANDAS CODES ###########################
                # median_value = df[self.relevant_column].median()
                # df_filled = df.fillna({self.relevant_column: median_value})
                
                ############### PYSPARK CODES ###########################
                # Calculate median for the column
                median_value = df.approxQuantile(self.relevant_column, [0.5], 0.01)[0]
                df_filled = df.fillna({self.relevant_column: median_value})
                
                logger.info(f'✓ Filled missing values in {self.relevant_column} with median: {median_value:.2f}')
                
            elif self.method == 'mode':
                ############### PANDAS CODES ###########################
                # mode_value = df[self.relevant_column].mode()[0]
                # df_filled = df.fillna({self.relevant_column: mode_value})
                
                ############### PYSPARK CODES ###########################
                # Calculate mode for the column
                mode_value = df.groupBy(self.relevant_column).count() \
                    .orderBy(F.desc('count')).first()[0]
                df_filled = df.fillna({self.relevant_column: mode_value})
                
                logger.info(f'✓ Filled missing values in {self.relevant_column} with mode: {mode_value}')
                
            elif self.method == 'constant' and self.fill_value is not None:
                df_filled = df.fillna({self.relevant_column: self.fill_value})
                logger.info(f'✓ Filled missing values in {self.relevant_column} with constant: {self.fill_value}')
                
            else:
                raise ValueError(f"Invalid method '{self.method}' or missing fill_value")
                
        else:
            # Fill all columns based on method
            if self.method == 'constant' and self.fill_value is not None:
                df_filled = df.fillna(self.fill_value)
                logger.info(f'✓ Filled all missing values with constant: {self.fill_value}')
            else:
                # Use Spark ML Imputer for mean/median on all numeric columns
                numeric_cols = [field.name for field in df.schema.fields 
                              if field.dataType.typeName() in ['integer', 'long', 'float', 'double']]
                
                if numeric_cols:
                    imputer = Imputer(
                        inputCols=numeric_cols,
                        outputCols=[f"{col}_imputed" for col in numeric_cols],
                        strategy=self.method if self.method in ['mean', 'median'] else 'mean'
                    )
                    
                    model = imputer.fit(df)
                    df_imputed = model.transform(df)
                    
                    # Replace original columns with imputed ones
                    for col in numeric_cols:
                        df_imputed = df_imputed.withColumn(col, F.col(f"{col}_imputed")) \
                            .drop(f"{col}_imputed")
                    
                    df_filled = df_imputed
                    logger.info(f'✓ Filled missing values in numeric columns using {self.method}')
                else:
                    df_filled = df
                    logger.warning('No numeric columns found for imputation')
        
        return df_filled