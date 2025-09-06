import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import logging
from sklearn.metrics import (
                            accuracy_score,
                            precision_score,
                            recall_score,
                            f1_score,
                            confusion_matrix,
                            )

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(
                self,
                model,
                model_name
                ):
        self.model = model 
        self.model_name = model_name
        self.evaluation_results = {}

    def evaluate(
                self,
                X_test,
                Y_test
                ):
        Y_pred = self.model.predict(X_test)

        cm = confusion_matrix(Y_test, Y_pred)
        accuracy = accuracy_score(Y_test, Y_pred)
        precision = precision_score(Y_test, Y_pred)
        recall = recall_score(Y_test, Y_pred)
        f1 = f1_score(Y_test, Y_pred)

        self.evaluation_results = {
                                    'cm' : cm,
                                    'accuracy' : accuracy,
                                    'precision' : precision,
                                    'recall' : recall,
                                    'f1' : f1
                                    }
        return self.evaluation_results