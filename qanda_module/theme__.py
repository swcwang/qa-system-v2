"""
Defines the custom Gradio theme for the Q+A Voices application.
This is the definitive, correct method for styling a Gradio app.
"""

from gradio.themes import Soft
from gradio.themes.utils import colors

class QandATheme(Soft):
    """
    A custom theme inheriting from gr.themes.Soft to get its fonts and base styles,
    while applying a specific burgundy, charcoal, and "Old Gold" palette.
    """
    def __init__(self):
        # We inherit from Soft() to get its fonts and general layout.
        # We set the primary_hue to amber (gold). This will make all default
        # highlights, like selected radio buttons and sliders, use this gold tone.
        super().__init__(
            primary_hue=colors.amber, 
            secondary_hue=colors.slate,
            neutral_hue=colors.slate
        )
        
        # Now we define our specific overrides.
        # This is where we force the main button to be burgundy, overriding the gold.
        theme_overrides = {
            # --- Primary Action Button (Burgundy) ---
            "button_primary_background_fill": "#800000",
            "button_primary_background_fill_hover": "#660000",
            "button_primary_text_color": "white",
            
            # --- Secondary Button (Light Grey) ---
            "button_secondary_background_fill": "#f1f5f9",
            "button_secondary_background_fill_hover": "#e2e8f0",
            "button_secondary_text_color": "#36454F",

            # --- Links & Text (Inherited but can be overridden if needed) ---
            "link_text_color": "#800000",
            "link_text_color_hover": "#660000",
            
            # --- Specific Accent Overrides (A more "Old Gold" tone) ---
            # This allows us to have a slightly different gold than the base 'amber'.
            "slider_color": "#A16207",
            # REMOVED invalid 'slider_color_dark' if not supported, rely on hue
            
            # Using valid properties for selected radio/checkboxes
            "checkbox_label_background_fill_selected": "#fefce8",
            "checkbox_border_color_selected": "#ca8a04",
        }
        
        # Apply all our overrides at once
        self.set(**theme_overrides)

# Create a single, reusable instance of the theme
qanda_theme = QandATheme()
