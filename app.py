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
)

# ----------------------------------------------------------------------------
# CUSTOM CSS (Premium UI)
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #4a90e2;
        color: white;
        border-radius: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #357abd;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    .card {
        padding: 24px;
        border-radius: 16px;
        background-color: #1e1e1e;
        border: 1px solid #333;
        margin-bottom: 24px;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
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
def robust_analysis_call(data: Any, input_type: str) -> Dict[str, Any]:
    """Wraps the execution layer with exponential backoff retries."""
    return analyze_input(data, input_type)


# ----------------------------------------------------------------------------
# UI COMPONENTS
# ----------------------------------------------------------------------------
def render_header():
    st.title("🧠 Intelligent Decision-Support Interface")
    st.markdown(
        "Transforming **unstructured real-world inputs** into actionable, "
        "structured insights using Gemini 2.0 Flash."
    )


def render_sidebar(config):
    with st.sidebar:
        st.header("⚙️ System Status")
        st.info("### 3-Layer Architecture")
        st.caption("Layer 1: Directive (SOP)")
        st.caption("Layer 2: Orchestration (Decision Logic)")
        st.caption("Layer 3: Execution (Deterministic Scripts)")

        st.divider()

        if config["api_key_found"]:
            st.success("✅ Gemini API: Connected")
        else:
            st.error("❌ Gemini API: Key Missing in .env")
            st.info("Please add `GEMINI_API_KEY` to your `.env` file.")


# ----------------------------------------------------------------------------
# MAIN APPLICATION LOGIC
# ----------------------------------------------------------------------------
def main():
    config = load_app_config()
    render_header()
    render_sidebar(config)

    # Input Selection with Accessibility help
    input_mode = st.radio(
        "Select Inquiry Channel",
        ["Text Intelligence", "Visual Diagnostics", "Audio Analysis"],
        horizontal=True,
        help="Choose the type of messy real-world data you wish to process.",
    )

    # Mapping UI friendly names to internal types
    mode_map = {
        "Text Intelligence": (
            "text",
            "Paste messy notes, news feeds, or reports here:",
        ),
        "Visual Diagnostics": (
            "image",
            "Upload documents, scene photos, or medical scans:",
        ),
        "Audio Analysis": ("audio", "Upload voice recordings or audio updates:"),
    }
    internal_type, label = mode_map[input_mode]

    user_data = None

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if internal_type == "text":
            user_data = st.text_area(
                label,
                height=250,
                placeholder="e.g. Broken water main at 12th Street. Crews on site. Schools closing at 2pm.",
                help="Input raw text data from any source.",
            )

        elif internal_type == "image":
            uploaded_file = st.file_uploader(
                label,
                type=["jpg", "png", "jpeg"],
                help="Supports document scans and real-world scene photography.",
            )
            if uploaded_file:
                user_data = Image.open(uploaded_file)
                st.image(
                    user_data, caption="Ingested Visual Data", use_container_width=True
                )

        elif internal_type == "audio":
            uploaded_file = st.file_uploader(
                label,
                type=["wav", "mp3"],
                help="Handles verbal reports and ambient recordings.",
            )
            if uploaded_file:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                ) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    user_data = tmp.name
                st.audio(uploaded_file, format="audio/wav")

        st.markdown("</div>", unsafe_allow_html=True)

    # Execution Trigger
    if st.button(
        "🚀 Execute Strategic Analysis",
        help="Trigger the 3-layer architecture to process your input.",
    ):
        if not user_data:
            st.warning("⚠️ No data detected. Please provide input before execution.")
            return

        with st.spinner("Orchestrating AI Execution Layers..."):
            # Handle special audio upload for Gemini
            if internal_type == "audio":
                try:
                    audio_handle = genai.upload_file(path=user_data)
                    result = robust_analysis_call(audio_handle, "audio")
                except Exception as e:
                    st.error(f"Media Upload Failed: {e}")
                    return
            else:
                result = robust_analysis_call(user_data, internal_type)

            # Error Handling Layer
            if "error" in result:
                st.error(f"### Analysis Interrupted\n{result.get('error')}")
                if "details" in result:
                    with st.expander("Technical Error Surface"):
                        st.write(result["details"])
                return

            # Success Feedback & Insights Rendering
            render_insights(result)


def render_insights(result: Dict[str, Any]):
    """Renders the extraction results in a clean grid."""
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📋 Structural Summary")
        st.markdown(f"**Domain Category:** `{result.get('category', 'N/A')}`")
        st.markdown(f"**Abstract:** {result.get('summary', '...').strip()}")

        st.divider()
        st.markdown("**🔍 Identified Entities**")
        entities = result.get("entities", [])
        if entities:
            for e in entities:
                st.markdown(
                    f"- **{e.get('name')}** ({e.get('type')}): {e.get('value')}"
                )
        else:
            st.caption("No discrete entities identified in this dataset.")

    with col2:
        st.subheader("💡 Actionable Insights")
        insights = result.get("insights", [])
        for insight in insights:
            st.info(f"**Action:** {insight}")

        # System Confidence Gauge
        conf = result.get("confidence_score", 0.0)
        st.metric(
            label="Analytic Confidence Score",
            value=f"{conf * 100:.1f}%",
            delta="Reliable" if conf > 0.8 else "Conditional",
            help="Statistical certainty of the extraction schema.",
        )

    # Footer Metadata
    with st.expander("📦 Raw System Metadata (JSON)"):
        st.json(result)

    verif = result.get("verification", {})
    if verif.get("status") == "Verified":
        st.success(f"**Data Integrity Protocol:** Verified - {verif.get('notes')}")
    else:
        st.warning(
            f"**Data Integrity Protocol:** {verif.get('status')} - {verif.get('notes')}"
        )


if __name__ == "__main__":
    main()
    st.divider()
    st.caption("Architecture v2.0 | Security Hardened • Accessible • Deterministic")
