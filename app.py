import streamlit as st
import os
import logging
import tempfile
from PIL import Image
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from execution.gemini_analyzer import analyze_input
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------------------------------------------------------
# LOGGING & CONFIG
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Intelligent Decision-Support Interface",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# PREMIUM UI SYSTEM (Design System)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Outfit:wght@400;700&display=swap" rel="stylesheet">
<style>
    /* Global Styles */
    :root {
        --primary: #6366F1;
        --secondary: #06B6D4;
        --accent: #F43F5E;
        --bg-deep: #0B0E14;
        --card-bg: rgba(25, 30, 42, 0.7);
        --border-glow: rgba(99, 102, 241, 0.2);
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #111827, #0B0E14);
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .main-title {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        border-color: var(--primary);
        box-shadow: 0 0 20px var(--border-glow);
        transform: translateY(-2px);
    }
    
    /* Sidebar Aesthetics */
    .sidebar .stMarkdown {
        font-size: 0.9rem;
    }
    
    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-active { background-color: #22C55E; box-shadow: 0 0 8px #22C55E; }
    .status-pending { background-color: #FACC15; }
    .status-error { background-color: #EF4444; }

    /* Custom Button */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }

    /* Result Aesthetics */
    .insight-pill {
        background: rgba(99, 102, 241, 0.1);
        border-left: 4px solid var(--primary);
        padding: 12px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .entity-tag {
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.2);
        color: #22D3EE;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 4px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# CACHED UTILITIES
# ----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_app_config():
    """Load application configuration and environment."""
    load_dotenv()
    return {
        "api_key_found": bool(os.getenv("GEMINI_API_KEY")),
        "directive_path": "directives/data_structuring.md",
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
def robust_analysis_call(data: Any, input_type: str, model_id: str) -> Dict[str, Any]:
    """Wraps the execution layer with exponential backoff retries."""
    return analyze_input(data, input_type, model_id=model_id)


# ----------------------------------------------------------------------------
# UI COMPONENTS
# ----------------------------------------------------------------------------
def render_header():
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="font-size: 3rem; background: linear-gradient(to right, #818CF8, #22D3EE); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                INTELLIGENT DECISION SUPPORT
            </h1>
            <p style="font-size: 1.1rem; color: #94A3B8; letter-spacing: 0.1em;">
                REAL-TIME MULTIMODAL ACTIONABLE DATA SYNTHESIS
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(config):
    with st.sidebar:
        st.markdown(
            '<h2 style="font-size: 1.5rem;">⚙️ SYSTEM CORE</h2>', unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="glass-card" style="padding: 15px;">
                <p><span class="status-dot status-active"></span>Directive Layer: Live</p>
                <p><span class="status-dot status-active"></span>Orchestration: Ready</p>
                <p><span class="status-dot status-active"></span>Execution: Secure</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        if config["api_key_found"]:
            st.success("✅ Gemini Endpoint: Active")
        else:
            st.error("❌ Gemini Endpoint: Offline")
            st.info("Key missing in `.env`.")

        st.divider()
        st.markdown("### 🧠 ANALYTIC ENGINE")
        model_choice = st.selectbox(
            "Select Processing Core",
            [
                "gemini-flash-latest",
                "gemini-2.0-flash",
                "gemini-pro-latest",
                "gemini-flash-lite-latest",
            ],
            index=0,
            help="Switch models to manage quota limits or reasoning depth.",
        )
        return model_choice


# ----------------------------------------------------------------------------
# MAIN APPLICATION LOGIC
# ----------------------------------------------------------------------------
def main():
    config = load_app_config()
    render_header()
    model_id = render_sidebar(config)

    # Input Selection
    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button("📝 TEXT INTEL"):
            st.session_state.input_mode = "text"
    with cols[1]:
        if st.button("🖼️ VISUAL DIAG"):
            st.session_state.input_mode = "image"
    with cols[2]:
        if st.button("🎙️ AUDIO ANALYTICS"):
            st.session_state.input_mode = "audio"

    if "input_mode" not in st.session_state:
        st.session_state.input_mode = "text"

    internal_type = st.session_state.input_mode
    user_data = None

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    if internal_type == "text":
        user_data = st.text_area(
            "INCOMING DATA STREAM",
            height=200,
            placeholder="Paste raw notes, sensor feeds, or emergency reports...",
            help="Input raw text from any source.",
        )

    elif internal_type == "image":
        uploaded_file = st.file_uploader(
            "INGEST VISUAL DATA", type=["jpg", "png", "jpeg"]
        )
        if uploaded_file:
            user_data = Image.open(uploaded_file)
            st.image(user_data, use_container_width=True)

    elif internal_type == "audio":
        uploaded_file = st.file_uploader("INGEST AUDIO SIGNAL", type=["wav", "mp3"])
        if uploaded_file:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp:
                tmp.write(uploaded_file.getvalue())
                user_data = tmp.name
            st.audio(uploaded_file, format="audio/wav")

    st.markdown("</div>", unsafe_allow_html=True)

    # Execution Trigger
    if st.button("🚀 EXECUTE STRATEGIC SYNTHESIS"):
        if not user_data:
            st.warning("⚠️ No data detected. Please feed the signal.")
            return

        with st.spinner("Processing through 3-Layer Architecture..."):
            if internal_type == "audio":
                try:
                    audio_handle = genai.upload_file(path=user_data)
                    result = robust_analysis_call(audio_handle, "audio", model_id)
                except Exception as e:
                    st.error(f"Media Upload Failed: {e}")
                    return
            else:
                result = robust_analysis_call(user_data, internal_type, model_id)

            if "error" in result:
                st.error(f"Analysis Failed: {result['error']}")
                return

            render_insights(result)


def render_insights(result: Dict[str, Any]):
    """Renders the extraction results in a premium UI layout."""
    st.markdown("---")
    res_col1, res_col2 = st.columns([1, 1.2], gap="large")

    with res_col1:
        st.markdown(
            f'<div class="glass-card" style="border-left: 5px solid var(--secondary);">'
            f'<h3 style="color: var(--secondary);">📋 EXTRACTION SUMMARY</h3>'
            f'<p><strong>DOMAIN:</strong> <span class="entity-tag">{result.get("category", "N/A")}</span></p>'
            f'<p style="font-size: 0.95rem;">{result.get("summary", "No summary available.")}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🔍 KEY ENTITIES")
        entities = result.get("entities", [])
        if entities:
            for e in entities:
                st.markdown(
                    f'<span class="entity-tag"><strong>{e.get("name")}</strong> | {e.get("type")}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No entities identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    with res_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 💡 STRATEGIC INSIGHTS")
        insights = result.get("insights", [])
        for insight in insights:
            st.markdown(
                f'<div class="insight-pill">{insight}</div>', unsafe_allow_html=True
            )

        # Confidence Gauge using dynamic HTML bars
        conf = result.get("confidence_score", 0.0)
        color = "#22C55E" if conf > 0.8 else "#FACC15"
        st.markdown(
            f"""
            <div style="margin-top: 20px;">
                <p style="margin-bottom: 5px; font-weight: 600;">ANALYTIC CONFIDENCE: {conf*100:.1f}%</p>
                <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px;">
                    <div style="background: {color}; width: {conf*100}%; height: 100%; border-radius: 10px; box-shadow: 0 0 10px {color};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Integrity view
    verif = result.get("verification", {})
    v_status = verif.get("status", "Unknown")
    v_color = "#22C55E" if v_status == "Verified" else "#EF4444"
    st.markdown(
        f"""
        <div class="glass-card" style="border-top: 1px solid {v_color}; background: rgba(0,0,0,0.2);">
            <strong style="color: {v_color};">INTEGRITY PROTOCOL:</strong> {v_status} — {verif.get('notes')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📦 RAW SYSTEM LOG"):
        st.json(result)


if __name__ == "__main__":
    main()
    st.markdown(
        '<div style="text-align: center; color: #64748B; font-size: 0.8rem; margin-top: 50px;">'
        "ARCHITECTURE V2.5 | POWERED BY GEMINI ADAPTIVE EXECUTION • CLOUDRUN READY"
        "</div>",
        unsafe_allow_html=True,
    )
