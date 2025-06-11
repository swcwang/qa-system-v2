"""
Gradio UI components and event handling for the Q&A system.
"""

import gradio as gr
from typing import List, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
import pandas as pd
import importlib
import sys
import os
import base64
from .constants import POPULAR_TOPICS, UI_CSS, LEGACY_UI_CSS
from .data_processing import (
    extract_panelist_name, get_semantic_topic_matches, 
    prepare_ui_data, enhanced_build_panelist_list
)
# Force reload the specific theme module
if 'qanda_module.theme_pure' in sys.modules:
    importlib.reload(sys.modules['qanda_module.theme_pure'])

from .retrieval_lean import process_question_with_style
#from .theme_earthy import earthy_theme
#from .theme_retro import retro_theme
from .theme_modern import modern_theme
#from .theme_burgundy_pure import burgundy_pure_theme
#from .theme_forest import forest_green_theme
#from .theme_burgundy_fixed import burgundy_fixed_theme
from .theme_burgundy_gold import burgundy_gold_theme

# --- NEW: Helper functions for creating themed buttons ---
def PrimaryButton(value, **kwargs):
    """Creates a Gradio Button with the 'primary' variant."""
    return gr.Button(value, variant="primary", **kwargs)

def SecondaryButton(value, **kwargs):
    """Creates a Gradio Button with the 'secondary' variant."""
    return gr.Button(value, variant="secondary", **kwargs)

def get_logo_base64():
    """Convert logo to base64 for embedding."""
    try:
        with open("./logo2.png", "rb") as f:
            img_data = f.read()
            return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"Logo loading error: {e}")
        return None
    
def get_background_image_base64():
    """Convert background image to base64."""
    try:
        with open("./panel_bk.png", "rb") as f:  # adjust filename
            img_data = f.read()
            return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"Background image loading error: {e}")
        return None
    
def get_gradio_theme(theme_name: str):
    """Get Gradio theme by name"""
    themes = {
        "soft": gr.themes.Soft(),
        "default": gr.themes.Default(),
        "modern": modern_theme,  
        "burgundy_gold": burgundy_gold_theme,  
    }
    return themes.get(theme_name, gr.themes.Soft())

def generate_smart_questions(panelist: str = "", topic: str = "") -> List[str]:
    """Generate context-aware questions with general questions included."""
    if panelist and topic:
        return [
            f"What are {panelist}'s views on {topic.lower()}?", 
            f"How did {panelist} handle {topic.lower()} questions?",
            f"What's {panelist}'s stance on {topic.lower()} policy?"
        ]
    elif topic == "General Politics":
        if panelist:
            return [
                f"What are {panelist}'s most notable political views?",
                f"How has {panelist}'s political stance evolved over time?",
                f"What are {panelist}'s most controversial political positions?"
            ]
        else:
            return [
                "What are the most controversial political debates?",
                "How have political views changed over the years?",
                "What are the biggest political divisions in Australia?"
            ]
    elif panelist:
        panelist_questions = [
            f"What are {panelist}'s most notable views?",
            f"Has {panelist} changed their political views over time?",
            f"What are {panelist}'s most controversial positions?",
            f"How did {panelist} handle tough questions?"
        ]
        
        general_questions = [
            "What do panelists think of climate change?",
            "How do panelists view immigration policy?", 
            "What are different perspectives on the economy?",
            "What are the most controversial political debates?",
            "Which panelists had the most heated exchanges?",
            "How have political views changed over the years?"
        ]
        
        # Combine: panelist-specific first, then general
        return panelist_questions + general_questions
    elif topic:
        return [
            f"What do panelists think of {topic.lower()}?",
            f"What are different perspectives on {topic.lower()}?",
            f"Which panelists have strong views on {topic.lower()}?",
            f"How do Labor and Liberal differ on {topic.lower()}?",
            f"What are the most controversial views on {topic.lower()}?",
            f"How have panelist views on {topic.lower()} evolved?"
        ]
    else:
        return [
            "What do panelists think of climate change?",
            "How do panelists view immigration policy?", 
            "What are different perspectives on the economy?",
            "Which panelists had the most controversial views?",
            "What are the most controversial political debates?",
            "How have political views changed over the years?",
            "What are the biggest political divisions in Australia?"            
        ]


def format_selection_display(panelist: str = "", topic: str = "", 
                           panelist_lookup: dict = None) -> str:
    """Format current selection display with clickable panelist profiles and dates."""
    if not panelist and not topic:
        return "**Current Focus:** None selected"
    
    parts = []
    
    if panelist and panelist_lookup:
        # Find matching panelist (case-insensitive)
        matching_key = None
        for key in panelist_lookup.keys():
            if key.upper() == panelist.upper():
                matching_key = key
                break
        
        if matching_key:
            lookup_data = panelist_lookup[matching_key]
            
            # Handle both 2-tuple (profession, url) and 3-tuple (profession, url, date)
            if len(lookup_data) == 3:
                profession, url, latest_date = lookup_data
                profession_text = profession if profession and str(profession) != 'nan' else 'Panelist'
                if latest_date and str(latest_date) != 'nan' and latest_date.strip():
                    profession_with_date = f"{profession_text}, {latest_date}"
                else:
                    profession_with_date = profession_text
            else:
                profession, url = lookup_data
                profession_with_date = profession if profession and str(profession) != 'nan' else 'Panelist'
            
            if url and str(url) != 'nan':
                panelist_part = f"👤 [{matching_key}]({url}) *({profession_with_date})*"
            else:
                panelist_part = f"👤 {matching_key} *({profession_with_date})*"
        else:
            panelist_part = f"👤 {panelist}"
        parts.append(panelist_part)
    elif panelist:
        parts.append(f"👤 {panelist}")
    
    if topic:
        parts.append(f"🎯 {topic}")
    
    return "**Current Focus:** " + " + ".join(parts)



def handle_question(question: str, k_value: int, style: str, 
                   helpers, qa_chain, config) -> Tuple[str, str, str]:
    """
    Handle user question and return response.
    
    Args:
        question: User's question
        k_value: Number of documents to retrieve
        style: Response style (Concise/Standard/Detailed)
        helpers: QAHelpers object
        qa_chain: QA chain
        config: System configuration
        
    Returns:
        Tuple of (answer, sources, status)
    """
    if not question.strip():
        return "Please enter a question.", "", "⚠️ No question provided"
    
    print(f"Processing: {question[:50]}...")
    
    try:
        result = process_question_with_style(
            helpers=helpers,
            qa_chain=qa_chain, 
            query=question,
            k=k_value,
            style=style,
            config=config
        )
        
        # result = (formatted_answer, sources, status, pdf_output, tech_info)
        return result[0], result[1], result[2]
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ Error in handler: {error_msg}")
        return error_msg, "", f"❌ {error_msg}"


def update_selections(panelist: str, topic: str, panelist_lookup: dict) -> Tuple:
    """
    Update UI selections and generate new questions.
    
    Args:
        panelist: Selected panelist
        topic: Selected topic  
        panelist_lookup: Panelist profile data
        
    Returns:
        Tuple of UI updates
    """
    questions = generate_smart_questions(panelist, topic)
    display = format_selection_display(panelist, topic, panelist_lookup)
    selected = questions[0] if (panelist or topic) else None
    status = f"Generated {len(questions)} questions" if (panelist or topic) else "Ready"
    
    return (
        display, 
        gr.update(choices=questions, value=selected), 
        selected or "", 
        status
    )

def create_episode_scroller(helpers):
    """Create auto-scrolling episode display with real data"""
    try:
        # Convert date to datetime for proper sorting
        df_episodes = helpers.df_ep.copy()
        df_episodes['date'] = pd.to_datetime(df_episodes['date'])
        
        # Get recent episodes - now properly sorted
        episodes_data = df_episodes.sort_values('date', ascending=False).head(25)
        
        episode_html = ""
        episode_count = 0
        
        for _, episode in episodes_data.iterrows():
            if pd.notna(episode['date']) and pd.notna(episode['title']):
                # Format date back to string for display
                date = episode['date'].strftime('%Y-%m-%d')
                title = episode['title']
                episode_html += f'{date}: "{title}"<br>'
                episode_count += 1
        
        # Duplicate content for smooth continuous scroll
        episode_html = episode_html + episode_html
        
        print(f"✅ Successfully loaded {episode_count} real episodes for scroller")
        
        if episode_count == 0:
            raise Exception("No episodes found after processing")
            
    except Exception as e:
        print(f"❌ Error loading episodes: {e}")
        print("📝 Using sample episodes instead")
        # Now you'll know it's using fallback
        episode_html = """
        2024-11-25: "Conflict, Quotas and Calling Out Racism"<br>
        2024-11-18: "Trump's Return and Australia's Response"<br>
        2024-11-11: "Climate Action After COP29"<br>
        """ * 8
    
    return gr.HTML(f"""
    <div style="margin: 10px 0; text-align: center;">
        <div style="max-width: 500px; margin: 0 auto; height: 80px; overflow: hidden; 
                    border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; 
                    background: #f9fafb;">
            <div style="font-family: 'Georgia', 'Times New Roman', serif; 
                        font-size: 0.9em; line-height: 1.5; color: #4b5563; 
                        text-align: center; animation: scroll-episodes 50s linear infinite;">
                {episode_html}
            </div>
        </div>
    </div>

    <style>
    @keyframes scroll-episodes {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(-50%); }}
    }}
    </style>
    """)

def get_panelist_episodes(helpers, panelist_name: str) -> str:
    """
    Get episodes for selected panelist in formatted display.
    
    Args:
        helpers: QAHelpers object
        panelist_name: Name of panelist
        
    Returns:
        Formatted episode list
    """
    if not panelist_name:
        return "*Select a panelist to see their episodes*"
    
    try:
        episodes = helpers.df_reply[
            (helpers.df_reply["speaker_name"] == panelist_name) & 
            (helpers.df_reply["speaker_type"] == 3)
        ].merge(helpers.df_ep, left_on="episode_id", right_on="id")["ep_label"].unique()
        
        if len(episodes) == 0:
            return f"*No episodes found for {panelist_name}*"
        
        # Sort and format
        sorted_episodes = sorted(episodes, reverse=True)
        header = f"**{panelist_name} appeared in {len(episodes)} episodes:**\n\n"
        episode_list = "\n".join([f"• {ep}" for ep in sorted_episodes])
        
        return header + episode_list
    except Exception as e:
        return f"*Error loading episodes: {str(e)}*"
        
def create_event_handlers(helpers, qa_chain, config, embedder):
    """
    Create event handler functions with proper closures.
    
    Args:
        helpers: QAHelpers object
        qa_chain: QA chain
        config: System configuration  
        embedder: SentenceTransformer model
        
    Returns:
        Dict of event handler functions
    """
    panelist_lookup = helpers.panelist_lookup
    
    def on_panelist_change(panelist_display, topic):
        """Handle panelist selection change - FAST version."""
        clean_panelist = extract_panelist_name(panelist_display)
        episodes_text = get_panelist_episodes(helpers, clean_panelist)
        
        if clean_panelist:
            # FAST: Always use popular topics (no semantic matching)
            topic_label_text = f"**Popular Topics**"
            topic_choices = POPULAR_TOPICS
            
            # Show semantic button for this panelist
            semantic_btn_visible = True
            semantic_btn_text = f"🧠 Show {clean_panelist}'s Topics"
            
            # Extract latest date from existing episode data
            try:
                episodes_data = helpers.df_reply[
                    (helpers.df_reply["speaker_name"] == clean_panelist) & 
                    (helpers.df_reply["speaker_type"] == 3)
                ][['episode_id', 'speaker_name', 'speaker_type']].merge(
                    helpers.df_ep[['id', 'date', 'title', 'url', 'ep_label']], 
                    left_on="episode_id", 
                    right_on="id"
                )
                
                if not episodes_data.empty:
                    latest_date = episodes_data["date"].max()
                    # Create temporary lookup with date for display
                    matching_key = None
                    for key in panelist_lookup.keys():
                        if key.upper() == clean_panelist.upper():
                            matching_key = key
                            break
                    
                    if matching_key:
                        profession, url = panelist_lookup[matching_key]
                        temp_lookup = {clean_panelist: (profession, url, latest_date)}
                    else:
                        temp_lookup = {clean_panelist: ("Panelist", None, latest_date)}
            except Exception as e:
                temp_lookup = panelist_lookup
        else:
            topic_label_text = "**Popular Topics**"
            topic_choices = POPULAR_TOPICS
            semantic_btn_visible = False
            semantic_btn_text = "🧠 Show Personalized Topics"
            temp_lookup = panelist_lookup
        
        # Use temp_lookup for this specific selection
        selection_results = update_selections(clean_panelist, topic, temp_lookup)
        
        return (
            clean_panelist,                                    # current_panelist (State)
            episodes_text,                                     # episodes_display (Textbox)  
            topic_label_text,                                  # topic_label (Markdown)
            gr.update(choices=topic_choices, value=None),      # topic_radio (Radio)
            gr.update(visible=semantic_btn_visible, value=semantic_btn_text),  # semantic_btn (Button)
            selection_results[0],                              # current_selection (Markdown)
            selection_results[1],                              # sample_questions (Radio) 
            selection_results[2],                              # question (Textbox)
            selection_results[3]                               # status_display (Textbox)
        )

    def on_semantic_click(panelist):
        """SLOW but smart - only runs when user clicks button."""
        if not panelist:
            return gr.update(), gr.update(), gr.update()
        
        # NOW do the heavy computation
        relevant_topics = get_semantic_topic_matches(helpers, panelist, embedder)
        topic_label_text = f"**{panelist}'s Topics** ({len(relevant_topics)} most relevant)"
        
        return (
            topic_label_text,                                  # topic_label
            gr.update(choices=relevant_topics, value=None),    # topic_radio
            gr.update(visible=False)                           # hide button after use
        )
                
    def on_topic_click(topic_name, panelist):
        """Handle topic selection."""
        return (topic_name,) + update_selections(panelist, topic_name, panelist_lookup)
    
    def clear_all():
        """Clear all selections."""
        return (
            "",  # current_panelist
            "*Select a panelist to see their episodes*",  # episodes_display
            "",  # current_topic
            "**Current Focus:** None selected",  # current_selection
            gr.update(choices=POPULAR_TOPICS, value=None),  # topic_radio
            gr.update(choices=generate_smart_questions(), value=None),  # sample_questions
            "",  # question
            "Cleared"  # status_display
        )

    def clear_question_only():
        """Clear only the question field."""
        return ""
        
    def ask_question(q, k, s):
        if not q.strip():
            return "**Please enter a question**", "", "⚠️ No question provided", gr.update()
        
        try:
            # Update status immediately, then process
            gr.Info("🔄 Processing your question...")  # This shows immediately
            result = handle_question(q, k, s, helpers, qa_chain, config)
            return result[0], result[1], gr.update(selected=2)
        except Exception as e:
            return f"Error: {str(e)}", "", f"❌ Error: {str(e)}", gr.update()
    
    return {
        'on_panelist_change': on_panelist_change,
        'on_semantic_click': on_semantic_click,  # ← ADDED THIS
        'on_topic_click': on_topic_click,
        'clear_all': clear_all,
        'clear_question_only': clear_question_only,
        'ask_question': ask_question
    }

def wire_ui_events(components: dict, handlers: dict):
    """
    Wire up all UI events using provided components and handlers.
    
    Args:
        components: Dict of Gradio components
        handlers: Dict of event handler functions
    """
    # Unpack components
    panelist_dropdown = components['panelist_dropdown']
    topic_radio = components['topic_radio']
    topic_label = components['topic_label']
    semantic_btn = components['semantic_btn']  
    sample_questions = components['sample_questions']
    question = components['question']
    ask_btn = components['ask_btn']
    clear_btn = components['clear_btn']
    back_btn = components['back_btn']
    clear_question_btn = components['clear_question_btn']
    current_panelist = components['current_panelist']
    current_topic = components['current_topic']
    current_selection = components['current_selection']
    #status_display = components['status_display']
    answer_display = components['answer_display']
    sources_display = components['sources_display']
    tabs = components['tabs']
    k_slider = components['k_slider']
    style_radio = components['style_radio']
    episodes_display = components['episodes_display']
    
    # Wire events
    panelist_dropdown.change(
        fn=handlers['on_panelist_change'],
        inputs=[panelist_dropdown, current_topic],
        outputs=[current_panelist, episodes_display, topic_label, topic_radio, 
                semantic_btn, current_selection, sample_questions, question]
    )

    semantic_btn.click(
        fn=handlers['on_semantic_click'],
        inputs=[current_panelist],
        outputs=[topic_label, topic_radio, semantic_btn]
    )

    topic_radio.change(
        fn=handlers['on_topic_click'],
        inputs=[topic_radio, current_panelist],
        outputs=[current_topic, current_selection, sample_questions, question]
    )
    
    sample_questions.change(
        lambda q: q or "", 
        [sample_questions], 
        [question]
    )
    
    clear_question_btn.click(
        handlers['clear_question_only'], 
        outputs=[question]
    )
    
    clear_btn.click(
        handlers['clear_all'], 
        outputs=[current_panelist, episodes_display, current_topic, current_selection, 
                topic_radio, sample_questions, question]
    )
    
    ask_btn.click(
        handlers['ask_question'], 
        [question, k_slider, style_radio], 
        [answer_display, sources_display, tabs]
    )
    
    back_btn.click(lambda: gr.update(selected=1), outputs=[tabs])  


def create_semantic_ui(helpers, qa_chain, config) -> gr.Blocks:
    """
    Create the semantic discovery UI with clean component organization.
    
    Args:
        helpers: QAHelpers object with attached data
        qa_chain: QA chain
        config: System configuration
        
    Returns:
        Gradio Blocks demo
    """
    # Initialize embedder
    embedder = SentenceTransformer(config.embedding_model_name)
    
    # Get panelist data
    panelist_names = enhanced_build_panelist_list(helpers)
    
    bg_b64 = get_background_image_base64()
    print(f"Background image loaded: {bg_b64 is not None}")

    background_css = ""
    if bg_b64:
        background_css = f"""
        /* Header background on all pages */
        .gradio-container > div:first-child {{
            background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)),
                        url('data:image/jpeg;base64,{bg_b64}') !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-position: center top !important;
            min-height: 200px;
        }}

        /* Full background only on Response tab */
        .tab-nav button[aria-selected="true"][id*="Response"] ~ .tabitem {{
            background: linear-gradient(rgba(255,255,255,0.93), rgba(255,255,255,0.93)),
                        url('data:image/jpeg;base64,{bg_b64}') !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
        }}
        #clear-btn-inside {{
            position: absolute !important;
            top: 8px !important;
            right: 8px !important;
            width: 24px !important;
            height: 24px !important;
            min-width: 24px !important;
            padding: 0 !important;
            font-size: 14px !important;
            opacity: 0.6 !important;
            z-index: 10 !important;
            border-radius: 50% !important;
            border: 1px solid #ccc !important;
        }}
        .horizontal-radio .gr-radio-group {{
            display: flex !important;
            flex-direction: row !important;
            gap: 10px !important;
        }}
        .horizontal-radio .gr-radio-group label {{
            margin-right: 15px !important;
        }}
        """

    with gr.Blocks(
        title="Q+A Voices: A Nation in Question", 
        #theme=modern_theme,
        theme=get_gradio_theme(config.ui_theme),
        css=background_css  
    ) as demo:
        logo_b64 = get_logo_base64()

        if logo_b64:
            logo_html = f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{logo_b64}" 
                    style="width: 88px; height: 69px; margin-right: 15px; object-fit: contain;" 
                    alt="Q+A Voices Logo">
                <h1 style="margin: 0; font-size: 2em; font-weight: bold;">Q+A Voices: A Nation in Question</h1>
            </div>
            """
        else:
            # Fallback without logo
            logo_html = """
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="width: 88px; height: 69px; background: #722F37; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-right: 15px; color: #D4AF37; font-weight: bold; font-size: 14px;">Q+A</div>
                <h1 style="margin: 0; font-size: 2em; font-weight: bold;">Q+A Voices: A Nation in Question</h1>
            </div>
            """
        gr.HTML(logo_html)
        #gr.Markdown("# 🧠 **Q+A Voices: A Nation in Question**")
 
        with gr.Tabs() as tabs:
            with gr.Tab("👋 Welcome", id=0):
                with gr.Column():
                    # Constrain width and reduce spacing
                    gr.HTML('<div style="max-width: 750px; margin: 0 auto;">')
                    
                    # Simple, clean hero - no banner
                    #gr.Markdown("## What have Australians been debating for the past decade?")
                    gr.HTML('<h2 style="text-align: center;">What have Australians been debating for the past decade?</h2>')
                    # Compact timeline integrated into content
                    create_episode_scroller(helpers)
                    # Main content - tighter spacing
                    gr.Markdown("""
            Q+A Voices draws from over ten years of <a href="https://www.abc.net.au/qanda" target="_blank">ABC's Q+A</a> program transcripts. For those unfamiliar, Q+A brings together politicians, public figures, and community members each week for unscripted political discussion. The format encourages genuine, in-depth responses and often leads to revealing moments of candour and passionate debate. 
                                
            This archive captures those exchanges - the spontaneous answers, the challenging follow-ups, and the diverse perspectives that emerge when Australians grapple with the issues that matter.

            **Now, with AI, we can explore it all.**

            <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 3px solid #8b5cf6;">

            **🕰️ Journey Through Time** • Ask questions across any topic or timeframe

            **🎤 Follow the Voices** • See what specific panellists discussed or how themes emerged  

            **💡 Uncover Key Moments** • Surface intriguing segments from a vast archive of conversations

            **🔍 Spark Your Curiosity** • Discover how public discourse has shifted and why

            </div>

            **👥 Who's It For?** Anyone with a curious mind! Political analysts, media researchers, students, journalists, or if you're just keen to revisit pivotal moments in Australian debate.

            **💫 Why It Matters:** This tool was born from a passion for Australian public discourse and a fascination with how AI can help us understand it better. Q+A Voices aims to make these important conversations accessible and open for your own reflection and discovery.
                    """)
                    
                    # Compact expandable sections in a row
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Accordion("🔧 Tech Details", open=False):
                                gr.Markdown("""
            Built with OpenAI LLMs, custom RAG pipeline, vector store of Q+A transcripts, and Gradio interface for interactive exploration.
                                """)
                        with gr.Column(scale=1):
                            with gr.Accordion("👩‍💻 Who Built It", open=False):
                                gr.Markdown("""
            Created by **Susan**, a data scientist passionate about Australian politics. She developed this tool to reveal trends, perspectives, and potential biases in over a decade of *Q+A* episodes.
                                """)
                    
                    # Call to action - reduced spacing
                    gr.HTML('<div style="margin: 25px 0 10px 0;">')
                    start_exploring_btn = PrimaryButton("🚀 Begin Your Exploration", size="lg")
                    gr.HTML('</div>')
                    
                    gr.HTML('</div>')  # Close width constraint

                    # Add styling
                    gr.HTML("""
                    <style>
                    .gr-column > * {
                        margin-bottom: 0.5em !important;
                    }
                    </style>
                    """)

            # Ask Question Tab
            with gr.Tab("🔍 Ask Question", id=1):
                with gr.Row():
                    # LEFT COLUMN
                    with gr.Column(scale=35):
                        gr.Markdown("### 👤 Panelist")
                        panelist_dropdown = gr.Dropdown(
                            choices=[""] + panelist_names, 
                            value="", 
                            filterable=True, 
                            label="👤 Panelist",
                            info="Search by name (sorted by episode frequency)"
                        )
                        episodes_display = gr.Textbox(
                            value="*Select a panelist to see their episodes*", 
                            label="📅 All Episode Appearances",
                            lines=6,
                            max_lines=6,
                            interactive=False,
                            elem_id="episodes-display"
                        )
                        
                        with gr.Column() as topics_section:
                            topic_label = gr.Markdown("**Popular Topics**")
                            topic_radio = gr.Radio(
                                choices=POPULAR_TOPICS,
                                interactive=True,
                                label=""
                            )
                            # NEW: Optional semantic button
                            semantic_btn = gr.Button(
                                "🧠 Show Personalized Topics", 
                                visible=False,  # Hidden until panelist selected
                                variant="secondary",
                                size="sm"
                            )
                        
                        with gr.Row():
                            k_slider = gr.Slider(5, 150, 80, step=5, label="Docs")
                            style_radio = gr.Radio(
                                [("Short", "Concise"), ("Mid", "Standard"), ("Long", "Detailed")], 
                                value="Standard", 
                                label="Length",  # or "Detail Level"
                                elem_classes=["horizontal-radio"]
                            )     
                    # RIGHT COLUMN
                    with gr.Column(scale=65):
                        current_selection = gr.Markdown("**Current Selection:** None")
                        gr.Markdown("### 🚀 Your Question")
                        gr.Markdown("*Ask anything about Australian politics - from economy to immigration, from party leaders to policy debates.*")

                        with gr.Row():
                            with gr.Column(scale=1, elem_id="question-container"):
                                question = gr.Textbox(
                                    "",
                                    placeholder="Say something...",
                                    lines=4,
                                    label="",  # ← Remove the label completely
                                    elem_id="question-input"
                                )
                                clear_question_btn = SecondaryButton(
                                    "✕",
                                    size="sm",
                                    elem_id="clear-btn-inside"
                                )
                                                
                        with gr.Row():
                            ask_btn = PrimaryButton("🔍 Ask Question", scale=3)
                            clear_btn = SecondaryButton("🗑️ Clear All", scale=1)

                        #tatus_display = gr.Textbox("Ready", label="Status", interactive=False)                        

                        gr.Markdown("### 💡 Sample Questions")
                        sample_questions = gr.Radio(
                            choices=generate_smart_questions(), 
                            interactive=True, 
                            label=""
                        )
                        
            # Response Tab
            with gr.Tab("📝 Response", id=2):
                gr.Markdown("### 📝 Answer")
                answer_display = gr.Markdown("**Click 'Ask Question' to see response**")
                gr.Markdown("### 📚 Sources")
                sources_display = gr.Markdown("*Sources will appear here*")
                back_btn = SecondaryButton("← Back")
        
        # State management
        current_panelist = gr.State("")
        current_topic = gr.State("")
        
        # Create components dict for event wiring
        components = {
            'panelist_dropdown': panelist_dropdown,
            'topic_radio': topic_radio,
            'topic_label': topic_label,
            'semantic_btn': semantic_btn, 
            'sample_questions': sample_questions,
            'question': question,
            'ask_btn': ask_btn,
            'clear_btn': clear_btn,
            'back_btn': back_btn,
            'clear_question_btn': clear_question_btn,
            'current_panelist': current_panelist,
            'current_topic': current_topic,
            'current_selection': current_selection,
            #'status_display': status_display,
            'answer_display': answer_display,
            'sources_display': sources_display,
            'tabs': tabs,
            'k_slider': k_slider,
            'style_radio': style_radio,
            'episodes_display': episodes_display
        }
        
        # Create event handlers and wire up
        start_exploring_btn.click(lambda: gr.update(selected=1), outputs=[tabs])
        handlers = create_event_handlers(helpers, qa_chain, config, embedder)
        wire_ui_events(components, handlers)
    
    return demo


def create_current_ui(helpers, qa_chain, config) -> gr.Blocks:
    """
    Create the current working UI - preserved as fallback.
    
    Args:
        helpers: QAHelpers object
        qa_chain: QA chain  
        config: System configuration
        
    Returns:
        Gradio Blocks demo
    """
    with gr.Blocks(
        title="Q&A System V2 - Current UI",
        #theme=modern_theme,
        theme=get_gradio_theme(config.ui_theme),
        css=background_css
    ) as demo:
        
        gr.Markdown("# 🧠 Q&A System V2 - Current UI")
        gr.Markdown("Current working interface with episode/panelist/topic filtering.")
        
        with gr.Row():
            # Left column - Filtering
            with gr.Column(scale=1):
                gr.Markdown("### 1️⃣ Select Content")
                
                episode_dropdown = gr.Dropdown(
                    label="Episode",
                    choices=sorted(helpers.episode_lookup.keys()),
                    value=sorted(helpers.episode_lookup.keys())[0],
                    interactive=True,
                )
                
                default_episode = sorted(helpers.episode_lookup.keys())[0]
                gr.Markdown("**Filter by:** *(based on selected episode)*")

                with gr.Row():
                    with gr.Column():
                        panellist_radio = gr.Radio(
                            label="Panellist (in this episode)", 
                            choices=helpers.get_panellists_by_episode(default_episode),
                            interactive=True
                        )
                    with gr.Column():
                        subtopic_radio = gr.Radio(
                            label="Topic (in this episode)", 
                            choices=helpers.get_subtopics_by_episode(default_episode),
                            interactive=True
                        )
            
            # Right column - Question input
            with gr.Column(scale=2):
                # Sample questions
                sample_questions = gr.Radio(
                    label="Sample Questions (click to select)",
                    choices=[
                        "What did panelists say about climate change?",
                        "How do panelists view immigration policy?", 
                        "What are different perspectives on the economy?",
                    ],
                    interactive=True,
                    elem_id="sample-questions"
                )   
                
                # Question input with clear button
                with gr.Row():
                    with gr.Column(scale=1, elem_id="question-container"):
                        question = gr.Textbox(
                            label="",
                            placeholder="e.g., What did panelists say about climate change?",
                            lines=4,
                            elem_id="question-input"
                        )
                        clear_question_btn = SecondaryButton(
                            "✕", 
                            size="sm",
                            elem_id="clear-btn-inside"
                        )
                
                # Controls
                with gr.Row():
                    k_slider = gr.Slider(
                        minimum=5,
                        maximum=50, 
                        value=15,
                        step=5,
                        label="Documents to retrieve (k)"
                    )
                    
                    style_radio = gr.Radio(
                        label="Response Style",
                        choices=["Concise", "Standard", "Detailed"],
                        value="Standard"
                    )
                
                # Buttons
                with gr.Row():
                    submit_btn = PrimaryButton(
                        "🔍 Ask Question", 
                        interactive=False
                    )   
                    clear_btn = SecondaryButton("🗑️ Clear")
            
            with gr.Column(scale=1):
                # Status
                gr.Markdown("### System Status")
                status_display = gr.Textbox(
                    label="Status",
                    value="Ready to test!",
                    interactive=False
                )
                
                # Config info
                gr.Markdown(f"""
                **Configuration:**
                - Model: {config.chat_model_name}
                - Temperature: {config.temperature}
                - Debug: {config.debug_enabled}
                """)
        
        # Results
        gr.Markdown("### 📝 Response")
        answer_display = gr.Markdown(
            value="*Ask a question to see the response here.*"
        )
        
        gr.Markdown("### 📚 Sources") 
        sources_display = gr.Markdown(
            value="*Sources will appear here.*"
        )
        
        # Helper functions for this UI
        def set_sample_question(selected_question):
            return selected_question if selected_question else ""
        
        def clear_inputs():
            return "", "*Ask a question to see the response here.*", "Cleared - ready for next question"
        
        def update_panellists(ep_label):
            new_panelists = helpers.get_panellists_by_episode(ep_label)
            return gr.update(choices=new_panelists, value=None)

        def update_subtopics(ep_label):
            new_subtopics = helpers.get_subtopics_by_episode(ep_label)
            return gr.update(choices=new_subtopics, value=None)

        def filter_subtopics_by_panellist(panellist_name, ep_label):
            if panellist_name is None:
                return gr.update()
            new_subtopics = helpers.get_subtopics_by_panellist(ep_label, panellist_name)
            return gr.update(choices=new_subtopics, value=None)

        def clear_question():
            return "", gr.update(interactive=False)

        def update_submit_button(question_text):
            has_content = bool(question_text.strip())
            return gr.update(interactive=has_content)
        
        def update_sample_questions(panelist, topic):
            return gr.update(choices=generate_smart_questions(panelist, topic))
        
        def handle_submit(q, k, s):
            return handle_question(q, k, s, helpers, qa_chain, config)
        
        # Wire up events
        episode_dropdown.change(
            fn=update_panellists,
            inputs=episode_dropdown,
            outputs=panellist_radio,
        )
        episode_dropdown.change(
            fn=update_subtopics,
            inputs=episode_dropdown,
            outputs=subtopic_radio,
        )
        panellist_radio.change(
            fn=filter_subtopics_by_panellist,
            inputs=[panellist_radio, episode_dropdown],
            outputs=subtopic_radio,
        )
        sample_questions.change(
            fn=set_sample_question,
            inputs=[sample_questions],
            outputs=[question]
        )
        panellist_radio.change(
            fn=update_sample_questions,
            inputs=[panellist_radio, subtopic_radio],
            outputs=sample_questions
        )
        subtopic_radio.change(
            fn=update_sample_questions,
            inputs=[panellist_radio, subtopic_radio], 
            outputs=sample_questions
        )
        submit_btn.click(
            fn=handle_submit,
            inputs=[question, k_slider, style_radio],
            outputs=[answer_display, sources_display, status_display]
        )
        clear_btn.click(
            fn=clear_inputs,
            inputs=[],
            outputs=[question, answer_display, status_display]
        )
        clear_question_btn.click(
            fn=clear_question,
            inputs=[],
            outputs=[question, submit_btn]
        )
        question.change(
            fn=update_submit_button,
            inputs=[question],
            outputs=[submit_btn]
        )
    
    return demo


def launch_ui_with_toggle(helpers, qa_chain, config, design: str = "current") -> gr.Blocks:
    """
    Main launcher with design selection and data preparation.
    
    Args:
        helpers: QAHelpers object
        qa_chain: QA chain
        config: System configuration
        design: "current" or "new"
        
    Returns:
        Gradio demo ready to launch
    """
    print(f"🎨 Creating {design} UI...")
    
    # Prepare all necessary data
    ui_data = prepare_ui_data(helpers, config)
    print(f"✅ UI data prepared: {len(ui_data['panelist_list'])} panelists loaded")
    
    # Ensure helpers has the required attributes
    helpers.panelist_lookup = ui_data['panelist_lookup']
    helpers.con = ui_data['con']
    
    if design == "new":
        demo = create_semantic_ui(helpers, qa_chain, config)  
        print("✅ New semantic UI created")
    else:
        demo = create_current_ui(helpers, qa_chain, config)
        print("✅ Current UI created")
    
    return demo
