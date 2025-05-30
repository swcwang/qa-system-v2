"""
Q&A System V2 - Clean refactored version
"""

__version__ = "2.0.0"

from .config import get_config, setup_system
from .retrieval_lean import process_question_with_style, SpeakerTypes

__all__ = ["get_config", "setup_system", "process_question_with_style", "SpeakerTypes"]
