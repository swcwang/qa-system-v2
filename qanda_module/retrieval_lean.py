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
    """Generate AI response with episode citations and style-based length."""
    # Build context
    context_text = "\n\n".join(doc.page_content for doc in docs)
    # Style-specific instructions
    style_instructions = {
        "concise": "Provide a concise response (up to 150 words) focusing on key points only.",
        "standard": "Provide a response (150-300 words) with moderate detail and analysis.", 
        "detailed": "Provide a detailed response (300-1000 words) with comprehensive analysis and multiple perspectives."
    }
    length_instruction = style_instructions.get(style.lower(), style_instructions["standard"])
    prompt = f"""Please answer this question based on the context provided.
    FORMATTING: Use markdown formatting with:
    - ## Main headings for key sections
    - **Bold text** for panelist names and key points
    - > Quote blocks for direct quotes from panelists

    IMPORTANT: When referencing information, add episode citations at the end of each paragraph using the format "Episode ID: XXX" where XXX is the episode number from the context.
    Example: "Climate action remains a contentious issue with various approaches proposed. Episode ID: 615 Episode ID: 422"
    {length_instruction}
    Structure your response with clear sections, use headings to organize main points, and include specific quotes in quote blocks where relevant.
    Context: {context_text}
    Question: {query}
    Response:"""
    
    # Rest of function unchanged...
    
    # Call OpenAI
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
        
        # MODIFIED: Use unified formatter from helpers
        if hasattr(helpers, 'format_response_with_links'):
            formatted_response, sources = helpers.format_response_with_links(response, docs)
        else:
            # Simple fallback
            formatted_response = response
            sources = ""
        
        tech_info = f"Model: {config.chat_model_name}, Temp: {config.temperature}"
        
        return formatted_response, sources, "✅ Completed!", None, tech_info
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, "", f"❌ {error_msg}", None, ""

# REMOVED: format_response_with_episode_links() function - unified formatter only