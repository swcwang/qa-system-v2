"""
Test script to run the Q&A app locally
"""

import sys
#sys.path.append('.')

from app import demo

if __name__ == "__main__":
    # Launch the interface locally
    print("🌐 Launching Gradio interface locally...")
    
    demo.launch(
        share=False,  # Set to True for public link
        server_port=7860,
        show_error=True,
        debug=True  # Shows more info in console
    ) 