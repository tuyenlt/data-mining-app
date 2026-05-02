import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import threading

from src.config.theme import COLORS, FONTS
from src.config.AppConfig import AppConfig
from src.components.widgets import (
    StyledCard, StyledButton, StyledOptionMenu, DataTable,
    ProgressCard, MetricCard, show_info, show_warning
)
from src.services.ModelTrainningService import ModelTrainningService
from src.services.DataPreprocessingService import DataPreprocessingService
from src.config.icons import icon_md, icon_lg


class ModelView(ctk.CTkFrame):
    """View for managing, comparing, and retraining models."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.training_service = ModelTrainningService()
        self.preprocessing_service = DataPreprocessingService()
        self.is_training = False
        
        self._build_ui()
        self._refresh_model_list()
    
    def _build_ui(self):
        # ── Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        
        self._icon_brain = icon_lg("brain")
        title = ctk.CTkLabel(
            header, text="  Quản lý Model",
            image=self._icon_brain,
            compound="left",
            font=FONTS["title"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            header, text="So sánh & Retrain các model phát hiện gian lận",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w"
        )
        subtitle.pack(side="left", padx=(16, 0), pady=(8, 0))
        
        # ── Main content split
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        
        # ═══════════════════════════════════════════════════
        # TOP: Model comparison table + metrics
        # ═══════════════════════════════════════════════════
        top_frame = ctk.CTkFrame(content, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        top_frame.grid_columnconfigure(0, weight=3)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_rowconfigure(0, weight=1)
        
        # Model list table
        table_card = StyledCard(top_frame, title="Danh sách Model")
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Sort controls
        sort_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        sort_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        sort_label = ctk.CTkLabel(
            sort_frame, text="Sắp xếp theo:",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        )
        sort_label.pack(side="left")
        
        self.sort_var = ctk.StringVar(value="F1 Score")
        sort_menu = StyledOptionMenu(
            sort_frame,
            variable=self.sort_var,
            values=["Recall", "Precision", "F1 Score", "Accuracy", "Ngày tạo", "Model Name"],
            command=self._on_sort_changed,
            width=150,
            height=32,
        )
        sort_menu.pack(side="left", padx=(8, 8))
        
        self.sort_asc_var = ctk.BooleanVar(value=False)
        sort_order_btn = StyledButton(
            sort_frame, text="▼ Giảm dần", width=110,
            variant="secondary", height=32,
            command=self._toggle_sort_order
        )
        sort_order_btn.pack(side="left")
        self.sort_order_btn = sort_order_btn
        
        self._icon_refresh = icon_md("refresh")
        refresh_btn = StyledButton(
            sort_frame, text=" Làm mới", width=120,
            image=self._icon_refresh, compound="left",
            variant="secondary", height=32,
            command=self._refresh_model_list
        )
        refresh_btn.pack(side="right")
        
        self.model_table = DataTable(
            table_card,
            columns=["Model", "Type", "Recall", "Precision", "F1 Score", "Accuracy", "File"]
        )
        self.model_table.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # Best model metrics
        self._icon_trophy = icon_md("trophy")
        metrics_card = StyledCard(top_frame, title=" Model tốt nhất")
        metrics_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        self.best_model_label = ctk.CTkLabel(
            metrics_card, text="—",
            font=FONTS["body_bold"],
            text_color=COLORS["accent_secondary"],
            anchor="w"
        )
        self.best_model_label.pack(fill="x", padx=20, pady=(0, 12))
        
        self.metric_cards = {}
        for metric_name, color in [
            ("Recall", COLORS["accent_primary"]),
            ("Precision", COLORS["accent_secondary"]),
            ("F1 Score", COLORS["accent_warning"]),
            ("Accuracy", COLORS["accent_success"]),
        ]:
            mc = MetricCard(metrics_card, title=metric_name, value="—", color=color)
            mc.pack(fill="x", padx=20, pady=(0, 8))
            self.metric_cards[metric_name] = mc
        
        # ═══════════════════════════════════════════════════
        # BOTTOM: Retrain section
        # ═══════════════════════════════════════════════════
        bottom_frame = ctk.CTkFrame(content, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=2)
        bottom_frame.grid_rowconfigure(0, weight=1)
        
        # Train controls
        self._icon_retrain = icon_md("refresh")
        train_card = StyledCard(bottom_frame, title=" Retrain Model")
        train_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        train_inner = ctk.CTkFrame(train_card, fg_color="transparent")
        train_inner.pack(fill="x", padx=20, pady=(0, 8))
        
        algo_label = ctk.CTkLabel(
            train_inner, text="Chọn thuật toán:",
            font=FONTS["body_bold"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        algo_label.pack(fill="x")
        
        self.algo_var = ctk.StringVar(value="Random Forest")
        
        algo_frame = ctk.CTkFrame(train_inner, fg_color="transparent")
        algo_frame.pack(fill="x", pady=(6, 12))
        
        for algo_name in ["Random Forest", "XGBoost", "Logistic Regression"]:
            rb = ctk.CTkRadioButton(
                algo_frame,
                text=algo_name,
                variable=self.algo_var,
                value=algo_name,
                font=FONTS["body"],
                text_color=COLORS["text_primary"],
                fg_color=COLORS["accent_primary"],
                hover_color=COLORS["accent_primary_hover"],
                border_color=COLORS["border"],
                radiobutton_width=22,
                radiobutton_height=22,
            )
            rb.pack(anchor="w", pady=3)
        
        data_label = ctk.CTkLabel(
            train_inner, text="Dữ liệu train:",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        data_label.pack(fill="x")
        
        # File/Folder browse buttons
        browse_frame = ctk.CTkFrame(train_inner, fg_color="transparent")
        browse_frame.pack(fill="x", pady=(4, 4))
        
        self._icon_file = icon_md("file")
        browse_file_btn = StyledButton(
            browse_frame, text=" Chọn file CSV", width=160,
            image=self._icon_file, compound="left",
            variant="secondary", height=36,
            command=self._browse_train_file
        )
        browse_file_btn.pack(side="left", padx=(0, 6))
        
        self._icon_folder = icon_md("folder")
        browse_folder_btn = StyledButton(
            browse_frame, text=" Chọn thư mục", width=160,
            image=self._icon_folder, compound="left",
            variant="secondary", height=36,
            command=self._browse_train_folder
        )
        browse_folder_btn.pack(side="left")
        
        self.train_data_path = ctk.StringVar(value=AppConfig.TRAIN_DATA_PATH)
        self.data_path_label = ctk.CTkLabel(
            train_inner, text=f"{AppConfig.TRAIN_DATA_PATH}",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
            anchor="w",
            wraplength=300,
        )
        self.data_path_label.pack(fill="x", pady=(4, 16))
        
        self._icon_rocket = icon_md("rocket")
        self.train_btn = StyledButton(
            train_inner, text=" Bắt đầu Train",
            image=self._icon_rocket, compound="left",
            command=self._start_training,
            height=44,
        )
        self.train_btn.pack(fill="x", pady=(0, 8))
        
        self._icon_stop = icon_md("stop")
        self.stop_btn = StyledButton(
            train_inner, text=" Dừng lại",
            image=self._icon_stop, compound="left",
            variant="danger",
            command=self._stop_training,
            state="disabled",
            height=36,
        )
        self.stop_btn.pack(fill="x")
        
        # Progress log
        self.progress_card = ProgressCard(bottom_frame)
        self.progress_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    
    # ═══════════════════════════════════════════════════════════
    # Model List & Sorting
    # ═══════════════════════════════════════════════════════════
    def _refresh_model_list(self):
        model_dir = AppConfig.MODEL_OUT_DIR
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
            return
        
        self.models_data = []
        
        # Find all .pkl / .joblib files and their corresponding .txt score files
        model_files = [f for f in os.listdir(model_dir)
                       if f.endswith(('.pkl', '.joblib'))]
        
        for model_file in model_files:
            if "random_forest" in model_file:
                model_type = "Random Forest"
            elif "logistic_regression" in model_file:
                model_type = "Logistic Regression"
            else:
                model_type = "XGBoost"
            base_name = model_file.rsplit('.', 1)[0]
            score_file = base_name + ".txt"
            score_path = os.path.join(model_dir, score_file)
            
            recall = precision = f1 = accuracy = 0.0
            
            if os.path.exists(score_path):
                try:
                    with open(score_path, 'r') as f:
                        content = f.read()
                    # Parse the pandas DataFrame string output
                    lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
                    if len(lines) >= 2:
                        # Find the data line (usually the last line with numeric values)
                        for line in lines:
                            parts = line.split()
                            nums = []
                            for p in parts:
                                try:
                                    nums.append(float(p))
                                except ValueError:
                                    continue
                            if len(nums) >= 4:
                                recall, precision, f1, accuracy = nums[:4]
                except Exception:
                    pass
            
            # Extract date from filename (e.g. random_forest_20260501_162110)
            import re
            date_match = re.search(r'(\d{8}_\d{6})', base_name)
            date_str = date_match.group(1) if date_match else '00000000_000000'
            
            self.models_data.append({
                'Model': base_name,
                'Type': model_type,
                'Recall': recall,
                'Precision': precision,
                'F1 Score': f1,
                'Accuracy': accuracy,
                'Date': date_str,
                'File': model_file,
            })
        
        self._apply_sort_and_display()
    
    def _apply_sort_and_display(self):
        sort_key = self.sort_var.get()
        ascending = self.sort_asc_var.get()
        
        if sort_key == "Model Name":
            self.models_data.sort(key=lambda x: x['Model'], reverse=not ascending)
        elif sort_key == "Ngày tạo":
            self.models_data.sort(key=lambda x: x.get('Date', ''), reverse=not ascending)
        else:
            self.models_data.sort(key=lambda x: x.get(sort_key, 0), reverse=not ascending)
        
        # Convert to DataFrame for table display
        if self.models_data:
            df = pd.DataFrame(self.models_data)
            # Format numeric columns
            for col in ['Recall', 'Precision', 'F1 Score', 'Accuracy']:
                df[col] = df[col].apply(lambda x: f"{x:.4f}" if x > 0 else "—")
            
            self.model_table.set_columns(["Model", "Type", "Recall", "Precision", "F1 Score", "Accuracy", "File"])
            self.model_table.insert_dataframe(df)
            
            # Update best model metrics
            best = self.models_data[0]
            self.best_model_label.configure(text=f"{best['Type']} — {best['File']}")
            for metric_name in ['Recall', 'Precision', 'F1 Score', 'Accuracy']:
                val = best.get(metric_name, 0)
                self.metric_cards[metric_name].set_value(
                    f"{val:.4f}" if val > 0 else "—"
                )
        else:
            self.model_table.clear()
            self.best_model_label.configure(text="Chưa có model nào")
    
    def _on_sort_changed(self, value):
        self._apply_sort_and_display()
    
    def _toggle_sort_order(self):
        current = self.sort_asc_var.get()
        self.sort_asc_var.set(not current)
        if not current:
            self.sort_order_btn.configure(text="▲ Tăng dần")
        else:
            self.sort_order_btn.configure(text="▼ Giảm dần")
        self._apply_sort_and_display()
    
    # ═══════════════════════════════════════════════════════════
    # Data Path Selection
    # ═══════════════════════════════════════════════════════════
    def _browse_train_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.train_data_path.set(path)
            self.data_path_label.configure(text=f"{path}")
    
    def _browse_train_folder(self):
        path = filedialog.askdirectory(title="Chọn thư mục chứa file CSV")
        if path:
            self.train_data_path.set(path)
            csv_count = len([f for f in os.listdir(path) if f.endswith('.csv')])
            self.data_path_label.configure(text=f"{path} ({csv_count} files)")
    
    # ═══════════════════════════════════════════════════════════
    # Training
    # ═══════════════════════════════════════════════════════════
    def _start_training(self):
        if self.is_training:
            show_info(self.winfo_toplevel(), "Thông báo", "Đang trong quá trình training!")
            return
        
        data_path = self.train_data_path.get()
        if not data_path or not os.path.exists(data_path):
            show_warning(self.winfo_toplevel(), "Cảnh báo", "Vui lòng chọn file hoặc thư mục dữ liệu hợp lệ!")
            return
        
        self.is_training = True
        self.train_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_card.clear_log()
        
        algo = self.algo_var.get()
        
        # Run training in background thread
        thread = threading.Thread(target=self._train_worker, args=(algo, data_path), daemon=True)
        thread.start()
    
    def _train_worker(self, algo, data_path):
        import sys
        import io
        
        try:
            # Step 1: Load & preprocess data
            self._update_progress(0.05, "📂 Đang load dữ liệu...")
            self._log("Đang load dữ liệu từ: " + data_path)
            
            if os.path.isdir(data_path):
                # Load all CSVs from folder
                raw_df = self.preprocessing_service.load_folder(data_path)
                df = self.preprocessing_service.clean(raw_df)
            else:
                df = self.preprocessing_service.prepare(data_path)
            self._update_progress(0.15, "✅ Đã load & clean dữ liệu")
            self._log(f"Dữ liệu: {df.shape[0]} dòng, {df.shape[1]} cột")
            
            # Step 2: Split data
            self._update_progress(0.20, "📊 Đang chia dữ liệu train/test...")
            X_train, X_test, y_train, y_test = self.training_service.splitData(df)
            self._log(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
            self._update_progress(0.25, "✅ Đã chia dữ liệu")
            
            # Redirect stdout to capture training logs
            old_stdout = sys.stdout
            captured = io.StringIO()
            
            class TeeOutput:
                def __init__(self, original, capture, callback):
                    self.original = original
                    self.capture = capture
                    self.callback = callback
                
                def write(self, text):
                    self.original.write(text)
                    self.capture.write(text)
                    if text.strip():
                        self.callback(text.strip())
                
                def flush(self):
                    self.original.flush()
                    self.capture.flush()
            
            sys.stdout = TeeOutput(old_stdout, captured, self._log)
            
            if algo == "Random Forest":
                self._update_progress(0.30, "Đang train Random Forest...")
                self._log("\n" + "="*50)
                self._log("BẮT ĐẦU TRAIN RANDOM FOREST")
                self._log("="*50)
                self.training_service.startRandomForest(X_train, X_test, y_train, y_test)
                self._update_progress(0.90, "Random Forest hoàn thành!")
            
            elif algo == "XGBoost":
                self._update_progress(0.30, "Đang train XGBoost...")
                self._log("\n" + "="*50)
                self._log("BẮT ĐẦU TRAIN XGBOOST")
                self._log("="*50)
                self.training_service.startXGBoost(X_train, X_test, y_train, y_test)
                self._update_progress(0.90, "XGBoost hoàn thành!")
            
            elif algo == "Logistic Regression":
                self._update_progress(0.30, "Đang train Logistic Regression...")
                self._log("\n" + "="*50)
                self._log("BẮT ĐẦU TRAIN LOGISTIC REGRESSION")
                self._log("="*50)
                self.training_service.startLogisticRegression(X_train, X_test, y_train, y_test)
                self._update_progress(0.90, "Logistic Regression hoàn thành!")
            
            sys.stdout = old_stdout
            
            self._update_progress(1.0, "🎉 Training hoàn tất!")
            self._log("\n🎉 TẤT CẢ HOÀN TẤT!")
            
            # Refresh model list on main thread
            self.after(500, self._refresh_model_list)
            
        except Exception as e:
            sys.stdout = sys.__stdout__
            self._log(f"\n❌ LỖI: {str(e)}")
            self._update_progress(0, f"❌ Lỗi: {str(e)[:60]}")
        finally:
            self.is_training = False
            self.after(0, lambda: self.train_btn.configure(state="normal"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))
    
    def _stop_training(self):
        # Note: Can't truly stop a thread in Python, but we mark it
        self.is_training = False
        self._log("⏹ Yêu cầu dừng training...")
        self.stop_btn.configure(state="disabled")
    
    def _update_progress(self, value, text):
        self.after(0, lambda: self.progress_card.set_progress(value, text))
    
    def _log(self, text):
        self.after(0, lambda: self.progress_card.append_log(text))
