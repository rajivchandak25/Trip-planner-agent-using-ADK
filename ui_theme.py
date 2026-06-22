# ui_theme.py
# ───────────
# Premium CSS stylesheet injection block for Streamlit.

CSS_BLOCK = """
<style>
/* Base Theme Overrides */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b0e17;
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
}

/* Background Glowing Accents */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: absolute;
    top: -200px;
    right: -100px;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stAppViewContainer"]::after {
    content: "";
    position: absolute;
    bottom: -200px;
    left: -200px;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
}

/* Header & Wordmark */
h1 {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
}

.gradient-text {
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #fb7185 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.page-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
    margin-top: -10px;
    margin-bottom: 25px;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: rgba(15, 23, 42, 0.7);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
}

.sidebar-wordmark {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 20px;
    text-align: center;
}

.sidebar-section-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.08em;
    margin-top: 15px;
    margin-bottom: 10px;
    text-transform: uppercase;
}

/* Cards & Containers (Glassmorphism) */
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div {
    /* Target widgets wrapper */
}

/* Chat Input Bar */
[data-testid="stChatInput"] {
    border-radius: 12px;
    background-color: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 1px #6366f1 !important;
}

/* Log / Thought Trace Blocks */
.thought-log-container {
    background-color: #0f172a;
    border-left: 3px solid #818cf8;
    border-radius: 4px;
    padding: 10px 14px;
    margin-bottom: 15px;
}

.thought-log-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.thought-log-content {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.85rem;
    color: #cbd5e1;
    line-height: 1.4;
    white-space: pre-wrap;
}

.thought-badge {
    background-color: rgba(129, 140, 248, 0.15);
    color: #818cf8;
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
}

.tool-badge {
    background-color: rgba(234, 179, 8, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(234, 179, 8, 0.3);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
}

/* Custom Dividers */
hr {
    border-color: rgba(255, 255, 255, 0.08) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}
</style>
"""
