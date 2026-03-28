import streamlit as st
import os
import json
from PIL import Image
import tempfile
from execution.gemini_analyzer import analyze_input
from dotenv import load_dotenv
import google.generativeai as genai

# Page config
st.set_page_config(
    page_title="Intelligent Decision-Support Interface",
    page_icon="🧠",
    layout="wide",
)

# Custom CSS for a premium look
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #4a90e2;
        color: white;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #357abd;
        transform: scale(1.05);
    }
    .card {
        padding: 20px;
        border-radius: 12px;
        background-color: #1e1e1e;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .metric-card {
        text-align: center;
        padding: 15px;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 10px;
        margin: 10px;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.title("🧠 Intelligent Decision-Support Interface")
st.markdown("Transforming unstructured real-world inputs into actionable, structured insights in real-time.")

# Sidebar - Configuration and Information
with st.sidebar:
    st.header("⚙️ System Configuration")
    st.info("### 3-Layer Architecture")
    st.write("- **Directive**: `directives/data_structuring.md` (SOP)")
    st.write("- **Orchestration**: `app.py` (Decision Logic)")
    st.write("- **Execution**: `execution/gemini_analyzer.py` (Script)")
    
    st.divider()
    
    # Check for API key in .env
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        st.warning("⚠️ Warning: No Gemini API Key found in `.env`. Please add it to see analysis.")
    else:
        st.success("✅ Gemini API Key found.")

# Input Selection
input_mode = st.radio("Select Input Mode", ["Text Paste", "Image Upload", "Audio Upload"], horizontal=True)

# Main Input Section
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    if input_mode == "Text Paste":
        user_input = st.text_area("Paste messy notes, news feeds, or reports here:", height=200, placeholder="e.g. Broken water main at 12th Street. Crews on site. Schools closing at 2pm.")
    
    elif input_mode == "Image Upload":
        uploaded_file = st.file_uploader("Choose an image (documents, scenes, maps, etc.)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            user_input = Image.open(uploaded_file)
            st.image(user_input, caption="Uploaded Image", use_column_width=True)
        else:
            user_input = None

    elif input_mode == "Audio Upload":
        uploaded_file = st.file_uploader("Choose an audio file (voice recordings, updates, news feed)", type=["wav", "mp3"])
        if uploaded_file:
            # For now, let's treat audio as a transcript input for consistency 
            # or upload to Gemini File API if we want full multimodal
            # Let's save to .tmp first
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                user_input = tmp.name
            st.audio(uploaded_file, format='audio/wav')
        else:
            user_input = None
            
    st.markdown('</div>', unsafe_allow_html=True)

# Action Button
if st.button("Generate Structured Insights"):
    if user_input:
        with st.spinner("Processing through architected layers..."):
            # Call the execution layer
            input_type_map = {
                "Text Paste": "text",
                "Image Upload": "image",
                "Audio Upload": "audio"
            }
            
            # For audio, we'd ideally use the Gemini File API.
            # Simplified for MVP: if path is provided, we use the File API
            if input_mode == "Audio Upload":
                audio_file = genai.upload_file(path=user_input)
                result = analyze_input(audio_file, 'audio')
            else:
                result = analyze_input(user_input, input_type_map[input_mode])
            
            if "error" in result:
                st.error(f"Analysis failed: {result['error']}")
            else:
                # Dashboard Layout for results
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📋 Extraction Summary")
                    st.markdown(f"**Category:** {result.get('category', 'Unknown')}")
                    st.markdown(f"**Quick Overview:** {result.get('summary', 'No summary provided')}")
                    
                    st.markdown("---")
                    st.markdown("**Key Entities Found:**")
                    entities = result.get('entities', [])
                    if entities:
                        for e in entities:
                            st.markdown(f"- **{e.get('name')}** ({e.get('type')}): {e.get('value')}")
                    else:
                        st.write("No specific entities identified.")
                
                with col2:
                    st.subheader("💡 Actionable Insights")
                    insights = result.get('insights', [])
                    if insights:
                        for insight in insights:
                            st.info(f"👉 {insight}")
                    else:
                        st.write("No specific insights generated.")
                    
                    # Confidence Metric
                    conf = result.get('confidence_score', 0.0)
                    st.metric("System Confidence", f"{conf * 100:.0f}%", delta=f"{conf - 0.5:.2f}")

                # Raw Data View
                with st.expander("View Raw Structured JSON"):
                    st.json(result)
                    
                # Verification logic
                verif = result.get('verification', {})
                if verif.get('status') == "Verified":
                    st.success(f"**Data Integrity:** {verif.get('status')} - {verif.get('notes')}")
                else:
                    st.warning(f"**Data Integrity:** {verif.get('status')} - {verif.get('notes')}")

    else:
        st.warning("Please provide an input before generating insights.")

# Footer
st.divider()
st.caption("Built with 3-Layer Agentic Architecture | Python • Streamlit • Gemini 2.0 Flash")
