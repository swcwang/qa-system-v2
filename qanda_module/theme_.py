"""
Defines the custom Gradio theme for the Q+A Voices application.
This module decouples the theme definition from the UI layout code.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors, fonts, sizes
from .theme import qanda_theme

# Inherit directly from gr.themes.Soft to get its fonts and base styles
class QandATheme(Soft):
    """
    A custom theme that inherits from Gradio's Soft theme and applies
    a burgundy, charcoal, and gold palette.
    """
    def __init__(self):
        # MODIFIED: Set the primary_hue to amber (gold). This will automatically
        # color highlights like sliders and selected radio buttons in gold tones.
        super().__init__(
            primary_hue=colors.amber, 
            secondary_hue=colors.slate,
            neutral_hue=colors.slate
        )
        
        # Now, we only need to override the primary button to be burgundy,
        # as all other highlights will correctly inherit the gold/amber color.
        theme_overrides = {
            # --- Primary Action Button (Burgundy) ---
            "button_primary_background_fill": "#800000",
            "button_primary_background_fill_hover": "#660000",
            "button_primary_text_color": "white",
            
            # --- Secondary Button (Light Grey) ---
            "button_secondary_background_fill": "#f1f5f9",
            "button_secondary_background_fill_hover": "#e2e8f0",
            "button_secondary_text_color": "#36454F",

            # --- Links & Other ---
            "link_text_color": "#800000",
            "link_text_color_hover": "#660000",
        }
        
        # Apply all overrides at once using dictionary unpacking
        self.set(**theme_overrides)

# Create a single, reusable instance of the theme
qanda_theme = QandATheme()
