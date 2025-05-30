"""
Clean, lean refactored pipeline with minimal debugging.
"""

import os
import logging
from typing import List, Tuple
from openai import OpenAI

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
    """Generate AI response from documents."""
    # Build context
    context_text = "\n\n".join(doc.page_content for doc in docs)
    
    # Simple prompt - you can enhance this later
    prompt = f"""Please answer this question based on the context provided.

Context: {context_text}

Question: {query}

Please provide a {style.lower()} response."""
    
    # Call OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    stream = client.chat.completions.create(
        model=config.chat_model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=config.temperature,
        stream=True,
    )
    
    response = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
            
    return response


def process_question_with_style(helpers, qa_chain, query: str, k: int, style: str, 
                               config) -> Tuple[str, str, str, None, str]:
    """
    Main pipeline - simple and clean.
    
    Returns: (formatted_answer, sources, status, pdf_output, tech_info)
    """
    try:
        # Pipeline steps
        docs = retrieve_enhanced_documents(qa_chain.retriever, query, k, config.debug_enabled)
        response = generate_ai_response(docs, query, style, config)
        
        # Simple formatting - enhance this later
        formatted_answer = response
        sources = f"Based on {len(docs)} documents"
        tech_info = f"Model: {config.chat_model_name}, Temp: {config.temperature}"
        
        return formatted_answer, sources, "✅ Completed!", None, tech_info
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, "", f"❌ {error_msg}", None, ""
