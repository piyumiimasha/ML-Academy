import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# PySpark imports
from pyspark.sql import DataFrame
from pyspark.ml import PipelineModel
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Original ModelEvaluator for scikit-learn models.
    """
    
    def __init__(self, model, model_name: str):
        self.model = model 
        self.model_name = model_name
        self.evaluation_results = {}

    def evaluate(self, X_test, Y_test):
        """Evaluate scikit-learn model performance."""
        logger.info(f"Evaluating {self.model_name} model...")
        
        Y_pred = self.model.predict(X_test)

        cm = confusion_matrix(Y_test, Y_pred)
        accuracy = accuracy_score(Y_test, Y_pred)
        precision = precision_score(Y_test, Y_pred)
        recall = recall_score(Y_test, Y_pred)
        f1 = f1_score(Y_test, Y_pred)

        self.evaluation_results = {
            'cm': cm,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        logger.info(f"✓ Accuracy: {accuracy:.4f}")
        logger.info(f"✓ Precision: {precision:.4f}")
        logger.info(f"✓ Recall: {recall:.4f}")
        logger.info(f"✓ F1-Score: {f1:.4f}")
        
        return self.evaluation_results


# ========================================================================================
# PYSPARK MLLIB MODEL EVALUATOR - Simple version matching original structure
# ========================================================================================

class SparkModelEvaluator:
    """
    PySpark MLlib model evaluator - simplified to match original ModelEvaluator structure.
    """
    
    def __init__(self, model: PipelineModel, model_name: str):
        self.model = model
        self.model_name = model_name
        self.evaluation_results = {}

    def evaluate(self, test_data: DataFrame):
        """Evaluate PySpark MLlib model performance."""
        logger.info(f"Evaluating {self.model_name} model...")
        
        # Make predictions
        predictions = self.model.transform(test_data)
        
        # Binary classification evaluator
        binary_evaluator = BinaryClassificationEvaluator(
            labelCol="label",
            rawPredictionCol="rawPrediction"
        )
        
        # Multiclass evaluator for additional metrics
        multiclass_evaluator = MulticlassClassificationEvaluator(
            labelCol="label",
            predictionCol="prediction"
        )
        
        # Calculate metrics
        auc = binary_evaluator.evaluate(predictions)
        accuracy = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "accuracy"})
        precision = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "weightedPrecision"})
        recall = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "weightedRecall"})
        f1 = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "f1"})
        
        self.evaluation_results = {
            'auc': auc,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        logger.info(f"✓ AUC: {auc:.4f}")
        logger.info(f"✓ Accuracy: {accuracy:.4f}")
        logger.info(f"✓ Precision: {precision:.4f}")
        logger.info(f"✓ Recall: {recall:.4f}")
        logger.info(f"✓ F1-Score: {f1:.4f}")
        
        return self.evaluation_results