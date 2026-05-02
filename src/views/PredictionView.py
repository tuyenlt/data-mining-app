import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import threading

from src.config.theme import COLORS, FONTS
from src.config.AppConfig import AppConfig
from src.components.widgets import (
    StyledCard, StyledButton, StyledEntry, StyledOptionMenu, DataTable,
    show_info, show_warning, show_error, show_success
)
from src.services.ModelPredictionService import ModelPredictionService
from src.config.icons import icon_md, icon_lg, icon_xl


# ═══════════════════════════════════════════════════════════════
# Columns expected for manual input
# ═══════════════════════════════════════════════════════════════
TRANSACTION_FIELDS = [
    ("merchant", "Merchant", "Rippin, Kub and Mann"),
    ("category", "Category", "misc_net"),
    ("amt", "Amount ($)", "4.97"),
    ("gender", "Gender (M/F)", "F"),
    ("lat", "Latitude", "36.0788"),
    ("long", "Longitude", "-81.1781"),
    ("city_pop", "City Population", "3495"),
    ("job", "Job", "Psychologist"),
    ("merch_lat", "Merchant Lat", "36.011293"),
    ("merch_long", "Merchant Long", "-82.048315"),
    ("dob", "Date of Birth", "1988-03-09"),
    ("trans_date_trans_time", "Transaction Time", "2019-01-01 00:00:18"),
    ("unix_time", "Unix Time", "1325376018"),
]


class PredictionView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.prediction_service = ModelPredictionService()
        self.result_df = None
        self.entries = {}
        
        self._build_ui()
        self._refresh_models()
    
    def _build_ui(self):
        # ── Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=0, pady=(0, 16))
        
        self._icon_search = icon_lg("search")
        title = ctk.CTkLabel(
            header_frame, text="  Dự đoán giao dịch",
            image=self._icon_search,
            compound="left",
            font=FONTS["title"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            header_frame, text="Phát hiện giao dịch gian lận bằng AI",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w"
        )
        subtitle.pack(side="left", padx=(16, 0), pady=(8, 0))
        
        # ── Content: left (input) + right (result)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=2, minsize=450)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)
        
        # ─────────────── LEFT PANEL ───────────────
        left_panel = ctk.CTkFrame(content, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Model selection card
        model_card = StyledCard(left_panel, title="Chọn Model")
        model_card.pack(fill="x", pady=(0, 12))
        
        model_inner = ctk.CTkFrame(model_card, fg_color="transparent")
        model_inner.pack(fill="x", padx=20, pady=(0, 12))
        
        self.model_var = ctk.StringVar(value="Chọn model...")
        self.model_menu = StyledOptionMenu(
            model_inner,
            variable=self.model_var,
            values=["Đang tải..."],
            command=self._on_model_selected,
            width=280
        )
        self.model_menu.pack(side="left", fill="x", expand=True)
        
        self._icon_refresh_sm = icon_md("refresh")
        refresh_btn = StyledButton(
            model_inner, text="", width=38, variant="secondary",
            image=self._icon_refresh_sm,
            command=self._refresh_models
        )
        refresh_btn.pack(side="right", padx=(8, 0))
        
        self.model_status = ctk.CTkLabel(
            model_card, text="Chưa chọn model",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w"
        )
        self.model_status.pack(fill="x", padx=20, pady=(0, 6))
        
        # Model metrics display
        self.metrics_frame = ctk.CTkFrame(model_card, fg_color=COLORS["bg_input"], corner_radius=10)
        self.metrics_frame.pack(fill="x", padx=20, pady=(0, 12))
        
        self._icon_chart = icon_md("chart")
        metrics_title = ctk.CTkLabel(
            self.metrics_frame, text=" Chỉ số đánh giá",
            image=self._icon_chart,
            compound="left",
            font=FONTS["small_bold"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        metrics_title.pack(fill="x", padx=12, pady=(8, 4))
        
        self.metric_labels = {}
        metrics_grid = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=12, pady=(0, 8))
        metrics_grid.grid_columnconfigure(0, weight=1)
        metrics_grid.grid_columnconfigure(1, weight=1)
        
        for i, (metric_key, metric_name, color) in enumerate([
            ("Recall", "Recall", COLORS["accent_primary"]),
            ("Precision", "Precision", COLORS["accent_secondary"]),
            ("F1 Score", "F1 Score", COLORS["accent_warning"]),
        ]):
            row = 0
            col = i
            metrics_grid.grid_columnconfigure(i, weight=1)
            cell = ctk.CTkFrame(metrics_grid, fg_color="transparent")
            cell.grid(row=row, column=col, sticky="ew", padx=4, pady=2)
            
            name_lbl = ctk.CTkLabel(cell, text=f"{metric_name}:", font=FONTS["tiny"],
                                    text_color=COLORS["text_muted"], anchor="w")
            name_lbl.pack(side="left")
            
            val_lbl = ctk.CTkLabel(cell, text="—", font=FONTS["small_bold"],
                                   text_color=color, anchor="e")
            val_lbl.pack(side="right")
            self.metric_labels[metric_key] = val_lbl
        
        # Input method tabs
        input_card = StyledCard(left_panel, title="Nhập dữ liệu")
        input_card.pack(fill="both", expand=True, pady=(0, 12))
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        tab_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        self.tab_manual_btn = StyledButton(
            tab_frame, text="Nhập tay", width=130,
            command=lambda: self._switch_tab("manual")
        )
        self.tab_manual_btn.pack(side="left", padx=(0, 8))
        
        self._icon_file_tab = icon_md("file")
        self.tab_csv_btn = StyledButton(
            tab_frame, text=" Import CSV", width=140,
            image=self._icon_file_tab, compound="left",
            variant="secondary",
            command=lambda: self._switch_tab("csv")
        )
        self.tab_csv_btn.pack(side="left")
        
        # Tab content container
        self.tab_container = ctk.CTkFrame(input_card, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # Build both tabs (show manual by default)
        self._build_manual_tab()
        self._build_csv_tab()
        self._switch_tab("manual")
        
        # ─────────────── RIGHT PANEL ───────────────
        right_panel = ctk.CTkFrame(content, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        # Results card
        result_card = StyledCard(right_panel, title="Kết quả dự đoán")
        result_card.pack(fill="both", expand=True)
        
        # Summary stats
        self.stats_frame = ctk.CTkFrame(result_card, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        self.stat_total = ctk.CTkLabel(
            self.stats_frame, text="Tổng: 0",
            font=FONTS["small_bold"],
            text_color=COLORS["text_secondary"]
        )
        self.stat_total.pack(side="left", padx=(0, 16))
        
        self.stat_fraud = ctk.CTkLabel(
            self.stats_frame, text="Gian lận: 0",
            font=FONTS["small_bold"],
            text_color=COLORS["fraud"]
        )
        self.stat_fraud.pack(side="left", padx=(0, 16))
        
        self.stat_legit = ctk.CTkLabel(
            self.stats_frame, text="Hợp lệ: 0",
            font=FONTS["small_bold"],
            text_color=COLORS["legit"]
        )
        self.stat_legit.pack(side="left")
        
        # Result table
        self.result_table = DataTable(
            result_card,
            columns=["merchant", "category", "amt", "prediction_label"]
        )
        self.result_table.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        
        # Action buttons
        action_frame = ctk.CTkFrame(result_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 16))
        
        self._icon_save = icon_md("save")
        self.save_btn = StyledButton(
            action_frame, text=" Lưu kết quả CSV", variant="success",
            image=self._icon_save, compound="left",
            command=self._save_results, state="disabled"
        )
        self.save_btn.pack(side="right")
    
    # ═══════════════════════════════════════════════════════════
    # Tab: Manual Input
    # ═══════════════════════════════════════════════════════════
    def _build_manual_tab(self):
        self.manual_frame = ctk.CTkScrollableFrame(
            self.tab_container,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        
        # Create entry fields in a 2-column grid
        for i, (field_key, field_label, placeholder) in enumerate(TRANSACTION_FIELDS):
            row = i // 2
            col = i % 2
            
            container = ctk.CTkFrame(self.manual_frame, fg_color="transparent")
            container.grid(row=row, column=col, sticky="ew", padx=4, pady=3)
            self.manual_frame.grid_columnconfigure(col, weight=1)
            
            lbl = ctk.CTkLabel(
                container, text=field_label,
                font=FONTS["tiny"],
                text_color=COLORS["text_secondary"],
                anchor="w"
            )
            lbl.pack(fill="x")
            
            entry = StyledEntry(container, placeholder_text=placeholder, height=32)
            entry.pack(fill="x")
            self.entries[field_key] = entry
        
        # Predict button
        btn_container = ctk.CTkFrame(self.manual_frame, fg_color="transparent")
        btn_container.grid(row=len(TRANSACTION_FIELDS) // 2 + 1, column=0, columnspan=2,
                          sticky="ew", pady=(12, 0))
        
        self._icon_rocket_pred = icon_md("rocket")
        predict_btn = StyledButton(
            btn_container, text=" Dự đoán", width=200,
            image=self._icon_rocket_pred, compound="left",
            command=self._predict_manual
        )
        predict_btn.pack(side="right")
        
        clear_btn = StyledButton(
            btn_container, text="Xóa", width=100,
            variant="secondary",
            command=self._clear_manual
        )
        clear_btn.pack(side="right", padx=(0, 8))
    
    def _build_csv_tab(self):
        self.csv_frame = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        
        # Drop zone style
        drop_zone = ctk.CTkFrame(
            self.csv_frame,
            fg_color=COLORS["bg_input"],
            corner_radius=14,
            border_width=2,
            border_color=COLORS["border"],
            height=120,
        )
        drop_zone.pack(fill="x", pady=(8, 12))
        drop_zone.pack_propagate(False)
        
        self._icon_folder_drop = icon_xl("folder")
        drop_icon = ctk.CTkLabel(
            drop_zone, text="",
            image=self._icon_folder_drop,
        )
        drop_icon.pack(pady=(16, 4))
        
        self.csv_label = ctk.CTkLabel(
            drop_zone, text="Chọn file CSV để dự đoán",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        )
        self.csv_label.pack()
        
        self._icon_folder_browse = icon_md("folder")
        browse_btn = StyledButton(
            self.csv_frame, text=" Chọn file CSV",
            image=self._icon_folder_browse, compound="left",
            command=self._browse_csv
        )
        browse_btn.pack(fill="x", pady=(0, 12))
        
        self.csv_path_var = ctk.StringVar()
        
        self._icon_rocket_csv = icon_md("rocket")
        predict_csv_btn = StyledButton(
            self.csv_frame, text=" Dự đoán từ CSV", width=200,
            image=self._icon_rocket_csv, compound="left",
            command=self._predict_csv
        )
        predict_csv_btn.pack(fill="x")
    
    # ═══════════════════════════════════════════════════════════
    # Tab Switching
    # ═══════════════════════════════════════════════════════════
    def _switch_tab(self, tab_name):
        self.manual_frame.pack_forget()
        self.csv_frame.pack_forget()
        
        if tab_name == "manual":
            self.manual_frame.pack(fill="both", expand=True)
            self.tab_manual_btn.configure(
                fg_color=COLORS["accent_primary"],
                hover_color=COLORS["accent_primary_hover"]
            )
            self.tab_csv_btn.configure(
                fg_color=COLORS["bg_card_hover"],
                hover_color=COLORS["border"]
            )
        else:
            self.csv_frame.pack(fill="both", expand=True)
            self.tab_csv_btn.configure(
                fg_color=COLORS["accent_primary"],
                hover_color=COLORS["accent_primary_hover"]
            )
            self.tab_manual_btn.configure(
                fg_color=COLORS["bg_card_hover"],
                hover_color=COLORS["border"]
            )
    
    # ═══════════════════════════════════════════════════════════
    # Model Management
    # ═══════════════════════════════════════════════════════════
    def _refresh_models(self):
        model_dir = AppConfig.MODEL_OUT_DIR
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
        
        models = [f for f in os.listdir(model_dir)
                   if f.endswith(('.pkl', '.joblib'))]
        models.sort(reverse=True)
        
        if models:
            self.model_menu.configure(values=models)
            self.model_var.set(models[0])
            self._on_model_selected(models[0])
        else:
            self.model_menu.configure(values=["Không có model"])
            self.model_var.set("Không có model")
            self.model_status.configure(
                text="Chưa có model. Vui lòng train trước.",
                text_color=COLORS["accent_warning"]
            )
    
    def _on_model_selected(self, model_name):
        if model_name in ("Đang tải...", "Không có model"):
            return
        try:
            model_path = os.path.join(AppConfig.MODEL_OUT_DIR, model_name)
            self.prediction_service.load_model(model_path)
            
            if "random_forest" in model_name:
                model_type = "Random Forest"
            elif "logistic_regression" in model_name:
                model_type = "Logistic Regression"
            else:
                model_type = "XGBoost"
            self.model_status.configure(
                text=f"Đã load: {model_type} ({model_name})",
                text_color=COLORS["accent_success"]
            )
            
            # Load and display model metrics from score file
            self._load_model_metrics(model_name)
            
        except Exception as e:
            self.model_status.configure(
                text=f"Lỗi load model: {str(e)[:50]}",
                text_color=COLORS["accent_danger"]
            )
            for lbl in self.metric_labels.values():
                lbl.configure(text="—")
    
    def _load_model_metrics(self, model_name):
        """Read the .txt score file for the selected model and display metrics."""
        base_name = model_name.rsplit('.', 1)[0]
        score_file = os.path.join(AppConfig.MODEL_OUT_DIR, base_name + ".txt")
        
        metrics = {'Recall': 0, 'Precision': 0, 'F1 Score': 0}
        
        if os.path.exists(score_file):
            try:
                with open(score_file, 'r') as f:
                    content = f.read()
                lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
                for line in lines:
                    parts = line.split()
                    nums = []
                    for p in parts:
                        try:
                            nums.append(float(p))
                        except ValueError:
                            continue
                    if len(nums) >= 3:
                        metrics['Recall'] = nums[0]
                        metrics['Precision'] = nums[1]
                        metrics['F1 Score'] = nums[2]
            except Exception:
                pass
        
        for key, val in metrics.items():
            if key in self.metric_labels:
                text = f"{val:.4f}" if val > 0 else "—"
                self.metric_labels[key].configure(text=text)
    
    # ═══════════════════════════════════════════════════════════
    # Prediction Actions
    # ═══════════════════════════════════════════════════════════
    def _predict_manual(self):
        if self.prediction_service.model is None:
            show_warning(self.winfo_toplevel(), "Cảnh báo", "Vui lòng chọn model trước!")
            return
        
        # Collect values from entries
        data = {}
        for field_key, _, _ in TRANSACTION_FIELDS:
            val = self.entries[field_key].get().strip()
            if not val:
                show_warning(self.winfo_toplevel(), "Cảnh báo", f"Vui lòng nhập: {field_key}")
                return
            data[field_key] = val
        
        # Convert types
        try:
            data['amt'] = float(data['amt'])
            data['lat'] = float(data['lat'])
            data['long'] = float(data['long'])
            data['city_pop'] = int(data['city_pop'])
            data['merch_lat'] = float(data['merch_lat'])
            data['merch_long'] = float(data['merch_long'])
            data['unix_time'] = int(data['unix_time'])
        except ValueError:
            show_error(self.winfo_toplevel(), "Lỗi", "Dữ liệu số không hợp lệ!")
            return
        
        # Add dummy columns that preprocessing expects
        data['Unnamed: 0'] = 0
        data['cc_num'] = 0
        data['trans_num'] = "manual_input"
        data['first'] = "N/A"
        data['last'] = "N/A"
        data['street'] = "N/A"
        data['city'] = "N/A"
        data['state'] = "N/A"
        data['zip'] = "00000"
        data['merch_zipcode'] = "00000"
        data['is_fraud'] = 0
        
        df = pd.DataFrame([data])
        
        try:
            result = self.prediction_service.predict(df)
            if result is not None:
                self.result_df = result
                self._display_results(result)
        except Exception as e:
            show_error(self.winfo_toplevel(), "Lỗi dự đoán", str(e))
    
    def _predict_csv(self):
        csv_path = self.csv_path_var.get()
        if not csv_path:
            show_warning(self.winfo_toplevel(), "Cảnh báo", "Vui lòng chọn file CSV!")
            return
        if self.prediction_service.model is None:
            show_warning(self.winfo_toplevel(), "Cảnh báo", "Vui lòng chọn model trước!")
            return
        
        try:
            result = self.prediction_service.predict_from_csv(csv_path)
            if result is not None:
                self.result_df = result
                self._display_results(result)
        except Exception as e:
            show_error(self.winfo_toplevel(), "Lỗi dự đoán", str(e))
    
    def _browse_csv(self):
        path = filedialog.askopenfilename(
            title="Chọn file CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.csv_path_var.set(path)
            filename = os.path.basename(path)
            self.csv_label.configure(text=f"✓ {filename}")
    
    def _display_results(self, df):
        # Update stats
        total = len(df)
        fraud = int(df['prediction'].sum()) if 'prediction' in df.columns else 0
        legit = total - fraud
        
        self.stat_total.configure(text=f"Tổng: {total}")
        self.stat_fraud.configure(text=f"Gian lận: {fraud}")
        self.stat_legit.configure(text=f"Hợp lệ: {legit}")
        
        # Show ALL columns, but move prediction_label and confidence to front
        priority_cols = ['prediction_label', 'fraud_prob']
        other_cols = [c for c in df.columns if c not in priority_cols and c != 'fraud_prob']
        display_cols = [c for c in priority_cols if c in df.columns] + other_cols
        
        self.result_table.set_columns(display_cols)
        self.result_table.insert_dataframe(df[display_cols])
        
        self.save_btn.configure(state="normal")
    
    def _save_results(self):
        if self.result_df is None:
            return
        path = filedialog.asksaveasfilename(
            title="Lưu kết quả",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if path:
            saved_path = self.prediction_service.save_result(self.result_df, path)
            show_success(self.winfo_toplevel(), "Thành công", f"Đã lưu kết quả tại:\n{saved_path}")
    
    def _clear_manual(self):
        for entry in self.entries.values():
            entry.delete(0, "end")
