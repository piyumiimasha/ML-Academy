import os
import sys
import json
import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from model_inference import ModelInference
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from mlflow_utils import MLflowTracker, create_mlflow_run_tags
import mlflow


def initialize_inference_system(
    model_path: str = 'artifacts/models/spark_random_forest_model',
    encoders_path: str = 'artifacts/encode'
) -> ModelInference:
    """
    Initialize the global inference system with model and encoders.
    """
    logger.info("Initializing global inference system...")
    logger.info(f"\n{'='*80}")
    logger.info(f"INITIALIZING STREAMING INFERENCE SYSTEM")
    logger.info(f"{'='*80}")
    
    try:
        # Create ModelInference instance
        logger.info("Creating ModelInference instance...")
        inference = ModelInference(model_path)
        
        # Load encoders
        logger.info(f"Loading encoders from: {encoders_path}")
        inference.load_encoders(encoders_path)
        
        logger.info("✓ Streaming inference system initialized successfully")
        return inference
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize inference system: {str(e)}")
        raise


def streaming_inference(inference: ModelInference, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Perform streaming inference on input data with MLflow tracking.
    """
    # Start MLflow tracking
    mlflow_tracker = MLflowTracker()
    run_tags = create_mlflow_run_tags('streaming_inference', {
        'inference_type': 'single_record',
        'model_type': 'XGBoost'
    })
    run = mlflow_tracker.start_run(run_name='streaming_inference', tags=run_tags)
    logger.info("✓ Inference tracking run started")
    logger.info(f"{'='*80}\n")
    
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"STREAMING INFERENCE REQUEST")
        logger.info(f"{'='*70}")
        logger.info("Processing inference request...")
        logger.info(f"Input data keys: {list(data.keys())}")
        
        # Measure inference time
        start_time = time.time()
        
        # Make prediction
        prediction_result = inference.predict(data)
        
        end_time = time.time()
        inference_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Log inference metrics to MLflow
        mlflow.log_metrics({
            'inference_time_ms': inference_time,
            'churn_probability': float(prediction_result['Confidence'].replace('%', '')) / 100,
            'predicted_class': 1 if prediction_result['Status'] == 'Churn' else 0
        })
        
        # Log input features as parameters
        mlflow.log_params({f'input_{k}': v for k, v in data.items()})
        
        logger.info("✓ Streaming inference completed successfully")
        logger.info(f"Result: {prediction_result}")
        logger.info(f"Inference time: {inference_time:.2f}ms")
        logger.info(f"{'='*70}")
        
        return prediction_result
        
    except Exception as e:
        logger.error(f"✗ Streaming inference failed: {str(e)}")
        raise
    finally:
        mlflow_tracker.end_run()


# Sample data for testing
sample_data = {
    "RowNumber": 1,
    "CustomerId": 15634602,
    "Firstname": "Grace",
    "Lastname": "Williams",
    "CreditScore": 619,
    "Geography": "France",
    "Gender": "Female",
    "Age": 42,
    "Tenure": 2,
    "Balance": 0,
    "NumOfProducts": 1,
    "HasCrCard": 1,
    "IsActiveMember": 1,
    "EstimatedSalary": 101348.88
}

if __name__ == "__main__":
    # Initialize inference system
    inference = initialize_inference_system()
    
    # Perform streaming inference
    pred = streaming_inference(inference, sample_data)
    print(pred)