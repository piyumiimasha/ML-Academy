import os
import sys
import logging
import pandas as pd
import joblib
from data_pipeline import data_pipeline
from config import get_data_paths, get_model_config
from typing import Dict, Any, Tuple, Optional
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_building import XGboostModelBuilder
from model_training import ModelTrainer
# from model_evaluation import ModelEvaluator
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from config import get_model_config
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def training_pipeline(
                    data_path: str = 'data/raw/ChurnModelling.csv',
                    model_params: Optional[Dict[str, Any]] = None,
                    test_size: float = 0.2, random_state: int = 42,
                    model_path: str = 'artifacts/models/churn_analysis.joblib',
                    ):
    if (not os.path.exists(get_data_paths()['X_train'])) or \
        (not os.path.exists(get_data_paths()['X_test'])) or \
        (not os.path.exists(get_data_paths()['y_train'])) or \
        (not os.path.exists(get_data_paths()['y_test'])):
        
        data_pipeline()
    else:
        print("Loading Data Artifacts from Data Pipeline.")

training_pipeline()
    