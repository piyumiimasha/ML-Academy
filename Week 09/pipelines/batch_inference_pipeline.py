#!/usr/bin/env python3
"""
Batch Inference Pipeline

This pipeline performs batch inference on processed data using the trained model.
Replaces the streaming inference pipeline with a simpler batch approach.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import project modules
from src.model_inference import ModelInference
from utils.spark_session import create_spark_session
from utils.config import load_config
from utils.mlflow_utils import start_mlflow_run, end_mlflow_run, log_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchInferencePipeline:
    """Batch inference pipeline for ML predictions"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the batch inference pipeline"""
        self.config = load_config()
        self.model_inference = None
        self.spark = None
        
    def initialize(self):
        """Initialize components"""
        try:
            logger.info("🚀 Initializing Batch Inference Pipeline")
            logger.info("=" * 60)
            
            # Initialize Spark session
            self.spark = create_spark_session("BatchInferencePipeline")
            logger.info("✅ Spark session initialized")
            
            # Initialize model inference
            model_path = "artifacts/models/spark_random_forest_model"
            self.model_inference = ModelInference(
                model_path=model_path, 
                use_spark=True, 
                spark=self.spark
            )
            logger.info("✅ Model inference initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    def load_test_data(self) -> pd.DataFrame:
        """Load test data for batch inference"""
        try:
            logger.info("📊 Loading test data for inference...")
            
            # Check for existing test data
            test_data_path = Path("artifacts/data/X_test.csv")
            if test_data_path.exists():
                df = pd.read_csv(test_data_path)
                logger.info(f"✅ Loaded test data: {df.shape}")
                return df
            else:
                # Load raw data and take a sample for inference
                raw_data_path = Path("data/raw/ChurnModelling.csv")
                if raw_data_path.exists():
                    df = pd.read_csv(raw_data_path)
                    # Take a sample for inference
                    sample_df = df.sample(n=min(100, len(df)), random_state=42)
                    logger.info(f"✅ Loaded sample data for inference: {sample_df.shape}")
                    return sample_df
                else:
                    raise FileNotFoundError("No data available for inference")
                    
        except Exception as e:
            logger.error(f"❌ Error loading test data: {str(e)}")
            raise
    
    def run_batch_inference(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run batch inference on the data"""
        try:
            logger.info("🔮 Running batch inference...")
            logger.info(f"📊 Processing {len(data)} records")
            
            predictions = []
            successful_predictions = 0
            
            # Process each record
            for idx, row in data.iterrows():
                try:
                    # Convert row to dictionary
                    record_dict = row.to_dict()
                    
                    # Make prediction
                    prediction = self.model_inference.predict(record_dict)
                    
                    # Combine original data with prediction
                    result = {
                        **record_dict,
                        **prediction,
                        'processed_at': datetime.now().isoformat(),
                        'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'record_index': idx
                    }
                    
                    predictions.append(result)
                    successful_predictions += 1
                    
                    if successful_predictions % 25 == 0:
                        logger.info(f"📈 Processed {successful_predictions}/{len(data)} records")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process record {idx}: {str(e)}")
                    continue
            
            # Convert to DataFrame
            results_df = pd.DataFrame(predictions)
            
            logger.info(f"✅ Batch inference completed")
            logger.info(f"📊 Successfully processed: {successful_predictions}/{len(data)} records")
            
            return results_df
            
        except Exception as e:
            logger.error(f"❌ Error in batch inference: {str(e)}")
            raise
    
    def save_results(self, results_df: pd.DataFrame):
        """Save inference results"""
        try:
            logger.info("💾 Saving inference results...")
            
            # Create output directory
            output_dir = Path("artifacts/inference_batches")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"batch_inference_results_{timestamp}.json"
            
            # Convert to JSON and save
            results_df.to_json(output_path, orient='records', indent=2)
            logger.info(f"✅ Results saved to: {output_path}")
            
            # Also save summary
            summary_path = output_dir / "latest_batch_inference.json"
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_records': len(results_df),
                'output_file': str(output_path),
                'sample_predictions': results_df.head(3).to_dict('records') if len(results_df) > 0 else []
            }
            
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"✅ Summary saved to: {summary_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            raise
    
    def run_pipeline(self):
        """Run the complete batch inference pipeline"""
        try:
            logger.info("🎯 STARTING BATCH INFERENCE PIPELINE")
            logger.info("=" * 60)
            
            # Start MLflow run
            run_id = start_mlflow_run("batch_inference_pipeline")
            
            # Initialize components
            if not self.initialize():
                raise Exception("Failed to initialize pipeline")
            
            # Load test data
            test_data = self.load_test_data()
            
            # Run inference
            results_df = self.run_batch_inference(test_data)
            
            # Save results
            self.save_results(results_df)
            
            # Log metrics to MLflow
            metrics = {
                'total_records': len(test_data),
                'successful_predictions': len(results_df),
                'success_rate': len(results_df) / len(test_data) if len(test_data) > 0 else 0
            }
            
            log_metrics(metrics)
            
            logger.info("🎉 Batch inference pipeline completed successfully!")
            logger.info(f"📊 Success rate: {metrics['success_rate']:.2%}")
            
            # End MLflow run
            end_mlflow_run()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            if 'run_id' in locals():
                end_mlflow_run()
            return False
        finally:
            if self.spark:
                self.spark.stop()
                logger.info("🔚 Spark session stopped")


def main():
    """Main function"""
    try:
        pipeline = BatchInferencePipeline()
        success = pipeline.run_pipeline()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import json
    exit(main())
