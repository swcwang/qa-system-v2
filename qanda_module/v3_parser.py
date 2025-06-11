"""
V3 Content Parser - Handles new V3 embedding format
NEW MODULE: Parses V3 content format and reconstructs metadata expected by existing code
SIMPLIFIED: Trusts clean data from user's name_cleaner.py preprocessing
"""

def parse_v3_content(content_string: str) -> tuple[dict, str]:
    """NEW FUNCTION: Parse V3 format into metadata components and clean content.
    
    Handles format: "Topic: Banking;;Ep 615;;Banks, Bikies and Broadband;;2019-03-15;;Diane Dent;;actual content"
    Returns reconstructed metadata dict compatible with existing code and the actual content.
    SIMPLIFIED: Assumes clean speaker names from preprocessed database.
    """
    # Check if this is V3 format by counting delimiters
    if content_string.count(';;') < 5 or not content_string.startswith('Topic: '):
        # Not V3 format - return empty metadata and original content
        return {}, content_string
    
    try:
        parts = content_string.split(';;', 5)  # Split into exactly 6 parts
        
        # Extract fields (trust clean data - no complex validation needed)
        topic = parts[0][7:] if parts[0].startswith('Topic: ') else ''
        
        # Extract episode ID (remove "Ep " prefix and convert to int)
        episode_id_str = parts[1].replace('Ep ', '') if parts[1].startswith('Ep ') else '0'
        try:
            episode_id = int(episode_id_str)
        except ValueError:
            episode_id = 0
        
        # Extract other fields (data is already clean from preprocessing)
        episode_title = parts[2]
        episode_date = parts[3] 
        speaker_name = parts[4]  # Already normalized by name_cleaner.py
        actual_content = parts[5]
        
        # Build metadata dict with field names expected by existing code
        metadata_dict = {
            'speaker_name': speaker_name,
            'episode_title': episode_title,
            'title': episode_title,  # Alias for compatibility
            'episode_date': episode_date,
            'episode_id': episode_id,
            'subtopic': topic if topic else 'General'
        }
        
        return metadata_dict, actual_content
        
    except (IndexError, ValueError) as e:
        # Malformed V3 content - return empty metadata and original content
        print(f"Warning: Failed to parse V3 content: {e}")
        return {}, content_string


def enhance_document_metadata(doc, original_metadata: dict) -> None:
    # Parse V3 content if present
    parsed_metadata, clean_content = parse_v3_content(doc.page_content)
    
    # KEEP ORIGINAL V3 CONTENT FOR AI - DON'T STRIP IT
    # (Remove the doc.page_content = clean_content line)
    
    # Merge original metadata with parsed metadata
    enhanced_metadata = original_metadata.copy()
    enhanced_metadata.update(parsed_metadata)
    
    # Add V3-specific fields
    if 'qs' in original_metadata:
        enhanced_metadata['quality_score'] = original_metadata['qs']
    if 'typ' in original_metadata:
        enhanced_metadata['speaker_type'] = original_metadata['typ']
    if 'sid' in original_metadata:
        enhanced_metadata['speaker_id'] = original_metadata['sid']
    if 'qid' in original_metadata:
        enhanced_metadata['question_id'] = original_metadata['qid']
    
    # Update document metadata
    doc.metadata = enhanced_metadata