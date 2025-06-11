"""
Forest Green theme with cream backgrounds.
Natural, calming design perfect for thoughtful discussions.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors

class ForestGreenTheme(Soft):
    """
    Calming forest green theme with cream backgrounds.
    """
    def __init__(self):
        super().__init__(
            primary_hue=colors.green,
            secondary_hue=colors.stone,
            neutral_hue=colors.stone
        )
        
        theme_overrides = {
            # --- Background Colors ---
            "background_fill_primary": "#F7F5F0",        # Warm cream
            "background_fill_secondary": "#FFFFFF",      # White cards
            "block_background_fill": "#FFFFFF",
            
            # --- Text Colors ---
            "body_text_color": "#1F2937",               # Dark grey
            "body_text_color_subdued": "#4B5563",
            
            # --- Primary Buttons (Forest Green) ---
            "button_primary_background_fill": "#065F46",
            "button_primary_background_fill_hover": "#047857", 
            "button_primary_text_color": "white",
            
            # --- Secondary Buttons ---
            "button_secondary_background_fill": "#F0FDF4",
            "button_secondary_background_fill_hover": "#DCFCE7",
            "button_secondary_text_color": "#065F46",
            "button_secondary_border_color": "#BBF7D0",
            
            # --- Input Fields ---
            "input_background_fill": "#FEFFFE",
            "input_border_color": "#D1D5DB", 
            "input_border_color_focus": "#10B981",
            "input_shadow_focus": "0 0 0 2px #10B98140",
            
            # --- Borders ---
            "border_color_primary": "#E5E7EB",
            "border_color_accent": "#10B981",
            
            # --- Links & Accents ---
            "link_text_color": "#059669",
            "link_text_color_hover": "#047857",
        }
        
        self.set(**theme_overrides)

forest_green_theme = ForestGreenTheme()