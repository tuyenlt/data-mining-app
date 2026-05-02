# 🛡 Fraud Detection App

Ứng dụng phát hiện giao dịch gian lận sử dụng Machine Learning, xây dựng bằng Python và CustomTkinter.

## 📸 Tính năng

- **Dự đoán giao dịch** — Nhập tay hoặc import CSV, hiển thị kết quả kèm xác suất gian lận
- **Quản lý Model** — So sánh các model theo Recall, Precision, F1, Accuracy
- **Train Model** — Hỗ trợ 3 thuật toán: Random Forest, XGBoost, Logistic Regression
- **Giao diện hiện đại** — Dark theme, custom icons, modal dialogs

## 📁 Cấu trúc

```
DataMinningApp/
├── main.py                  # Entry point
├── data/                    # Dữ liệu CSV train
├── models/                  # Model đã train (.pkl + .txt)
├── predictions/             # Kết quả dự đoán xuất ra
├── src/
│   ├── assets/icons/        # Icon PNG cho giao diện
│   ├── components/widgets.py # UI components (DataTable, ModernDialog...)
│   ├── config/
│   │   ├── AppConfig.py     # Đường dẫn, cấu hình
│   │   ├── theme.py         # Màu sắc, font chữ
│   │   └── icons.py         # Quản lý icon tập trung
│   ├── services/
│   │   ├── DataPreprocessingService.py  # Tiền xử lý dữ liệu
│   │   ├── ModelTrainningService.py     # Train model (RF, XGB, LR)
│   │   └── ModelPredictionService.py    # Dự đoán + xác suất
│   └── views/
│       ├── ModelView.py      # Trang quản lý & train model
│       └── PredictionView.py # Trang dự đoán giao dịch
└── requirements.txt
```         

## 🚀 Cài đặt & Chạy

```bash
# Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies (có version cố định)
pip install -r requirements.txt

# Hoặc cài không version (linh hoạt hơn)
pip install -r requirements-dev.txt

# Chạy app
python3 main.py
```

## 🛠 Công nghệ

| Thành phần | Công nghệ |
|---|---|
| GUI | CustomTkinter + PIL |
| ML | scikit-learn, XGBoost, imbalanced-learn (SMOTE) |
| Data | pandas, numpy |
| Serialization | joblib |

## 📊 Workflow

1. Đặt file CSV vào `data/` (hoặc chọn qua giao diện)
2. Vào tab **Quản lý Model** → chọn thuật toán → **Bắt đầu Train**
3. Vào tab **Dự đoán** → chọn model → nhập dữ liệu hoặc import CSV → **Dự đoán**
4. Xem kết quả với cột `prediction_label` và `fraud_prob`, lưu CSV nếu cần
