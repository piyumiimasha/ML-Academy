import os
import sys
import logging
import pandas as pd
import joblib
from data_pipeline import data_pipeline
from utils.config import get_data_paths, get_model_config
from typing import Dict, Any, Tuple, Optional
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.model_building import XGboostModelBuilder
from src.model_training import ModelTrainer
from src.model_evaluation import ModelEvaluator
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from utils.config import get_model_config
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

    X_train = pd.read_csv(get_data_paths()['X_train'])
    y_train = pd.read_csv(get_data_paths()['y_train'])
    X_test = pd.read_csv(get_data_paths()['X_test'])
    y_test = pd.read_csv(get_data_paths()['y_test'])

    model_builder = XGboostModelBuilder(**model_params)
    model = model_builder.build_model()

    trainer = ModelTrainer()
    model, train_score = trainer.train_simple(
        model=model,
        X_train=X_train,
        y_train=y_train.squeeze()
    )

    trainer.save_model(model, model_path)

    evaluator = ModelEvaluator(model, 'XGboost')
    evaluator.evaluate(X_test, y_test)

    print("Training Score:", train_score)

if __name__ == '__main__':
    model_config = get_model_config()
    model_params=model_config.get('model_params')
    print("Model Parameters:")
    print(model_params)
    training_pipeline(model_params=model_params)



    