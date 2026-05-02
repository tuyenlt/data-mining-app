"""
Centralized icon manager for the application.
Loads PNG icons from src/assets/icons/ and provides CTkImage instances.
"""
import os
import customtkinter as ctk
from PIL import Image

# Icon directory path
_ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons"
)

# Cache loaded icons to avoid repeated file I/O
_icon_cache = {}


def get_icon(name: str, size: tuple = (20, 20)) -> ctk.CTkImage:
    """
    Load an icon by name and return a CTkImage.
    
    Args:
        name: Icon filename without extension (e.g. 'folder', 'rocket')
        size: Tuple (width, height) for display size
    
    Returns:
        CTkImage ready to use in widgets
    """
    cache_key = f"{name}_{size[0]}x{size[1]}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    
    icon_path = os.path.join(_ICON_DIR, f"{name}.png")
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"Icon not found: {icon_path}")
    
    pil_img = Image.open(icon_path)
    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    _icon_cache[cache_key] = ctk_img
    return ctk_img


# ═══════════════════════════════════════════════════════════════
# Pre-defined icon sizes for convenience
# ═══════════════════════════════════════════════════════════════

def icon_sm(name: str) -> ctk.CTkImage:
    """Small icon (16x16) — for inline text, small buttons."""
    return get_icon(name, (16, 16))

def icon_md(name: str) -> ctk.CTkImage:
    """Medium icon (20x20) — for buttons, labels."""
    return get_icon(name, (20, 20))

def icon_lg(name: str) -> ctk.CTkImage:
    """Large icon (28x28) — for titles, headers."""
    return get_icon(name, (28, 28))

def icon_xl(name: str) -> ctk.CTkImage:
    """Extra large icon (40x40) — for dialogs, hero sections."""
    return get_icon(name, (40, 40))
