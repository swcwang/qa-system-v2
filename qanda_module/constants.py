"""
Constants and configuration data for the Q&A UI system.
"""

# Popular topics for general exploration (always visible)
POPULAR_TOPICS = [
    "Climate Change", "Economy", "Healthcare", "Education", "Housing", 
    "Immigration", "Energy", "Defence", "Employment", "Tax", 
    "Environment", "Trade"
]

# Complete list of substantive topics for semantic matching
ALL_SUBSTANTIVE_TOPICS = [
    "Climate Change", "Economy", "Healthcare", "Education", "Housing", "Immigration", 
    "Energy", "Defence", "Transport", "Tax", "Welfare", "Mining", "Agriculture",
    "Technology", "Media", "Arts", "Indigenous", "Mental Health", "Aged Care",
    "Childcare", "Employment", "Industrial Relations", "Trade", "Foreign Policy",
    "Security", "Environment", "Water", "Regional Development", "Infrastructure",
    "Small Business", "Innovation", "Tourism", "Disability", "Youth", "Women",
    "Multiculturalism", "Refugees", "Border Protection", "Asylum Seekers", "Coal"
]

# Add this to the end of constants.py
SPEAKER_NAME_FIXES = {
    # Exact matches from analysis
    'MARK COLERIDGE': 'Archbishop Mark Coleridge',
    'PJ O\'ROURKE': 'P.J. O\'Rourke', 
    'SANDY GUTMAN': 'Sandy Gutman aka Austen Tayshus',
    'GEORGE PELL': 'Cardinal George Pell',
    'SUSAN GREENFIELD': 'Baroness Susan Greenfield',
    'JORDAN PETERSON': 'Dr Jordan Peterson',
    'CHRISOPHER PYNE': 'Christopher Pyne',  # Typo fix
    'CORNEL WEST': 'Dr Cornel West',
    'CINDY PAN': 'Dr Cindy Pan',
    'FUZZY AGOLLEY': 'Faustina \'Fuzzy\' Agolley',
    'FELICITY HAMPEL': 'Judge Felicity Hampel',
    # Add more manually as you find them...
}

# CSS styles for the Gradio interface
UI_CSS = """
.topic-chip{margin:2px!important;padding:4px 8px!important;border-radius:12px!important;background:#f8fafc!important;border:1px solid #e2e8f0!important;transition:all 0.2s!important}
.topic-chip:hover{background:#2563eb!important;color:white!important}
#question-container{position:relative!important}
#clear-btn-inside{position:absolute!important;top:32px!important;right:8px!important;width:20px!important;height:20px!important;min-width:20px!important;padding:0!important;font-size:12px!important;opacity:0.5!important;z-index:10!important;border-radius:50%!important}
#clear-btn-inside:hover{opacity:0.8!important}
.topic-radio{max-height:280px!important;overflow-y:auto!important;border:1px solid #e5e7eb!important;border-radius:8px!important;padding:12px!important;background:#fafafa!important}
.topic-radio label{padding:4px 8px!important;margin:2px 0!important;border-radius:4px!important}
.topic-radio label:hover{background:#f0f0f0!important}
"""

# Legacy UI CSS (for current UI)
LEGACY_UI_CSS = """
.gr-radio-group {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px;
    background: #fafafa;
}
.gr-radio-group label {
    padding: 4px 8px !important;
    margin: 2px 0 !important;
    border-radius: 4px;
}
.gr-radio-group label:hover {
    background: #f0f0f0;
}
#sample-questions {
    max-height: 200px !important;
    overflow-y: auto !important;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 8px;
}
#question-container {
    position: relative !important;
}
#clear-btn-inside {
    position: absolute !important;
    top: 32px !important;
    right: 8px !important;
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
    padding: 0 !important;
    font-size: 12px !important;
    opacity: 0.5 !important;
    z-index: 10 !important;
    border-radius: 50% !important;
}
#clear-btn-inside:hover {
    opacity: 0.8 !important;
}
"""
