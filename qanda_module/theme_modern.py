"""
Modern theme with refined crimson red and clean grey tones.
Professional and sophisticated design.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors

class ModernTheme(Soft):
    """
    Clean modern theme with refined crimson red and light grey backgrounds.
    """
    def __init__(self):
        # Use red as base but we'll override with specific crimson
        super().__init__(
            primary_hue=colors.red,
            secondary_hue=colors.gray,
            neutral_hue=colors.gray
        )
        
        # Colors from your CSS:
        # --background: #f4f4f4 (light warm grey)
        # --surface: #ffffff (crisp white)  
        # --primary-text: #1F1F1F (dark charcoal)
        # --primary-action: #B91C1C (refined crimson red)
        # --primary-action-hover: #991B1B
        # --border-color: #e5e7eb
        
        theme_overrides = {
            # --- Background Colors ---
            "background_fill_primary": "#f4f4f4",        # Light warm grey
            "background_fill_secondary": "#ffffff",      # Crisp white cards
            "block_background_fill": "#ffffff",          # Component backgrounds
            
            # --- Text Colors ---
            "body_text_color": "#1F1F1F",               # Dark charcoal
            "body_text_color_subdued": "#4B5563",        # Medium grey for secondary text
            
            # --- Primary Buttons (Refined Crimson) ---
            "button_primary_background_fill": "#B91C1C",
            "button_primary_background_fill_hover": "#991B1B", 
            "button_primary_text_color": "white",
            "button_primary_border_color": "#B91C1C",
            
            # --- Secondary Buttons (Clean Grey) ---
            "button_secondary_background_fill": "#f3f4f6",
            "button_secondary_background_fill_hover": "#e5e7eb",
            "button_secondary_text_color": "#1F1F1F",
            "button_secondary_border_color": "#e5e7eb",
            
            # --- Input Fields ---
            "input_background_fill": "#f9fafb",
            "input_border_color": "#d1d5db", 
            "input_border_color_focus": "#B91C1C",
            "input_shadow_focus": "0 0 0 2px #B91C1C40",
            
            # --- Borders ---
            "border_color_primary": "#e5e7eb",
            "border_color_accent": "#B91C1C",
            
            # --- Links & Accents ---
            "link_text_color": "#B91C1C",
            "link_text_color_hover": "#991B1B",
            
            # --- Highlighted Elements ---
            "checkbox_background_color_selected": "#B91C1C",
            "radio_circle": "#B91C1C",
            "slider_color": "#B91C1C",
        }
        
        # Apply overrides
        self.set(**theme_overrides)

# Create the theme instance  
modern_theme = ModernTheme()