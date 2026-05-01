from src.services.DataPreprocessingService import DataPreprocessingService
import joblib
import pandas as pd
from src.config.AppConfig import AppConfig
from datetime import datetime
import os


class ModelPredictionService:
    def __init__(self):
        self.model = None
        self.dataPreprocessingService = DataPreprocessingService()
    
    def load_model(self, modelPath: str):
        self.model = joblib.load(modelPath)
    
    def predict(self, df: pd.DataFrame):
        if self.model is None:
            print("Model not loaded, please load model first")
            return
        
        df_clean = self.dataPreprocessingService.clean(df)
        
        X = df_clean.drop(columns=['is_fraud'], errors='ignore')
        
        y_pred = self.model.predict(X)

        # Get confidence scores via predict_proba
        try:
            y_proba = self.model.predict_proba(X)
            # Probability of the predicted class (fraud=1)
            confidence = y_proba[:, 1]  # probability of fraud
        except Exception:
            confidence = [None] * len(y_pred)

        result = df.copy()
        result['prediction'] = y_pred
        result['prediction_label'] = result['prediction'].map({0: 'Hợp lệ', 1: 'Gian lận'})
        result['fraud_prob'] = confidence
        result['fraud_prob'] = result['fraud_prob'].apply(
            lambda x: f"{x*100:.2f}%" if x is not None else "N/A"
        )

        return result
    

    def save_result(self, df: pd.DataFrame, path: str = None):

        if path is None:
            os.makedirs(AppConfig.PREDICTION_OUT_DIR, exist_ok=True)
            path = AppConfig.PREDICTION_OUT_DIR + f"/prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df.to_csv(path, index=False)

        print(f"Result saved to {path}")
        return path

    
    def predict_from_csv(self, path: str, columnsMapping: dict = {}):
        if not os.path.exists(path):
            print("File not found")
            return None
        
        df = pd.read_csv(path)

        # mapping 
        if columnsMapping is not None and len(columnsMapping) > 0:
            df = df.rename(columns=columnsMapping)

        result = self.predict(df)

        return result