import os
import joblib

class ModelTrainer:
    def train_simple(self, model, X_train, y_train):
        model.fit(X_train, y_train)
        train_score = model.score(X_train, y_train)
        return model, train_score

    def save_model(self, model, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(model, filepath)

    def load_model(self, filepath: str):
        return joblib.load(filepath)