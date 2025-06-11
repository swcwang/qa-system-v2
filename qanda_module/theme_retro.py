"""
Retro graphic theme inspired by mid-century poster design.
Bold coral-red and navy with cream backgrounds.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors

class RetroGraphicTheme(Soft):
    """
    Bold retro theme with coral-red primary actions and deep navy accents.
    """
    def __init__(self):
        # Use red as primary hue for the coral color
        super().__init__(
            primary_hue=colors.red,
            secondary_hue=colors.slate,
            neutral_hue=colors.stone
        )
        
        # Only use VALID Gradio theme properties
        theme_overrides = {
            # --- Background Colors ---
            "background_fill_primary": "#F7F5F3",        # Warm cream background
            "background_fill_secondary": "#FFFEF8",      # Off-white for cards
            
            # --- Text Colors ---
            "body_text_color": "#1A1A2E",               # Deep navy text
            "body_text_color_subdued": "#4A4A5E",        # Lighter navy
            
            # --- Primary Buttons (Coral-Red) ---
            "button_primary_background_fill": "#FF5733",
            "button_primary_background_fill_hover": "#E8431F", 
            "button_primary_text_color": "white",
            
            # --- Secondary Buttons ---
            "button_secondary_background_fill": "#F0EDE8",
            "button_secondary_background_fill_hover": "#E5E0D8",
            "button_secondary_text_color": "#1A1A2E",
            
            # --- Input Fields ---
            "input_background_fill": "#FFFEF8",
            "input_border_color": "#D5CFC5", 
            "input_border_color_focus": "#FF5733",
            
            # --- Borders ---
            "border_color_primary": "#D5CFC5",
            
            # --- Links ---
            "link_text_color": "#FF5733",
            "link_text_color_hover": "#E8431F",
        }
        
        # Apply overrides
        self.set(**theme_overrides)

# Create the theme instance  
retro_theme = RetroGraphicTheme()