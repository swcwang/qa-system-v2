"""
Q&A System V2 - Clean Modular Interface
Refactored UI with extracted modules for better maintainability.
"""

import sys
import os

# Import core system setup (imports are already correct!)
from qanda_module.config import setup_system
from qanda_module.ui_gradio import launch_ui_with_toggle

def create_demo():
    """Create and return the Gradio demo interface."""
    print("🚀 Setting up system...")
    
    # Get the path to config.yaml relative to this file
    config_path = "config.yaml"  #os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    
    # Setup system components
    helpers, qa_chain, config = setup_system(config_path)
    
    print("✅ System setup complete!")
    print(f"Model: {config.chat_model_name}")
    print(f"Temperature: {config.temperature}")
    print(f"Debug: {config.debug_enabled}")
    
    # Create UI with new design
    print("🎨 Creating new UI...")
    demo = launch_ui_with_toggle(
        helpers,
        qa_chain,
        config,
        design="new"  # Always use new design for HF Spaces
    )
    
    print("🎯 Demo created using NEW design")
    return demo

# Create the demo
demo = create_demo()

# For Hugging Face Spaces, we don't need to call demo.launch()
# The space will handle that automatically 