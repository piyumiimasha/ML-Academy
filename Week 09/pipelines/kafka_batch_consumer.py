#!/usr/bin/env python3
"""
Simplified Kafka Consumer with ML Predictions
Processes customer events with real-time ML inference
"""

import json
import logging
import argparse
import os
import sys
import time
from typing import Dict, Any
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from confluent_kafka import Consumer, Producer, KafkaError
from src.model_inference import ModelInference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INPUT_TOPIC = "churn_predictions"
OUTPUT_TOPIC = "churn_predictions_scored"
MODEL_PATH = "artifacts/models/spark_random_forest_model"


class MLKafkaConsumer:
    """Simplified ML Kafka Consumer"""
    
    def __init__(self):
        self.model = None
        
    def initialize(self):
        """Initialize ML model"""
        try:
            self.model = ModelInference(model_path=MODEL_PATH, use_spark=False)
            
            # Load encoders
            encoders_dir = "artifacts/encode"
            if os.path.exists(encoders_dir):
                self.model.load_encoders(encoders_dir)
                logger.info("✅ ML model and encoders loaded")
            
            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    def extract_customer_data(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate customer data"""
        # Handle nested structure
        customer_data = message_data.get('data', message_data)
        
        # Required fields with defaults
        return {
            'CustomerId': customer_data.get('CustomerId', 0),
            'Geography': customer_data.get('Geography', 'Unknown'),
            'Gender': customer_data.get('Gender', 'Unknown'),
            'Age': customer_data.get('Age', 0),
            'CreditScore': customer_data.get('CreditScore', 600),
            'Balance': customer_data.get('Balance', 0.0),
            'EstimatedSalary': customer_data.get('EstimatedSalary', 0.0),
            'Tenure': customer_data.get('Tenure', 0),
            'NumOfProducts': customer_data.get('NumOfProducts', 1),
            'HasCrCard': customer_data.get('HasCrCard', 0),
            'IsActiveMember': customer_data.get('IsActiveMember', 0),
            'Exited': customer_data.get('Exited', 0)
        }
    
    def process_batch(self, max_messages: int = 1000, timeout: int = 10, 
                     group_id: str = None) -> int:
        """Process batch of messages with ML predictions"""
        
        # Configure consumer
        if group_id is None:
            group_id = f"batch_consumer_{int(time.time())}"
        
        consumer_config = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': group_id,
            'auto.offset.reset': 'earliest' if 'batch_' in group_id else 'latest',
            'enable.auto.commit': True
        }
        
        consumer = Consumer(consumer_config)
        consumer.subscribe([INPUT_TOPIC])
        
        # Collect messages
        messages = []
        start_time = time.time()
        
        while len(messages) < max_messages and (time.time() - start_time) < timeout:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    break
                continue
            
            try:
                message_data = json.loads(msg.value().decode('utf-8'))
                messages.append(message_data)
            except json.JSONDecodeError:
                continue
        
        consumer.close()
        
        if not messages:
            logger.warning("⚠️ No messages to process")
            return 0
        
        # Process with ML
        logger.info(f"📥 Processing {len(messages)} messages with ML")
        
        # Setup producer for results
        producer = Producer({'bootstrap.servers': 'localhost:9092'})
        processed = 0
        
        print(f"\n📊 ML PREDICTIONS")
        print("=" * 70)
        print("Status | Customer   | Location | Prediction | Confidence")
        print("-" * 70)
        
        for i, message_data in enumerate(messages):
            try:
                # Extract customer data
                customer_data = self.extract_customer_data(message_data)
                customer_id = customer_data.get('CustomerId', 'N/A')
                geography = str(customer_data.get('Geography', 'N/A'))[:5]
                
                # Make prediction
                prediction = self.model.predict(customer_data)
                status = prediction.get('Status', 'Unknown')
                confidence = prediction.get('Confidence', '0%')
                
                # Display result
                pred_emoji = "🟢" if 'Retain' in status else "🔴"
                print(f"  {pred_emoji}   | {str(customer_id)[:8]:8s} | {geography:8s} | {status:10s} | {confidence:10s}")
                
                # Send result
                result = {
                    'customer_id': customer_id,
                    'original_data': customer_data,\
                    'prediction': prediction,
                    'processed_at': datetime.now().isoformat(),
                    'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                producer.produce(
                    topic=OUTPUT_TOPIC,
                    key=str(customer_id),
                    value=json.dumps(result, default=str)
                )
                
                processed += 1
                
            except Exception as e:
                print(f"  ❌   | ERROR    | ERROR    | FAILED     | ERROR")
                logger.error(f"Error processing message {i}: {str(e)}")
        
        producer.flush()
        
        print("-" * 70)
        print(f"✅ Completed: {processed}/{len(messages)} predictions")
        print("=" * 70)
        
        logger.info(f"🎉 Processed {processed} messages successfully")
        return processed
    
    def run_continuous(self, poll_interval: int = 3, show_progress: bool = True):
        """Run continuous processing"""
        logger.info("🔄 Starting continuous ML processing")
        logger.info("🛑 Press Ctrl+C to stop")
        
        total_processed = 0
        
        try:
            while True:
                if show_progress:
                    print(f"\n📡 Checking for new messages... (Total: {total_processed})")
                
                # Process new messages
                processed = self.process_batch(
                    max_messages=50,
                    timeout=poll_interval,
                    group_id='continuous_ml_consumer'
                )
                
                if processed > 0:
                    total_processed += processed
                    print(f"✅ Processed {processed} new messages (Total: {total_processed})")
                else:
                    if show_progress:
                        print("⏳ No new messages - waiting...")
                    else:
                        print(".", end="", flush=True)
                
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info(f"🛑 Continuous processing stopped (Total: {total_processed})")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Kafka Consumer with ML Predictions")
    parser.add_argument('--max-messages', type=int, default=1000)
    parser.add_argument('--timeout', type=int, default=10)
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--poll-interval', type=int, default=3)
    parser.add_argument('--quiet', action='store_true')
    
    args = parser.parse_args()
    
    try:
        logger.info("🚀 Starting Kafka ML Consumer")
        
        consumer = MLKafkaConsumer()
        if not consumer.initialize():
            return 1
        
        if args.continuous:
            consumer.run_continuous(args.poll_interval, not args.quiet)
        else:
            processed = consumer.process_batch(args.max_messages, args.timeout)
            return 0 if processed > 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Consumer failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())