import os
import time
from datetime import datetime
import joblib
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report
from src.config.AppConfig import AppConfig
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, recall_score, precision_score, f1_score, accuracy_score
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from src.services.ModelUtils import TargetEncoder, encode_gender

class ModelTrainningService:
    def __init__(self):
        pass
    
    def _get_next_version(self, prefix: str) -> int:
        """Scan MODEL_OUT_DIR and return the next model version number for a given prefix."""
        import re
        model_dir = AppConfig.MODEL_OUT_DIR
        if not os.path.exists(model_dir):
            return 1
        # Tìm pattern: prefix_v(số)_
        pattern = re.compile(rf'{prefix}_v(\d+)_')
        max_v = 0
        for fname in os.listdir(model_dir):
            m = pattern.search(fname)
            if m:
                max_v = max(max_v, int(m.group(1)))
        return max_v + 1
    
    def splitData(self, df: pd.DataFrame):
        X = df.drop(columns=['is_fraud'])
        y = df['is_fraud']

        X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

        print("X_train shape:", X_train.shape)
        print("X_test shape:", X_test.shape)
        print("y_train shape:", y_train.shape)
        print("y_test shape:", y_test.shape)

        # # Xử lý số

        # numeric_cols = ['amt', 'city_pop', 'age', 'hour', 'day_of_week', 'distance']
        # scaler = StandardScaler()
        # # Fit trên train
        # scaler.fit(X_train[numeric_cols])

        # # Transform
        # X_train[numeric_cols] = scaler.transform(X_train[numeric_cols])
        # X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])

        # def encode_gender(df):
        #     df = df.copy()
        #     df['gender'] = df['gender'].map({'M': 0, 'F': 1})
        #     return df

        # X_train = encode_gender(X_train)
        # X_test = encode_gender(X_test)  

        # target_cols = ['merchant', 'job']

        # # Tính mapping từ TRAIN
        # target_maps = {}
        # global_mean = y_train.mean()

        # for col in target_cols:
        #     mapping = X_train.join(y_train).groupby(col)['is_fraud'].mean()
        #     target_maps[col] = mapping

        # # Apply cho TRAIN
        # for col in target_cols:
        #     X_train[col] = X_train[col].map(target_maps[col])
        #     X_train[col] = X_train[col].fillna(global_mean)

        # # Apply cho TEST
        # for col in target_cols:
        #     X_test[col] = X_test[col].map(target_maps[col])
        #     X_test[col] = X_test[col].fillna(global_mean)

        # categorical_onehot = ['category']

        # ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

        # # Fit trên train
        # ohe.fit(X_train[categorical_onehot])

        # # Transform
        # X_train_ohe = ohe.transform(X_train[categorical_onehot])
        # X_test_ohe = ohe.transform(X_test[categorical_onehot])

        return (X_train, X_test, y_train, y_test)

    def startRandomForest(self, X_train, X_test, y_train, y_test):

        categorical_onehot = ['category']
        target_cols = ['merchant', 'job']
        numeric_cols = ['amt', 'city_pop', 'age', 'hour', 'day_of_week', 'distance']

        # Định nghĩa các bước pipeline
        steps = [
            ('gender', FunctionTransformer(encode_gender)),
            ('target_encode', TargetEncoder(cols=target_cols)),
            ('column_transformer', ColumnTransformer([
                ('onehot', OneHotEncoder(handle_unknown='ignore'), categorical_onehot),
                ('num', StandardScaler(), numeric_cols)
            ], remainder='passthrough')),
            ('smote', SMOTE()),
            ('model', RandomForestClassifier(verbose=1, n_jobs=-1))
        ]

        total_steps = len(steps)
        total_start = time.time()

        # Train từng bước thủ công để theo dõi tiến trình
        X_current, y_current = X_train.copy(), y_train.copy()

        fitted_steps = []
        for i, (name, step) in enumerate(steps):
            step_start = time.time()
            print(f"\n{'='*60}")
            print(f"[{i+1}/{total_steps}] Đang chạy bước: '{name}'...")
            print(f"  - Dữ liệu đầu vào: {X_current.shape if hasattr(X_current, 'shape') else 'N/A'}")

            if name == 'model':
                # Bước cuối: fit model
                step.fit(X_current, y_current)
            elif hasattr(step, 'fit_resample'):
                # SMOTE: fit_resample trả về (X, y) đã resample
                X_current, y_current = step.fit_resample(X_current, y_current)
                print(f"  - Dữ liệu sau resample: {X_current.shape}")
            else:
                # Các bước transform thông thường
                step.fit(X_current, y_current)
                X_current = step.transform(X_current)

            fitted_steps.append((name, step))

            step_elapsed = time.time() - step_start
            print(f"  ✓ Hoàn thành '{name}' trong {step_elapsed:.2f}s")

        total_elapsed = time.time() - total_start
        print(f"\n{'='*60}")
        print(f"✅ TỔNG THỜI GIAN TRAIN: {total_elapsed:.2f}s ({total_elapsed/60:.1f} phút)")
        print(f"{'='*60}")

        # Tạo lại pipeline đã fit để lưu
        rf_pipeline = Pipeline(fitted_steps)

        # Predict
        print("\n🔍 Đang predict trên tập test...")
        pred_start = time.time()
        rf_y_pred = rf_pipeline.predict(X_test)
        print(f"  ✓ Predict xong trong {time.time() - pred_start:.2f}s")

        # Naming convention: random_forest_v(x)_(timestamp).pkl
        prefix = "random_forest"
        version = self._get_next_version(prefix)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{prefix}_v{version}_{timestamp}"
        
        joblib.dump(rf_pipeline, AppConfig.MODEL_OUT_DIR + f"/{model_filename}.pkl")
        print(f"\n💾 Model đã lưu: {model_filename}.pkl")
        
        smote_rf_Recall = recall_score(y_test, rf_y_pred)
        smote_rf_Precision = precision_score(y_test, rf_y_pred)
        smote_rf_f1 = f1_score(y_test, rf_y_pred)

        rdf = [(smote_rf_Recall, smote_rf_Precision, smote_rf_f1)]

        rf_score = pd.DataFrame(data = rdf, columns=['Recall','Precision','F1 Score'])
        print(f"\n📊 Score:")
        print(rf_score)
        
        with open(AppConfig.MODEL_OUT_DIR + f"/{model_filename}.txt", "w") as f:
            f.write(rf_score.to_string(index=False))
        return rf_pipeline

    def startXGBoost(self, X_train, X_test, y_train, y_test):

        categorical_onehot = ['category']
        target_cols = ['merchant', 'job']
        numeric_cols = ['amt', 'city_pop', 'age', 'hour', 'day_of_week', 'distance']

        # Định nghĩa các bước pipeline
        steps = [
            ('gender', FunctionTransformer(encode_gender)),
            ('target_encode', TargetEncoder(cols=target_cols)),
            ('column_transformer', ColumnTransformer([
                ('onehot', OneHotEncoder(handle_unknown='ignore'), categorical_onehot),
                ('num', StandardScaler(), numeric_cols)
            ], remainder='passthrough')),
            ('smote', SMOTE(k_neighbors=5)),
            ('model', XGBClassifier(verbosity=1, n_jobs=-1,learning_rate= 0.3, max_depth= 6, n_estimators = 400))
        ]

        total_steps = len(steps)
        total_start = time.time()

        # Train từng bước thủ công để theo dõi tiến trình
        X_current, y_current = X_train.copy(), y_train.copy()

        fitted_steps = []
        for i, (name, step) in enumerate(steps):
            step_start = time.time()
            print(f"\n{'='*60}")
            print(f"[{i+1}/{total_steps}] Đang chạy bước: '{name}'...")
            print(f"  - Dữ liệu đầu vào: {X_current.shape if hasattr(X_current, 'shape') else 'N/A'}")

            if name == 'model':
                # Bước cuối: fit model
                step.fit(X_current, y_current)
            elif hasattr(step, 'fit_resample'):
                # SMOTE: fit_resample trả về (X, y) đã resample
                X_current, y_current = step.fit_resample(X_current, y_current)
                print(f"  - Dữ liệu sau resample: {X_current.shape}")
            else:
                # Các bước transform thông thường
                step.fit(X_current, y_current)
                X_current = step.transform(X_current)

            fitted_steps.append((name, step))

            step_elapsed = time.time() - step_start
            print(f"  ✓ Hoàn thành '{name}' trong {step_elapsed:.2f}s")

        total_elapsed = time.time() - total_start
        print(f"\n{'='*60}")
        print(f"✅ TỔNG THỚI GIAN TRAIN XGBOOST: {total_elapsed:.2f}s ({total_elapsed/60:.1f} phút)")
        print(f"{'='*60}")

        # Tạo lại pipeline đã fit để lưu
        xg_pipeline = Pipeline(fitted_steps)

        # Predict
        print("\n🔍 Đang predict trên tập test...")
        pred_start = time.time()
        xg_y_pred = xg_pipeline.predict(X_test)
        print(f"  ✓ Predict xong trong {time.time() - pred_start:.2f}s")

        # Đặt tên model: xgboost_v(x)_(timestamp).pkl
        prefix = "xgboost"
        version = self._get_next_version(prefix)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{prefix}_v{version}_{timestamp}"
        joblib.dump(xg_pipeline, AppConfig.MODEL_OUT_DIR + f"/{model_filename}.pkl")
        print(f"\n💾 Model đã lưu: {model_filename}.pkl")

        smote_xg_recall = recall_score(y_test, xg_y_pred)
        smote_xg_precision = precision_score(y_test, xg_y_pred)
        smote_xg_f1 = f1_score(y_test, xg_y_pred)

        xg = [(smote_xg_recall, smote_xg_precision, smote_xg_f1)]

        xg_score = pd.DataFrame(data=xg, columns=['Recall', 'Precision', 'F1 Score'])
        print(f"\n📊 Score:")
        print(xg_score)

        with open(AppConfig.MODEL_OUT_DIR + f"/{model_filename}.txt", "w") as f:
            f.write(xg_score.to_string(index=False))
        return xg_pipeline
    
    def startLogisticRegression(self, X_train, X_test, y_train, y_test):
        categorical_onehot = ['category']
        target_cols = ['merchant', 'job']
        numeric_cols = ['amt', 'city_pop', 'age', 'hour', 'day_of_week', 'distance']

        lr_pipeline = Pipeline([
            ('gender', FunctionTransformer(encode_gender)),
            ('target_encode', TargetEncoder(cols=target_cols)),
            ('column_transformer', ColumnTransformer([
                ('onehot', OneHotEncoder(handle_unknown='ignore'), categorical_onehot),
                ('num', StandardScaler(), numeric_cols)
            ], remainder='passthrough')),
            ('smote', SMOTE()),
            ('model', LogisticRegression(
                max_iter=1000,
                n_jobs=-1
            ))
        ])

        lr_pipeline.fit(X_train, y_train)

        lr_y_pred = lr_pipeline.predict(X_test)

        # Naming convention: logistic_regression_v(x)_(timestamp).pkl
        prefix = "logistic_regression"
        version = self._get_next_version(prefix)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{prefix}_v{version}_{timestamp}"
        
        joblib.dump(lr_pipeline, AppConfig.MODEL_OUT_DIR + f"/{model_filename}.pkl")
        print(f"\n💾 Model đã lưu: {model_filename}.pkl")

        smote_lr_recall = recall_score(y_test, lr_y_pred)
        smote_lr_precision = precision_score(y_test, lr_y_pred)
        smote_lr_f1 = f1_score(y_test, lr_y_pred)

        lr = [(smote_lr_recall, smote_lr_precision, smote_lr_f1)]

        lr_score = pd.DataFrame(data=lr, columns=['Recall', 'Precision', 'F1 Score'])
        print(f"\n Score:")
        print(lr_score)

        with open(AppConfig.MODEL_OUT_DIR + f"/{model_filename}.txt", "w") as f:
            f.write(lr_score.to_string(index=False))
        return lr_pipeline

    def train(self, df: pd.DataFrame):
        pass



