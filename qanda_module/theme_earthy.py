"""
Earthy theme for Q+A Voices application using warm terracotta and beige tones.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors, fonts, sizes

class EarthyTheme(Soft):
    """
    Custom earthy theme with warm terracotta, beige, and charcoal colors.
    """
    def __init__(self):
        # Use orange as base hue (closest to terracotta) for highlights
        super().__init__(
            primary_hue=colors.orange,
            secondary_hue=colors.stone, 
            neutral_hue=colors.stone
        )
        
        # CSS Color Mapping:
        # --background: #EAE0D5 (warm earthy beige)
        # --surface: #FFFDF5 (creamy off-white)
        # --primary-text: #2C2B2A (deep charcoal)
        # --primary-action: #C06C5D (terracotta)
        # --primary-action-hover: #a15a4d
        # --border-color: #DCD6CD
        
        theme_overrides = {
            # --- Background Colors ---
            "background_fill_primary": "#EAE0D5",        # Main background
            "background_fill_secondary": "#FFFDF5",      # Cards/panels
            "block_background_fill": "#FFFDF5",          # Component backgrounds
            
            # --- Text Colors ---
            "body_text_color": "#2C2B2A",               # Main text
            "body_text_color_subdued": "#5A5856",        # Secondary text
            
            # --- Primary Buttons (Terracotta) ---
            "button_primary_background_fill": "#C06C5D",
            "button_primary_background_fill_hover": "#a15a4d",
            "button_primary_text_color": "white",
            "button_primary_border_color": "#C06C5D",
            
            # --- Secondary Buttons (Light Beige) ---
            "button_secondary_background_fill": "#F8F6F2",
            "button_secondary_background_fill_hover": "#EAE0D5",
            "button_secondary_text_color": "#2C2B2A",
            "button_secondary_border_color": "#DCD6CD",
            
            # --- Input Fields ---
            "input_background_fill": "#FFFDF5",
            "input_border_color": "#DCD6CD",
            "input_border_color_focus": "#C06C5D",
            "input_shadow_focus": "0 0 0 2px #C06C5D40",
            
            # --- Borders ---
            "border_color_primary": "#DCD6CD",
            "border_color_accent": "#C06C5D",
            
            # --- Links & Accents ---
            "link_text_color": "#C06C5D",
            "link_text_color_hover": "#a15a4d",
            
            # --- Tabs ---
            "block_border_color": "#DCD6CD",
            "block_border_color_dark": "#C06C5D",
            
            # --- Shadows for cards ---
            "shadow_drop": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        }
        
        # Apply all overrides
        self.set(**theme_overrides)

# Create the theme instance
earthy_theme = EarthyTheme()