"""
Clean, lean refactored pipeline with minimal debugging.
"""

import os
import logging
from typing import List, Tuple
from openai import OpenAI
import re

logger = logging.getLogger(__name__)


class SpeakerTypes:
    """Speaker type constants."""
    HOST = 1
    AUDIENCE = 2
    PANELIST = 3


def log_debug_stats(stage: str, documents) -> None:
    """Simple debug logging - just warn about missing panelists."""
    panelist_count = sum(1 for doc in documents 
                        if doc.metadata.get('speaker_type') == SpeakerTypes.PANELIST)
    
    if panelist_count == 0:
        logger.warning(f"{stage}: No panelists found in {len(documents)} documents")
    elif panelist_count < 3:
        logger.info(f"{stage}: Only {panelist_count} panelists in {len(documents)} docs")


def retrieve_enhanced_documents(retriever, query: str, k: int, debug: bool = False):
    """Retrieve and enhance documents."""
    retriever.k = k
    docs = retriever._get_relevant_documents(query)
    
    if debug:
        log_debug_stats('enhanced_retrieval', docs)
    
    return docs


def generate_ai_response(docs, query: str, style: str, config) -> str:
    """Generate AI response with inline episode ID citations"""
    
    context_text = "\n\n".join(doc.page_content for doc in docs)
    
    # Ask for INLINE citations during the response
    prompt = f"""Please answer this question based on the context provided.

Context: {context_text}

Question: {query}

Please provide a {style.lower()} response. When referencing information from the context, include the episode ID inline like this: "Joyce argued that climate action is important Episode ID: 240."

Use the exact episode ID numbers shown in brackets in the context."""
    
   # Rest of function unchanged...
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model=config.chat_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"Error generating response: {e}"


def format_response_with_episode_links(ai_response, con, helpers):
    """Convert episode IDs to sequential references AND link panelist names with profiles"""
    import re
    
    # Get panelist_lookup from helpers
    panelist_lookup = getattr(helpers, 'panelist_lookup', {})
    
    # Step 1: Handle episode ID citations
    episode_ids = re.findall(r'Episode ID: (\d+)', ai_response)
    
    # Create sequential mapping
    unique_episodes = []
    episode_to_ref = {}
    for episode_id in episode_ids:
        if episode_id not in episode_to_ref:
            ref_num = len(unique_episodes) + 1
            episode_to_ref[episode_id] = ref_num
            unique_episodes.append(episode_id)
    
    # Look up episode details
    episode_details = {}
    for episode_id in unique_episodes:
        try:
            result = con.execute(f"""
                SELECT date, title, url 
                FROM dim_episode 
                WHERE id = {episode_id}
            """).fetchone()
            
            if result:
                date, title, url = result
                episode_details[episode_id] = {'date': date, 'title': title, 'url': url}
        except Exception as e:
            print(f"Error looking up episode {episode_id}: {e}")
    
    # Replace inline episode citations with colored sequential references
    formatted_response = ai_response
    for episode_id in episode_ids:
        if episode_id in episode_to_ref:
            pattern = f"Episode ID: {episode_id}"
            ref_num = episode_to_ref[episode_id]
            replacement = f'<sup><span style="color: #dc2626;">[{ref_num}]</span></sup>'
            formatted_response = formatted_response.replace(pattern, replacement, 1)
    
    # Remove AI's "Sources Used:" section if present
    formatted_response = re.sub(r'\*\*Sources Used:\*\*.*$', '', formatted_response, flags=re.DOTALL).strip()
    
    # Step 2: Link panelist names in the response
    linked_names = set()
    
    for panelist_name, (profession, url) in panelist_lookup.items():
        # Skip if no valid URL or already linked
        if not url or str(url) == 'nan' or panelist_name in linked_names:
            continue
            
        # Try case-insensitive word boundary matching
        pattern = rf'\b{re.escape(panelist_name)}\b'
        
        if re.search(pattern, formatted_response, re.IGNORECASE):
            # Replace first occurrence with clickable link
            replacement = f'[{panelist_name}]({url})'
            formatted_response = re.sub(pattern, replacement, formatted_response, count=1, flags=re.IGNORECASE)
            linked_names.add(panelist_name)
    
    # Step 3: Build episode sources list
    source_links = []
    for i, episode_id in enumerate(unique_episodes, 1):
        if episode_id in episode_details:
            details = episode_details[episode_id]
            if details['url']:
                link = f"[{i}] [{details['date']}: {details['title']}]({details['url']})"
            else:
                link = f"[{i}] {details['date']}: {details['title']}"
            source_links.append(link)
    
    # Add episode sources section
    if source_links:
        sources_section = "\n".join(f"- {link}" for link in source_links)
        formatted_response += "\n\n**Sources:**\n" + sources_section
    
    return formatted_response


def process_question_with_style(helpers, qa_chain, query: str, k: int, style: str, 
                               config) -> Tuple[str, str, str, None, str]:
    """Main pipeline with episode link formatting."""
    try:
        docs = retrieve_enhanced_documents(qa_chain.retriever, query, k, config.debug_enabled)
        response = generate_ai_response(docs, query, style, config)
        
        # Format with episode links AND panelist links
        con = getattr(helpers, 'con', None)
        if con:
            formatted_response = format_response_with_episode_links(response, con, helpers)  # Pass helpers
        else:
            formatted_response = response
        
        sources = ""
        tech_info = f"Model: {config.chat_model_name}, Temp: {config.temperature}"
        
        return formatted_response, sources, "✅ Completed!", None, tech_info
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, "", f"❌ {error_msg}", None, ""