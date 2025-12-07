import streamlit as st
from crew_orchestrator import run_medical_assessment
from utils.image_processor import ImageProcessor
from config.config import Config
import os
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="AI Medical Assessor - POC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .disclaimer-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .severity-minor {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .severity-moderate {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .severity-serious {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .agent-progress {
        background-color: #e7f3ff;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessment_result' not in st.session_state:
    st.session_state.assessment_result = None
if 'uploaded_image_path' not in st.session_state:
    st.session_state.uploaded_image_path = None

# Header
st.markdown('<div class="main-header">🏥 AI Medical Assessor</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; color: #666;">Proof of Concept - External Injury Assessment</div>', unsafe_allow_html=True)

# Disclaimer
with st.expander("⚠️ MEDICAL DISCLAIMER - READ BEFORE USE", expanded=False):
    st.markdown(f"""
    <div class="disclaimer-box">
        <h3>⚠️ IMPORTANT MEDICAL DISCLAIMER</h3>
        <p>{Config.DISCLAIMER}</p>
        <ul>
            <li>This is a proof-of-concept AI tool for educational and demonstration purposes</li>
            <li>NOT approved for clinical use</li>
            <li>NOT a replacement for professional medical diagnosis</li>
            <li>Always seek professional medical attention for injuries</li>
            <li>In case of emergency, call 911 or go to nearest emergency room</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📋 How It Works")
    st.markdown("""
    **3-Agent AI System:**

    1. 🔍 **Vision Agent**
       - Analyzes injury photograph
       - Identifies visible features

    2. 🏥 **Diagnostic Agent**
       - Consults medical literature (PubMed)
       - Provides differential diagnosis

    3. 🎙️ **Communication Agent**
       - Generates patient-friendly report
       - Creates audio output
    """)

    st.header("🚨 Emergency?")
    st.error("""
    **Seek immediate medical attention if:**
    - Severe bleeding
    - Bone visible
    - Deep wound
    - Signs of infection
    - Difficulty breathing
    - Chest pain
    """)

    if st.button("🚑 Call Emergency Services"):
        st.markdown("**Call 911 immediately**")

    st.divider()

    st.header("ℹ️ About")
    st.info("""
    **POC Version**

    - CrewAI Multi-Agent
    - Gemini Pro Vision
    - PubMed Integration
    - Streamlit Interface
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Assess", "📊 Results", "🔧 Technical Details"])

with tab1:
    st.header("Upload Injury Photo")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose an injury photo (JPEG/PNG)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of the external injury"
        )

        if uploaded_file is not None:
            # Save uploaded file
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(upload_dir, f"injury_{timestamp}.jpg")

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.session_state.uploaded_image_path = file_path

            # Display image
            st.image(uploaded_file, caption="Uploaded Injury Photo", use_container_width=True)

            # Validate image
            is_valid, message = ImageProcessor.validate_image(file_path)

            if is_valid:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")

    with col2:
        st.info("""
        **Photo Guidelines:**

        ✓ Good lighting
        ✓ Clear focus
        ✓ Close-up view
        ✓ Entire injury visible

        ✗ Avoid blurry photos
        ✗ Avoid poor lighting
        ✗ Avoid obstructions
        """)

    st.divider()

    # Assessment button
    if st.session_state.uploaded_image_path:
        if st.button("🔍 Analyze Injury", type="primary", use_container_width=True):

            with st.spinner(""):
                # Progress indicators
                progress_container = st.container()

                with progress_container:
                    st.markdown('<div class="agent-progress">🔍 Vision Agent: Analyzing image...</div>', unsafe_allow_html=True)
                    progress_bar = st.progress(0)

                    try:
                        # Run assessment
                        result = run_medical_assessment(st.session_state.uploaded_image_path)

                        progress_bar.progress(33)
                        st.markdown('<div class="agent-progress">🏥 Diagnostic Agent: Consulting medical literature...</div>', unsafe_allow_html=True)

                        progress_bar.progress(66)
                        st.markdown('<div class="agent-progress">🎙️ Communication Agent: Preparing your report...</div>', unsafe_allow_html=True)

                        progress_bar.progress(100)
                        st.markdown('<div class="agent-progress">✅ Assessment complete!</div>', unsafe_allow_html=True)

                        # Store result
                        st.session_state.assessment_result = result

                        st.success("✅ Analysis complete! View results in the 'Results' tab.")
                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ Error during assessment: {str(e)}")
                        st.info("💡 Try uploading a different photo or check your internet connection")

with tab2:
    st.header("Assessment Results")

    if st.session_state.assessment_result:
        result = st.session_state.assessment_result

        # Check for errors
        if 'error' in result:
            st.error(f"❌ {result['error']}")
        else:
            report = result.get('patient_report', {})
            diagnostic = result.get('diagnostic_analysis', {})
            metadata = result.get('metadata', {})

            # Severity indicator
            severity = report.get('severity', 'uncertain')
            confidence = metadata.get('confidence', 0)

            severity_class = f"severity-{severity}"

            st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)

            # Summary
            st.subheader("📋 Summary")
            st.markdown(report.get('summary', 'No summary available'))

            st.markdown('</div>', unsafe_allow_html=True)

            # Confidence and review flag
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Confidence", f"{confidence}%")

            with col2:
                if metadata.get('requires_professional_review'):
                    st.warning("⚠️ Professional review recommended")
                else:
                    st.success("✅ Confidence threshold met")

            with col3:
                image_quality = metadata.get('image_quality', 0)
                st.metric("Image Quality", f"{image_quality}/10")

            st.divider()

            # Detailed report
            with st.expander("📖 Detailed Assessment", expanded=True):
                st.markdown(report.get('detailed', 'No detailed information available'))

            # Medical details
            with st.expander("🏥 Medical Details"):
                st.markdown(report.get('medical_details', 'No medical details available'))

            # Differential diagnosis
            if 'differential_diagnosis' in diagnostic:
                with st.expander("🔬 Differential Diagnosis"):
                    diff_diag = diagnostic['differential_diagnosis']

                    for i, condition in enumerate(diff_diag, 1):
                        st.write(f"**{i}. {condition['condition']}**")
                        st.progress(condition['probability'] / 100)
                        st.write(f"Likelihood: {condition['probability']}%")
                        st.write(f"Literature support: {condition['literature_count']} studies")
                        st.write("")

            # Audio output
            st.divider()
            st.subheader("🎙️ Audio Report")

            audio_path = report.get('audio_path')
            if audio_path and os.path.exists(audio_path):
                with open(audio_path, 'rb') as audio_file:
                    st.audio(audio_file.read(), format='audio/mp3')
            else:
                st.info("Audio generation in progress...")

            # Literature references
            if 'pubmed_results' in diagnostic:
                st.divider()
                with st.expander("📚 Medical Literature References"):
                    pubmed_results = diagnostic['pubmed_results']
                    st.write(f"Found {len(pubmed_results)} relevant studies:")

                    for result in pubmed_results[:5]:
                        st.write(f"**{result['title']}**")
                        st.write(f"*{result['source']}, {result['pubdate']}*")
                        st.write(f"PMID: {result['pmid']}")
                        st.write("")

    else:
        st.info("👆 Upload and analyze an injury photo to see results here")

with tab3:
    st.header("Technical Details")

    if st.session_state.assessment_result:
        result = st.session_state.assessment_result

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Vision Analysis")
            vision = result.get('vision_analysis', {})
            st.json({
                "confidence": vision.get('confidence', 0),
                "image_quality": vision.get('image_quality', 0),
                "description_length": len(vision.get('description', ''))
            })

        with col2:
            st.subheader("Diagnostic Analysis")
            diagnostic = result.get('diagnostic_analysis', {})
            st.json({
                "confidence": diagnostic.get('confidence', 0),
                "literature_count": diagnostic.get('literature_count', 0),
                "differential_count": len(diagnostic.get('differential_diagnosis', []))
            })

        st.divider()

        with st.expander("🔍 Full Raw Output (Debug)"):
            st.json(result)

        with st.expander("🧠 Crew Memory (Shared Context)"):
            metadata = result.get('metadata', {})
            if 'crew_memory' in metadata:
                st.json(metadata['crew_memory'])

    else:
        st.info("Technical details will appear here after assessment")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.8rem;">
    POC Version | CrewAI Multi-Agent System | Gemini Pro Vision | PubMed Integration<br>
    For demonstration purposes only - Not for clinical use
</div>
""", unsafe_allow_html=True)

