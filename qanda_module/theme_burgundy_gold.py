"""
Fresh Burgundy Gold theme - new file to bypass cache issues.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors

class BurgundyGoldTheme(Soft):
    def __init__(self):
        super().__init__(
            primary_hue=colors.stone,
            secondary_hue=colors.stone, 
            neutral_hue=colors.stone
        )
        
        theme_overrides = {
            # --- Backgrounds ---
            "background_fill_primary": "#FAF7F0",
            "background_fill_secondary": "#FFFFFF",
            
            # --- Text ---
            "body_text_color": "#2C2C2C", 
            "body_text_color_subdued": "#5A5A5A",
            
            # --- PRIMARY BUTTONS (Deep Burgundy) ---
            "button_primary_background_fill": "#722F37",
            "button_primary_background_fill_hover": "#5D252B",
            "button_primary_text_color": "#FAF7F0",
            
            # --- SECONDARY BUTTONS (Warm Gold-Beige) ---
            "button_secondary_background_fill": "#F5F1E8",
            "button_secondary_background_fill_hover": "#EDE6D3",
            "button_secondary_text_color": "#722F37",
            "button_secondary_border_color": "#E8DCC0",
            
            # --- RADIO BUTTONS & SELECTIONS (Warm Gold) ---
            "checkbox_background_color_selected": "#D4AF37",  # Brighter gold
            "radio_circle": "#D4AF37",                        # Brighter gold
            "checkbox_border_color_selected": "#B8941C",
            
            # --- BUTTON SELECTIONS (Fix the grey topic buttons!) ---
            "button_primary_background_fill_dark": "#B8941C", # Gold for selected states
            "button_secondary_background_fill_dark": "#EDE6D3", # Warm beige for selected
            
            # --- SLIDERS (Burgundy) ---
            "slider_color": "#722F37",
            
            # --- INPUT FIELDS ---
            "input_background_fill": "#FEFCF7",
            "input_border_color": "#E8DCC0",
            "input_border_color_focus": "#722F37",
            "input_shadow_focus": "0 0 0 2px #722F3740",
            
            # --- BORDERS ---
            "border_color_primary": "#E8DCC0",
            "border_color_accent": "#722F37",
            
            # --- LINKS ---
            "link_text_color": "#B8941C",
            "link_text_color_hover": "#722F37",
            
            # --- ADDITIONAL OVERRIDES FOR STUBBORN ELEMENTS ---
            "color_accent": "#D4AF37",                        # Force accent to gold
            "color_accent_soft": "#D4AF3720",                 # Soft gold background
            "block_label_background_fill": "#F5F1E8",         # Warm label backgrounds
        }
        
        self.set(**theme_overrides)

# Create instance
burgundy_gold_theme = BurgundyGoldTheme()