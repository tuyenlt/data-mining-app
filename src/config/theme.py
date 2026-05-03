import customtkinter as ctk

# ═══════════════════════════════════════════════════════════════
# Theme & Color Constants
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # Background
    "bg_dark": "#0f0f1a",
    "bg_card": "#1a1a2e",
    "bg_card_hover": "#222240",
    "bg_input": "#16162b",
    "bg_sidebar": "#12121f",
    
    # Accent / Brand
    "accent_primary": "#6c5ce7",
    "accent_primary_hover": "#7e70f0",
    "accent_secondary": "#00cec9",
    "accent_danger": "#ff6b6b",
    "accent_danger_hover": "#ee5a5a",
    "accent_success": "#00b894",
    "accent_warning": "#fdcb6e",
    
    # Text
    "text_primary": "#e8e8f0",
    "text_secondary": "#a0a0c0",
    "text_muted": "#5a5a80",
    "text_on_accent": "#ffffff",
    
    # Border
    "border": "#2a2a45",
    "border_focus": "#6c5ce7",
    
    # Status
    "fraud": "#ff6b6b",
    "legit": "#00b894",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 18, "bold"),
    "heading": ("Segoe UI", 15, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 12),
    "small_bold": ("Segoe UI", 12, "bold"),
    "tiny": ("Segoe UI", 11),
    "mono": ("Consolas", 12),
    "mono_small": ("Consolas", 11),
    "icon": ("Segoe UI", 22),
}
