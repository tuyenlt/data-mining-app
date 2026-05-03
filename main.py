import customtkinter as ctk
import tkinter as tk
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.theme import COLORS, FONTS
from src.views.PredictionView import PredictionView
from src.views.ModelView import ModelView
from src.config.icons import icon_xl, icon_md


class App(ctk.CTk):
    """Main Application Window with sidebar navigation."""
    
    def __init__(self):
        super().__init__()
        
        # ── Window Config
        self.title("🛡 Fraud Detection — Data Mining App")
        self.geometry("1920x1080")
        self.minsize(1400, 900)
        # Maximize window (Linux-compatible)
        self.after(10, lambda: self.attributes('-zoomed', True))
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.configure(fg_color=COLORS["bg_dark"])
        
        self._build_layout()
        self._show_view("prediction")
    
    def _build_layout(self):
        # ═══════════════════════════════════════════════════
        # SIDEBAR
        # ═══════════════════════════════════════════════════
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_sidebar"],
            width=290,
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo / Brand
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(24, 8))
        
        self._logo_icon = icon_xl("shield")
        logo_label = ctk.CTkLabel(
            brand_frame,
            text="",
            image=self._logo_icon,
        )
        logo_label.pack(anchor="w")
        
        app_name = ctk.CTkLabel(
            brand_frame,
            text="Fraud Detection",
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        app_name.pack(fill="x", pady=(4, 0))
        
        app_sub = ctk.CTkLabel(
            brand_frame,
            text="Data Mining Application",
            font=FONTS["tiny"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        app_sub.pack(fill="x")
        
        # Separator
        sep = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["border"],
            height=1,
        )
        sep.pack(fill="x", padx=20, pady=(16, 16))
        
        # Navigation buttons
        nav_label = ctk.CTkLabel(
            self.sidebar,
            text="MENU",
            font=("Segoe UI", 10, "bold"),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        nav_label.pack(fill="x", padx=24, pady=(0, 8))
        
        self.nav_buttons = {}
        self._nav_icons = {
            "prediction": icon_md("search"),
            "models": icon_md("brain"),
        }
        nav_items = [
            ("prediction", "  Dự đoán"),
            ("models", "  Quản lý Model"),
        ]
        
        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                image=self._nav_icons[key],
                compound="left",
                font=FONTS["body"],
                anchor="w",
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                hover_color=COLORS["bg_card_hover"],
                corner_radius=10,
                height=42,
                command=lambda k=key: self._show_view(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn
        
        # Bottom info
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        version_label = ctk.CTkLabel(
            info_frame,
            text="v1.0.0 • Data Mining",
            font=FONTS["tiny"],
            text_color=COLORS["text_muted"],
        )
        version_label.pack()
        
        # ═══════════════════════════════════════════════════
        # MAIN CONTENT AREA
        # ═══════════════════════════════════════════════════
        self.main_area = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0,
        )
        self.main_area.pack(side="right", fill="both", expand=True)
        
        # Content padding wrapper
        self.content_wrapper = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
        )
        self.content_wrapper.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Create views (lazy)
        self.views = {}
    
    def _show_view(self, view_name):
        # Hide all views
        for v in self.views.values():
            v.pack_forget()
        
        # Create view if not exists
        if view_name not in self.views:
            if view_name == "prediction":
                self.views[view_name] = PredictionView(self.content_wrapper)
            elif view_name == "models":
                self.views[view_name] = ModelView(self.content_wrapper)
        
        # Show selected view
        self.views[view_name].pack(fill="both", expand=True)
        
        # Update nav button styles
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(
                    fg_color=COLORS["accent_primary"],
                    text_color=COLORS["text_on_accent"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                )


def main():
    # Ensure required directories exist
    os.makedirs("models", exist_ok=True)
    os.makedirs("predictions", exist_ok=True)
    os.makedirs("data/imported", exist_ok=True)
    
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
