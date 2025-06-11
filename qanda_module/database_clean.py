"""
Clean data types upstream during JSON loading rather than downstream conversions.
"""

import os
import json
import pandas as pd
import duckdb
from typing import Dict, Tuple, Optional, List, Any
import logging

logger = logging.getLogger(__name__)


def safe_int(value) -> Optional[int]:
    """Convert value to int or None if invalid."""
    if value is None or value == '':
        return None
    
    try:
        # Handle decimal strings like "123.0"
        if isinstance(value, str) and '.' in value:
            float_val = float(value)
            if float_val.is_integer():
                return int(float_val)
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_string(value) -> Optional[str]:
    """Convert value to clean string or None if empty."""
    if value is None:
        return None
    
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else None
    
    return str(value).strip() or None


def clean_responses_data(responses: List[Dict]) -> List[Dict]:
    """Clean fact_responses data with proper type enforcement."""
    cleaned = []
    
    for response in responses:
        # Clean IDs - convert to proper integers or None
        response['id'] = safe_int(response.get('id'))
        response['question_id'] = safe_int(response.get('question_id'))
        response['speaker_id'] = safe_int(response.get('speaker_id'))
        response['episode_id'] = safe_int(response.get('episode_id'))
        
        # Clean speaker type - must be 1, 2, or 3
        speaker_type = safe_int(response.get('speaker_type'))
        if speaker_type not in [1, 2, 3]:
            speaker_type = None
        response['speaker_type'] = speaker_type
        
        # Clean strings
        response['speaker_name'] = safe_string(response.get('speaker_name'))
        response['content'] = safe_string(response.get('content'))
        response['subtopic'] = safe_string(response.get('subtopic'))
        
        # Only include if we have essential fields
        if response['id'] is not None and response['content']:
            cleaned.append(response)
    
    logger.info(f"Cleaned responses: {len(responses)} → {len(cleaned)}")
    return cleaned


def clean_json_data(json_data: List[Dict], table_name: str) -> List[Dict]:
    """Clean and standardize data types at the JSON level."""
    
    if table_name == "fact_responses":
        return clean_responses_data(json_data)
    # Add other table cleaners as needed
    
    return json_data


def load_database_clean(
    base_path: Optional[str] = None, 
    force_reload: bool = False,
    db_path: str = "./data/qanda.duckdb"
) -> Tuple[duckdb.DuckDBPyConnection, Dict[str, pd.DataFrame]]:
    """
    Load database with upstream data cleaning.
    """
    db_exists = os.path.exists(db_path)
    con = duckdb.connect(db_path)
    dataframes = {}

    if not db_exists or force_reload:
        if not base_path:
            raise ValueError("base_path must be provided when creating a new database")

        file_map = {
            "dim_panellist": f"{base_path}/panellists1.json",
            "dim_question": f"{base_path}/questions1.json", 
            "dim_episode": f"{base_path}/episodes1.json",
            "fact_responses": f"{base_path}/responses1.json",
        }

        for table, path in file_map.items():
            if not os.path.exists(path):
                logger.warning(f"File not found: {path}")
                continue
                
            logger.info(f"Loading {table}...")
            
            with open(path) as f:
                raw_data = json.load(f)
            
            # Clean data at JSON level
            clean_data = clean_json_data(raw_data, table)
            
            # Convert to DataFrame
            df = pd.json_normalize(clean_data)
            dataframes[table] = df
            
            # Create table in DuckDB
            con.execute(f"DROP TABLE IF EXISTS {table}")
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM df")
            
            logger.info(f"{table}: {len(df)} records loaded")
    else:
        logger.info("Loading existing database...")
        for table in ["dim_panellist", "dim_question", "dim_episode", "fact_responses"]:
            try:
                df = con.execute(f"SELECT * FROM {table}").df()
                dataframes[table] = df
                logger.info(f"{table}: {len(df)} records")
            except Exception as e:
                logger.warning(f"Could not load table {table}: {e}")

    return con, dataframes
