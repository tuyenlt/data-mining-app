import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
from src.config.theme import COLORS, FONTS


class StyledCard(ctk.CTkFrame):
    """A rounded card container with consistent styling."""
    def __init__(self, master, title=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        if title:
            label = ctk.CTkLabel(
                self, text=title,
                font=FONTS["heading"],
                text_color=COLORS["text_primary"],
                anchor="w"
            )
            label.pack(fill="x", padx=20, pady=(16, 8))


class StyledButton(ctk.CTkButton):
    """Pre-styled button with consistent appearance."""
    def __init__(self, master, variant="primary", **kwargs):
        color_map = {
            "primary": (COLORS["accent_primary"], COLORS["accent_primary_hover"]),
            "danger": (COLORS["accent_danger"], COLORS["accent_danger_hover"]),
            "success": (COLORS["accent_success"], COLORS["accent_success"]),
            "secondary": (COLORS["bg_card_hover"], COLORS["border"]),
        }
        fg, hover = color_map.get(variant, color_map["primary"])
        
        defaults = {
            "fg_color": fg,
            "hover_color": hover,
            "text_color": COLORS["text_on_accent"],
            "font": FONTS["body_bold"],
            "corner_radius": 10,
            "height": 44,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class StyledEntry(ctk.CTkEntry):
    """Pre-styled text entry."""
    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": COLORS["bg_input"],
            "border_color": COLORS["border"],
            "text_color": COLORS["text_primary"],
            "placeholder_text_color": COLORS["text_muted"],
            "font": FONTS["body"],
            "corner_radius": 10,
            "height": 44,
            "border_width": 1,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class StyledOptionMenu(ctk.CTkOptionMenu):
    """Pre-styled dropdown."""
    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": COLORS["bg_input"],
            "button_color": COLORS["accent_primary"],
            "button_hover_color": COLORS["accent_primary_hover"],
            "text_color": COLORS["text_primary"],
            "font": FONTS["body"],
            "dropdown_fg_color": COLORS["bg_card"],
            "dropdown_text_color": COLORS["text_primary"],
            "dropdown_hover_color": COLORS["accent_primary"],
            "corner_radius": 10,
            "height": 44,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class StatusBadge(ctk.CTkLabel):
    """Colored badge for fraud/legit status."""
    def __init__(self, master, is_fraud=False, **kwargs):
        text = "⚠ Gian lận" if is_fraud else "✓ Hợp lệ"
        color = COLORS["fraud"] if is_fraud else COLORS["legit"]
        super().__init__(
            master,
            text=text,
            font=FONTS["small_bold"],
            text_color=color,
            **kwargs
        )


class DataTable(ctk.CTkFrame):
    """Scrollable data table using ttk.Treeview with dark styling."""
    def __init__(self, master, columns, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.columns = columns
        
        # Style the Treeview for dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Dark.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            font=("Segoe UI", 14),
            rowheight=40,
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["accent_secondary"],
            font=("Segoe UI", 14, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map("Dark.Treeview", 
                   background=[("selected", COLORS["accent_primary"])],
                   foreground=[("selected", COLORS["text_on_accent"])])
        style.map("Dark.Treeview.Heading",
                   background=[("active", COLORS["bg_card_hover"])])
        
        # Create treeview
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="extended",
        )
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", width=150, minwidth=100, stretch=False)
        
        # Scrollbars
        vsb = ctk.CTkScrollbar(self, command=self.tree.yview)
        hsb = ctk.CTkScrollbar(self, command=self.tree.xview, orientation="horizontal")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def insert_dataframe(self, df):
        self.clear()
        for _, row in df.iterrows():
            values = [str(v) for v in row.values]
            self.tree.insert("", "end", values=values)
    
    def set_columns(self, columns):
        self.columns = columns
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", width=150, minwidth=100, stretch=False)


class ProgressCard(ctk.CTkFrame):
    """Card showing training progress with log output."""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        header = ctk.CTkLabel(
            self, text="Training Log",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        header.pack(fill="x", padx=20, pady=(16, 8))
        
        self.progress_bar = ctk.CTkProgressBar(
            self,
            progress_color=COLORS["accent_primary"],
            fg_color=COLORS["bg_input"],
            corner_radius=6,
            height=12,
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 8))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self, text="Sẵn sàng",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 4))
        
        self.log_text = ctk.CTkTextbox(
            self,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["mono_small"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            height=200,
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 16))
    
    def set_progress(self, value, status_text=""):
        self.progress_bar.set(value)
        if status_text:
            self.status_label.configure(text=status_text)
    
    def append_log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
    
    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self.progress_bar.set(0)
        self.status_label.configure(text="Sẵn sàng")


class MetricCard(ctk.CTkFrame):
    """Small card showing a single metric value."""
    def __init__(self, master, title, value, color=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        title_lbl = ctk.CTkLabel(
            self, text=title,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        )
        title_lbl.pack(padx=16, pady=(12, 2))
        
        self.value_lbl = ctk.CTkLabel(
            self, text=value,
            font=("Segoe UI", 26, "bold"),
            text_color=color or COLORS["accent_secondary"]
        )
        self.value_lbl.pack(padx=16, pady=(0, 12))
    
    def set_value(self, value, color=None):
        self.value_lbl.configure(text=value)
        if color:
            self.value_lbl.configure(text_color=color)


# ═══════════════════════════════════════════════════════════════
# Modern Dialog / Toast
# ═══════════════════════════════════════════════════════════════

class ModernDialog(ctk.CTkToplevel):
    """A modern, dark-themed modal dialog that replaces messagebox."""
    
    # Resolve icon directory relative to this file
    _ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")
    
    DIALOG_CONFIG = {
        "info": {
            "icon_file": "info.png",
            "color": "#6c5ce7",
            "title_default": "Thông báo",
        },
        "success": {
            "icon_file": "success.png",
            "color": "#00b894",
            "title_default": "Thành công",
        },
        "warning": {
            "icon_file": "warning.png",
            "color": "#fdcb6e",
            "title_default": "Cảnh báo",
        },
        "error": {
            "icon_file": "error.png",
            "color": "#ff6b6b",
            "title_default": "Lỗi",
        },
    }
    
    def __init__(self, parent, dialog_type="info", title=None, message="", **kwargs):
        super().__init__(parent, **kwargs)
        
        config = self.DIALOG_CONFIG.get(dialog_type, self.DIALOG_CONFIG["info"])
        accent = config["color"]
        display_title = title or config["title_default"]
        
        # ── Window setup
        self.title(display_title)
        self.geometry("460x240")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Make modal
        self.transient(parent)
        
        # Center on parent
        self.update_idletasks()
        if parent.winfo_exists():
            px = parent.winfo_rootx() + (parent.winfo_width() // 2) - 230
            py = parent.winfo_rooty() + (parent.winfo_height() // 2) - 120
            self.geometry(f"460x240+{px}+{py}")
        
        # ── Outer border (accent glow)
        outer = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=20,
            border_width=2,
            border_color=accent,
        )
        outer.pack(fill="both", expand=True, padx=4, pady=4)
        
        # ── Accent top bar
        bar = ctk.CTkFrame(outer, fg_color=accent, height=5, corner_radius=0)
        bar.pack(fill="x", padx=20, pady=(16, 0))
        
        # ── Icon + Title row
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(12, 4))
        
        # Load icon image
        icon_path = os.path.join(self._ICON_DIR, config["icon_file"])
        try:
            from PIL import Image
            pil_img = Image.open(icon_path)
            self._icon_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(40, 40))
            icon_lbl = ctk.CTkLabel(header, image=self._icon_image, text="")
        except Exception:
            # Fallback to text if image fails
            icon_lbl = ctk.CTkLabel(header, text="●", font=("Segoe UI", 28), text_color=accent)
        icon_lbl.pack(side="left", padx=(0, 12))
        
        title_lbl = ctk.CTkLabel(
            header, text=display_title,
            font=("Segoe UI", 18, "bold"),
            text_color=accent,
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)
        
        # ── Message
        msg_lbl = ctk.CTkLabel(
            outer, text=message,
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            anchor="w",
            justify="left",
            wraplength=400,
        )
        msg_lbl.pack(fill="x", padx=28, pady=(4, 16))
        
        # ── Button
        btn_frame = ctk.CTkFrame(outer, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        ok_btn = ctk.CTkButton(
            btn_frame,
            text="OK",
            fg_color=accent,
            hover_color=self._lighten(accent),
            text_color="#ffffff",
            font=FONTS["body_bold"],
            corner_radius=10,
            width=120,
            height=40,
            command=self._close,
        )
        ok_btn.pack(side="right")
        
        # Keyboard binding
        self.bind("<Return>", lambda e: self._close())
        self.bind("<Escape>", lambda e: self._close())
        
        # Grab focus after window is visible
        self.after(50, self._do_grab)
    
    def _do_grab(self):
        """Grab focus after window is mapped and visible."""
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass
    
    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
    
    @staticmethod
    def _lighten(hex_color):
        """Return a slightly lighter version of a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"


def show_info(parent, title, message):
    """Show a modern info dialog."""
    ModernDialog(parent, "info", title, message)

def show_success(parent, title, message):
    """Show a modern success dialog."""
    ModernDialog(parent, "success", title, message)

def show_warning(parent, title, message):
    """Show a modern warning dialog."""
    ModernDialog(parent, "warning", title, message)

def show_error(parent, title, message):
    """Show a modern error dialog."""
    ModernDialog(parent, "error", title, message)
