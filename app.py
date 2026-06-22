# app.py
# ──────
# Main Streamlit entrypoint for the ADK Trip Planner Agent application.

import os
import asyncio
import streamlit as st
from dotenv import load_dotenv

# Load env variables if .env exists
load_dotenv()

# Set up Vertex AI/Gemini configuration before importing ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# --- Streamlit Page Setup ---
st.set_page_config(
    page_title="ADK Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import local stylesheet and agents factory after page config
from ui_theme import CSS_BLOCK
st.markdown(CSS_BLOCK, unsafe_allow_html=True)

from agents import get_agent_by_mode, InMemorySessionService, Runner, Content, Part

# --- Session State Initialization ---
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Helper: Async Session Service Manager ---
def get_or_create_session(agent_name: str):
    """Retrieves or creates a session for the active agent, resetting history on swap."""
    if ("adk_session" not in st.session_state or 
            st.session_state.get("adk_session_agent") != agent_name):
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        session = loop.run_until_complete(
            st.session_state.session_service.create_session(
                app_name=agent_name,
                user_id="streamlit_adventurer"
            )
        )
        st.session_state.adk_session = session
        st.session_state.adk_session_agent = agent_name
        st.session_state.chat_history = []  # Clear history for new agent session
        
    return st.session_state.adk_session

# --- Sidebar Control Panel ---
with st.sidebar:
    st.markdown('<div class="sidebar-wordmark">Trip Planner</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section-label">AUTHENTICATION</div>', unsafe_allow_html=True)
    # Check for GEMINI_API_KEY in environment
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not env_api_key:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="Paste your API key here",
            help="Create a key at Google AI Studio: https://aistudio.google.com/app/apikey"
        ).strip()
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            st.session_state.api_key_configured = True
        else:
            st.session_state.api_key_configured = False
    else:
        os.environ["GEMINI_API_KEY"] = env_api_key
        st.session_state.api_key_configured = True
        st.success("API key loaded from system env.")

    st.markdown("---")
    st.markdown('<div class="sidebar-section-label">AGENT CONFIGURE</div>', unsafe_allow_html=True)
    
    mode = st.selectbox(
        "Select Planner Mode",
        [
            "🧞 Day Trip Genie",
            "🌦️ Weather-Aware Planner",
            "🧠 Adaptive Multi-Day Planner",
            "🏢 Specialist Orchestrator"
        ],
        help="Select which specialized RAG agent will plan your trip."
    )
    
    model = st.selectbox(
        "Gemini Model",
        ["gemini-2.5-flash", "gemini-2.5-pro"],
        help="Choose the model. Flash is fast, Pro is highly analytical."
    )
    
    if st.button("Reset Conversation", use_container_width=True):
        if "adk_session_agent" in st.session_state:
            del st.session_state.adk_session
            del st.session_state.adk_session_agent
        st.session_state.chat_history = []
        st.success("Conversation cleared.")
        st.rerun()

# --- Main Page Header ---
st.markdown('# Travel Planner <span class="gradient-text">Agent Suite</span>', unsafe_allow_html=True)
st.markdown(f'<div class="page-subtitle">Multi-Agent RAG execution using Google\'s Agent Development Kit (ADK) — Running <b>{mode}</b></div>', unsafe_allow_html=True)

# Guard: Ensure API key is configured
if not st.session_state.get("api_key_configured", False):
    st.info("⚠️ Please enter a Google Gemini API Key in the sidebar to start planning.")
    st.stop()

# Load agent and session
agent = get_agent_by_mode(mode)
# Inject selected model
agent.model = model
session = get_or_create_session(agent.name)

# --- Render Conversation History ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Render logs if present for agent responses
        if msg["role"] == "assistant" and msg.get("logs"):
            with st.expander("🔍 View Agent Execution Trace", expanded=False):
                for log in msg["logs"]:
                    # Style based on event details
                    badge_class = "thought-badge"
                    badge_label = "Agent Event"
                    if "tool_call" in log.lower():
                        badge_class = "tool-badge"
                        badge_label = "Tool Call"
                    elif "tool_response" in log.lower():
                        badge_class = "tool-badge"
                        badge_label = "Tool Return"
                        
                    st.markdown(f"""
                    <div class="thought-log-container">
                        <div class="thought-log-header">
                            <span class="{badge_class}">{badge_label}</span>
                        </div>
                        <div class="thought-log-content">{log}</div>
                    </div>
                    """, unsafe_allow_html=True)

# --- Handle User Query Input ---
query = st.chat_input("Where would you like to go and what is your mood?")

if query:
    # 1. Display and save user query
    st.chat_message("user").write(query)
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    # 2. Run runner in assistant bubble
    with st.chat_message("assistant"):
        # Live thought log container
        status_placeholder = st.status("🧞 Initializing ADK Runner...", expanded=True)
        response_placeholder = st.markdown("")
        
        runner = Runner(
            agent=agent,
            session_service=st.session_state.session_service,
            app_name=agent.name
        )
        
        logs = []
        final_response_container = [""]
        
        async def run_and_stream():
            try:
                async for event in runner.run_async(
                    user_id="streamlit_adventurer",
                    session_id=session.id,
                    new_message=Content(parts=[Part(text=query)], role="user")
                ):
                    event_str = str(event)
                    logs.append(event_str)
                    
                    # Update live status log
                    if event.is_final_response():
                        final_response_container[0] = event.content.parts[0].text
                        response_placeholder.markdown(final_response_container[0])
                    else:
                        # Beautify the logs shown in live status
                        event_type = getattr(event, "type", None)
                        event_type_str = str(event_type).split(".")[-1] if event_type else "LOG"
                        
                        if "tool_call" in event_str.lower():
                            status_placeholder.write(f"🛠️ **Executing Tool**: `{event_type_str}`")
                        elif "tool_response" in event_str.lower():
                            status_placeholder.write(f"✅ **Tool Returned Data**")
                        else:
                            status_placeholder.write(f"💭 **Thought Step**: `{event_type_str}`")
            except Exception as e:
                final_response_container[0] = f"An error occurred during execution: {e}"
                response_placeholder.markdown(final_response_container[0])
                
        # Run async loop inside streamlit
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_and_stream())
        
        # Complete the status widget
        status_placeholder.update(label="Itinerary Generated!", state="complete", expanded=False)
        
        # Save assistant message with execution logs
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": final_response_container[0],
            "logs": logs
        })
