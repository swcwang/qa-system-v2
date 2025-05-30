"""
Basic tests for Q&A System V2
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from qanda_module.config import get_config, QAConfig


def test_config_loading():
    """Test configuration loading."""
    # Test default config
    config = QAConfig()
    assert config.chat_model_name == "gpt-4o-mini"
    assert config.temperature == 0.3
    
    # Test dict conversion
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert 'chat_model_name' in config_dict


def test_config_from_file():
    """Test loading config from file."""
    # This will use defaults if config.yaml doesn't exist
    config = get_config("../config.yaml")
    assert isinstance(config, QAConfig)


if __name__ == "__main__":
    test_config_loading()
    test_config_from_file()
    print("✅ Basic tests passed!")
