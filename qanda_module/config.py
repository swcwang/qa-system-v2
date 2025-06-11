"""
Simple external configuration - just load YAML, nothing fancy.
"""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class QAConfig:
    """Simple configuration class."""
    log_file_name: str = "qa_usage_log.csv"
    
    ui_theme: str = "soft"
    # Vector store
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    chroma_path: str = "./data/chroma_db_june11_clean" # "./data/chroma_db_large"
    collection_name: str = "qa_v3_enhanced" #"qa_chunks" #"qa_chunks_v2"
    n_chunks_to_retrieve_k: int = 20
    
    # AI settings
    chat_model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    
    # Enhancement settings
    min_host_length: int = 50
    min_panelist_length: int = 20
    max_results: int = 15
    
    # Data paths
    duck_db_name: str = "./data/qanda_june11_clean.duckdb" #"./data/qanda_may.duckdb" #"./data/qanda_v2.duckdb"
    input_json_path: str = "./data/input_json2"
    
    # Debug
    debug_enabled: bool = False
    
    @classmethod
    def from_file(cls, config_path: str = "config.yaml") -> 'QAConfig':
        """Load config from YAML file, use defaults if file missing."""
        if not os.path.exists(config_path):
            logger.info(f"Config file {config_path} not found, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Create instance with file values
            return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
            
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using defaults")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return {field.name: getattr(self, field.name) 
                for field in self.__dataclass_fields__.values()}


def get_config(config_path: str = "config.yaml") -> QAConfig:
    """Load configuration - simple one-liner."""
    return QAConfig.from_file(config_path)


def setup_system(config_path: str = "config.yaml"):
    """Setup entire system with config file."""
    try:
        from .database_clean import load_database_clean
        from .legacy_imports import setup_qa_chain, ImprovedQAHelpers
        from chromadb import PersistentClient
        
        config = get_config(config_path)
        
        # Load data
        con, dataframes = load_database_clean(
            base_path=config.input_json_path,
            db_path=config.duck_db_name
        )
        
        # Setup vector store
        client = PersistentClient(path=config.chroma_path)
        collection = client.get_or_create_collection(config.collection_name)
        
        # Setup helpers and QA chain
        helpers = ImprovedQAHelpers(dataframes)
        qa_chain = setup_qa_chain(collection, config.to_dict())
        
        return helpers, qa_chain, config
        
    except ImportError as e:
        print(f"⚠️  Some modules not yet migrated: {e}")
        print("You'll need to copy over legacy modules or install dependencies")
        return None, None, get_config(config_path)
