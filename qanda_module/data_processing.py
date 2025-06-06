"""
Data processing functions for panelist search, semantic matching, and database operations.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from typing import List, Dict, Tuple, Any
from sklearn.metrics.pairwise import cosine_similarity
from .constants import ALL_SUBSTANTIVE_TOPICS, POPULAR_TOPICS
from .constants import SPEAKER_NAME_FIXES

def get_latest_panelist_data(con) -> Dict[str, Tuple[str, str]]:
    """Get latest profession and URL for each panelist based on their most recent episode appearance."""
    
    # Get panelist data based on latest episode date (not ID)
    panelist_data = con.execute("""
        WITH panelist_latest_episodes AS (
            SELECT 
                dp.name,
                dp.profession, 
                dp.link,
                de.date as episode_date,
                dp.id as panelist_id,
                ROW_NUMBER() OVER (
                    PARTITION BY UPPER(dp.name) 
                    ORDER BY de.date DESC, dp.id DESC
                ) as rn
            FROM dim_panellist dp
            JOIN fact_responses fr ON UPPER(fr.speaker_name) = UPPER(dp.name)
            JOIN dim_episode de ON fr.episode_id = de.id
            WHERE fr.speaker_type = 3
            AND dp.name IS NOT NULL
        )
        SELECT name, profession, link, episode_date
        FROM panelist_latest_episodes 
        WHERE rn = 1
        ORDER BY name
    """).df()
    
    print(f"Loaded {len(panelist_data)} panelists using date-based latest episode logic")
    
    # Create lookup dictionary: name -> (profession, link)
    panelist_lookup = {}
    for _, row in panelist_data.iterrows():
        panelist_lookup[row['name']] = (row['profession'], row['link'])
    
    # Apply speaker name fixes for typos and mismatches
    fixed_lookup = {}
    for wrong_name, correct_name in SPEAKER_NAME_FIXES.items():
        if correct_name in panelist_lookup:
            fixed_lookup[wrong_name] = panelist_lookup[correct_name]
    
    # Merge fixes into main lookup
    panelist_lookup.update(fixed_lookup)
    
    return panelist_lookup


def build_panelist_search_index(helpers) -> List[Dict[str, Any]]:
    """
    Build searchable index of all panelists with metadata.
    
    Returns:
        List of dicts with panelist info sorted by activity
    """
    df_responses = helpers.df_reply
    df_panelists = helpers.df_guests
    
    # Get panelist stats from responses  
    panelist_stats = df_responses[df_responses["speaker_type"] == 3].groupby("speaker_name").agg({
        "episode_id": "nunique",  # Number of episodes appeared in
        "id": "count"            # Total number of responses
    }).rename(columns={"episode_id": "episodes", "id": "responses"})
    
    # Build search index
    search_index = []
    for name in panelist_stats.index:
        if pd.isna(name) or not name.strip():
            continue
            
        stats = panelist_stats.loc[name]
        
        # Try to find profile URL
        profile_url = None
        matching_panelist = df_panelists[df_panelists["name"] == name]
        if not matching_panelist.empty and "link" in df_panelists.columns:
            profile_url = matching_panelist.iloc[0]["link"]
            if pd.isna(profile_url):
                profile_url = None
        
        search_index.append({
            "name": name,
            "episodes": int(stats["episodes"]),
            "responses": int(stats["responses"]),
            "profile_url": profile_url,
            "search_text": name.lower()
        })
    
    # Sort by total responses (most active first)
    search_index.sort(key=lambda x: x["responses"], reverse=True)
    return search_index





def build_panelist_text_profile(helpers, panelist_name: str) -> str:
    """
    Build rich text profile for semantic matching.
    
    Args:
        helpers: QAHelpers object with dataframes
        panelist_name: Name of panelist
        
    Returns:
        Text profile combining topics and episodes
    """
    if not panelist_name:
        return ""
    
    # Get panelist's responses
    panelist_data = helpers.df_reply[
        (helpers.df_reply["speaker_name"] == panelist_name) & 
        (helpers.df_reply["speaker_type"] == 3)
    ]
    
    # Collect subtopics
    subtopics = panelist_data["subtopic"].dropna().unique()
    subtopic_text = " ".join(subtopics)
    
    # Get episode titles they appeared in
    episode_ids = panelist_data["episode_id"].unique()
    episodes = helpers.df_ep[helpers.df_ep["id"].isin(episode_ids)]
    episode_titles = " ".join(episodes["title"].fillna(""))
    
    # Combine for rich profile
    profile = f"{subtopic_text} {episode_titles}".strip()
    return profile if profile else "general political discussion"


def get_semantic_topic_matches(helpers, panelist_name: str, embedder, 
                              limit: int = 16, threshold: float = 0.3) -> List[str]:
    """Get semantically similar topics with smart filtering."""
    if not panelist_name:
        return POPULAR_TOPICS
    
    try:
        profile = build_panelist_text_profile(helpers, panelist_name)
        
        if not profile or len(profile.strip()) < 5:
            return POPULAR_TOPICS
        
        profile_embedding = embedder.encode([profile])
        topic_embeddings = embedder.encode(ALL_SUBSTANTIVE_TOPICS)
        
        if profile_embedding.shape[1] == 0 or topic_embeddings.shape[1] == 0:
            return POPULAR_TOPICS
        
        similarities = cosine_similarity(profile_embedding, topic_embeddings)[0]
        
        # Filter and sort by similarity
        valid_similarities = [
            (topic, score) for topic, score in zip(ALL_SUBSTANTIVE_TOPICS, similarities) 
            if not (np.isnan(score) or np.isinf(score)) and score > threshold
        ]
        valid_similarities.sort(key=lambda x: x[1], reverse=True)
        
        if len(valid_similarities) < 4:
            return POPULAR_TOPICS
        
        # Smart filtering: only show more topics if they're high quality
        high_quality_threshold = 0.5  # Higher bar for relevance
        
        # Always include top 8 that meet basic threshold
        matched_topics = [topic for topic, _ in valid_similarities[:8]]
        
        # Only add more if the additional topics are high quality
        if len(valid_similarities) > 8:
            additional_topics = [
                topic for topic, score in valid_similarities[8:limit] 
                if score > high_quality_threshold
            ]
            matched_topics.extend(additional_topics)
        
        return matched_topics
        
    except Exception as e:
        print(f"Semantic matching failed for {panelist_name}: {e}")
        return POPULAR_TOPICS
    
    
def extract_panelist_name(display_text: str) -> str:
    """
    Extract just the name from 'Name (X eps)' format.
    
    Args:
        display_text: Formatted text like "John Smith (5 eps)"
        
    Returns:
        Just the name part
    """
    if not display_text or display_text == "":
        return ""
    return display_text.split(" (")[0] if " (" in display_text else display_text


def enhanced_build_panelist_list(helpers) -> List[str]:
    """
    Build panelist list sorted by episodes, with episode counts.
    
    Args:
        helpers: QAHelpers object
        
    Returns:
        List of formatted panelist names with episode counts
    """
    try:
        search_index = build_panelist_search_index(helpers)
        
        # Sort by episodes (most frequent guests first)
        search_index.sort(key=lambda x: x["episodes"], reverse=True)
        
        # Format: "Name (X eps)" - short and clean
        enhanced_list = [f"{p['name']} ({p['episodes']} eps)" for p in search_index[:100]]
        return enhanced_list
    except Exception as e:
        print(f"Warning: Using fallback panelist list: {e}")
        return ["Malcolm Turnbull (15 eps)", "Penny Wong (12 eps)"]


def prepare_ui_data(helpers, config):
    """
    Prepare all data needed for UI initialization.
    
    Args:
        helpers: QAHelpers object
        config: System configuration
        
    Returns:
        Dict with all prepared data
    """
    # Get database connection
    import duckdb
    con = duckdb.connect(config.duck_db_name)
    
    # Get panelist data
    panelist_lookup = get_latest_panelist_data(con)
    panelist_list = enhanced_build_panelist_list(helpers)
    
    # Attach to helpers for backwards compatibility
    helpers.panelist_lookup = panelist_lookup
    helpers.con = con
    
    return {
        'panelist_lookup': panelist_lookup,
        'panelist_list': panelist_list,
        'con': con
    }
