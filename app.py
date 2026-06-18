import streamlit as st
import config
from utils.session_state import init_session_state, reset_document_state, reset_quiz_state, save_session_state
from utils.pdf_processor import extract_text_from_pdf, chunk_text
from services.gemini_service import configure_gemini
from services.topic_extractor import extract_topics
from services.tutor_engine import generate_topic_lesson
from services.doubt_solver import solve_doubt
from services.quiz_generator import generate_quiz, evaluate_quiz

# 1. Page Configuration & Custom Styling
st.set_page_config(
    page_title="StudyFlow AI — AI Tutor & Study Guide",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Font Awesome 6 Icons
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
    unsafe_allow_html=True
)

# Initialize session state variables
init_session_state()

# CSS Variables and Custom Styling 
theme_css = """
:root {
    --bg-color: #f8fafc;
    --sidebar-bg-color: #ffffff;
    --content-bg-color: #ffffff;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --border-color: #e2e8f0;
    --primary-color: #2563eb;
    --primary-hover-color: #1d4ed8;
    --card-bg: #ffffff;
    --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
    --nav-active-bg: #eff6ff;
    --nav-text-active: #1e40af;
    --nav-text-inactive: #475569;
    --nav-hover-bg: #f1f5f9;
    --success-color: #16a34a;
    --warning-color: #d97706;
    --info-color: #2563eb;
    --info-bg: #f0f7ff;
}
"""

st.markdown(f"""
<style>
    {theme_css}
    
    /* Global Background and Typography */
    .stApp {{
        background-color: var(--bg-color) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }}
    
    /* Clean Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }}
    
    /* Headings and Texts */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }}
    
    .stMarkdown p, .stMarkdown span, .stMarkdown label {{
        color: var(--text-secondary) !important;
    }}
    
    /* Hide default Streamlit headers and footers */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    footer {{
        display: none !important;
    }}
    
    /* Primary buttons (filled) */
    div[data-testid="stBaseButton-primary"] button {{
        background-color: var(--primary-color) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }}
    div[data-testid="stBaseButton-primary"] button:hover {{
        background-color: var(--primary-hover-color) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }}
    
    /* Secondary buttons (outline) */
    div[data-testid="stBaseButton-secondary"] button {{
        background-color: transparent !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }}
    div[data-testid="stBaseButton-secondary"] button:hover {{
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        background-color: var(--nav-hover-bg) !important;
    }}
    
    /* Sidebar Navigation Container & Buttons */
    div.sidebar-nav-container {{
        margin-top: 1rem !important;
        margin-bottom: 1.5rem !important;
    }}
    div.sidebar-nav-container button {{
        text-align: left !important;
        justify-content: flex-start !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.25rem !important;
        width: 100% !important;
    }}
    div.sidebar-nav-container div[data-testid="stBaseButton-secondary"] button {{
        background-color: transparent !important;
        color: var(--nav-text-inactive) !important;
    }}
    div.sidebar-nav-container div[data-testid="stBaseButton-secondary"] button:hover {{
        background-color: var(--nav-hover-bg) !important;
        color: var(--text-primary) !important;
    }}
    div.sidebar-nav-container div[data-testid="stBaseButton-primary"] button {{
        background-color: var(--nav-active-bg) !important;
        color: var(--nav-text-active) !important;
        font-weight: 600 !important;
    }}
    
    /* Modern Card Layouts (bordered containers) */
    div[data-testid="stVerticalBlockBorder"],
    div[data-testid="stVerticalBlockBorder"] > div,
    div[data-testid="stVerticalBlockBorder"] [data-testid="stVerticalBlock"] {{
        background-color: var(--card-bg) !important;
        border-radius: 12px !important;
        box-shadow: var(--card-shadow) !important;
    }}
    div[data-testid="stVerticalBlockBorder"] {{
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    /* Info Box */
    .info-box {{
        background-color: var(--info-bg) !important;
        border-left: 4px solid var(--info-color) !important;
        padding: 1rem !important;
        border-radius: 6px !important;
        margin-bottom: 1.5rem !important;
        color: var(--text-secondary) !important;
        font-size: 0.95rem !important;
    }}
    
    /* List Item Row */
    .list-item {{
        margin-bottom: 0.75rem !important;
        font-size: 0.95rem !important;
        color: var(--text-secondary) !important;
        line-height: 1.5 !important;
        display: flex !important;
        align-items: flex-start !important;
    }}
    .list-item i {{
        margin-top: 4px !important;
        margin-right: 10px !important;
    }}
    
    /* Sub-tabs Styling */
    div[data-testid="stTabBar"] {{
        background-color: transparent !important;
        border-bottom: 2px solid var(--border-color) !important;
        margin-bottom: 1.5rem !important;
    }}
    button[data-testid="stMarkdownTab"] {{
        color: var(--nav-text-inactive) !important;
        background-color: transparent !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 1rem !important;
    }}
    button[data-testid="stMarkdownTab"][aria-selected="true"] {{
        color: var(--primary-color) !important;
        border-bottom: 2px solid var(--primary-color) !important;
        font-weight: 600 !important;
    }}
    
    /* Chat message container override */
    div[data-testid="stChatMessage"] {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Main Headers */
    .main-header {{
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem !important;
    }}
    .sub-header {{
        font-size: 1.05rem !important;
        color: var(--text-secondary) !important;
        margin-bottom: 2rem !important;
        line-height: 1.5 !important;
    }}
    
    /* Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        box-shadow: var(--card-shadow) !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{
        color: var(--text-secondary) !important;
    }}
    
    /* General Widget Labels & Controls visibility */
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] label,
    .stWidgetLabel p,
    label {{
        color: var(--text-primary) !important;
    }}
    
    /* Selectbox Styling */
    div[data-baseweb="select"] > div {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
    }}
    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] div {{
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: var(--text-secondary) !important;
    }}
    
    /* Dropdown Menu styling */
    div[data-baseweb="menu"] {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
    }}
    div[data-baseweb="menu"] li {{
        color: var(--text-primary) !important;
        background-color: transparent !important;
    }}
    div[data-baseweb="menu"] li:hover {{
        background-color: var(--nav-hover-bg) !important;
    }}
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] section {{
        background-color: var(--card-bg) !important;
        border: 1px dashed var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }}
    div[data-testid="stFileUploader"] label {{
        color: var(--text-primary) !important;
    }}
    div[data-testid="stFileUploader"] small {{
        color: var(--text-secondary) !important;
    }}
    div[data-testid="stFileUploader"] section button {{
        background-color: var(--sidebar-bg-color) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    /* Align right-column navigation buttons to the right */
    div[data-testid="column"]:nth-of-type(2) button {{
        float: right !important;
        width: auto !important;
    }}
</style>
""", unsafe_allow_html=True)

# 2. Sidebar Setup
with st.sidebar:
    st.markdown('<h2 class="sidebar-logo" style="margin-bottom:0.2rem;"><i class="fa-solid fa-graduation-cap" style="color: var(--primary-color); margin-right: 8px;"></i>StudyFlow AI</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-secondary); font-size: 0.82rem; margin-top:0; margin-bottom: 1.5rem;">Guided Learning Platform</p>', unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # 2.0 Study View Selection (if document is uploaded)
    if st.session_state.pdf_metadata:
        st.markdown('<h5>Study View</h5>', unsafe_allow_html=True)
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            btn_type = "primary" if st.session_state.view_mode == "learning_plan" else "secondary"
            if st.button("Learn", key="switch_learning_plan", type=btn_type, use_container_width=True):
                if not st.session_state.topics:
                    with st.spinner("Analyzing curriculum and extracting topics..."):
                        topics = extract_topics(st.session_state.pdf_raw_text, st.session_state.study_mode)
                        st.session_state.topics = topics
                st.session_state.view_mode = "learning_plan"
                st.rerun()
        with col_v2:
            btn_type = "primary" if st.session_state.view_mode == "recall_sheet" else "secondary"
            if st.button("Exam Recall", key="switch_recall_sheet", type=btn_type, use_container_width=True):
                if not st.session_state.recall_sheet:
                    from services.recall_sheet_generator import generate_recall_sheet
                    with st.spinner("Generating Exam Recall Sheet..."):
                        st.session_state.recall_sheet = generate_recall_sheet(st.session_state.pdf_raw_text)
                st.session_state.view_mode = "recall_sheet"
                st.rerun()
        st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # 2.1 Learning Path navigation buttons
    st.markdown('<h5>Learning Path</h5>', unsafe_allow_html=True)
    if st.session_state.topics:
        # Progress Calculation & Visual Gauge
        completed_count = len(st.session_state.completed_topics)
        total_count = len(st.session_state.topics)
        progress_percentage = int(completed_count / total_count * 100) if total_count > 0 else 0
        
        # Flatten choices: each topic has an Explanation page and a Quiz page
        choices = []
        for idx, t in enumerate(st.session_state.topics):
            choices.append({"type": "explanation", "idx": idx})
            choices.append({"type": "quiz", "idx": idx})
            
        # Determine the currently selected index in the flat list
        active_choice_idx = 0
        current_type = "quiz" if st.session_state.active_section in ["quiz", "analysis"] else "explanation"
        for choice_idx, choice in enumerate(choices):
            if choice["idx"] == st.session_state.current_topic_index and choice["type"] == current_type:
                active_choice_idx = choice_idx
                break

        # Render selector for LMS segments using our custom styled buttons
        st.markdown('<div class="sidebar-nav-container">', unsafe_allow_html=True)
        for choice_idx, choice in enumerate(choices):
            idx = choice["idx"]
            t = st.session_state.topics[idx]
            name = t["name"]
            
            is_active = (idx == st.session_state.current_topic_index and choice["type"] == current_type)
            
            status_symbol = "✓" if name in st.session_state.completed_topics else "○"
            prefix = "Read:" if choice["type"] == "explanation" else "Quiz:"
            btn_label = f"{status_symbol} {prefix} {name}"
            
            btn_type = "primary" if is_active else "secondary"
            if st.button(btn_label, key=f"nav_{choice_idx}", type=btn_type, use_container_width=True):
                st.session_state.current_topic_index = idx
                st.session_state.active_section = "explanation" if choice["type"] == "explanation" else "quiz"
                if choice["type"] == "quiz":
                    reset_quiz_state()
                st.session_state.view_mode = "learning_plan"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-style: italic; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;">Upload notes to generate your path</div>', unsafe_allow_html=True)
        
    st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)

    # 2.2 Study Mode selection
    st.markdown('<h5>Study Mode</h5>', unsafe_allow_html=True)
    study_modes = ["Exam Preparation", "Learn Concepts", "Quick Revision"]
    try:
        default_index = study_modes.index(st.session_state.study_mode)
    except ValueError:
        default_index = 1  # Fallback default
        
    selected_mode = st.selectbox(
        "Choose Study Mode",
        study_modes,
        index=default_index,
        label_visibility="collapsed",
        help="Tailors explanation density, priorities, and details."
    )
    
    # If the user changes the study mode, sync with state and reset active explanations
    if selected_mode != st.session_state.study_mode:
        st.session_state.study_mode = selected_mode
        st.session_state.explanations = {}
        st.rerun()
        
    st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)

    # 2.3 Progress Summary
    if st.session_state.topics:
        st.markdown('<h5>Progress</h5>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.8rem; font-weight:600; color:var(--primary-color); margin-bottom: 0.3rem;">{progress_percentage}% COMPLETE ({completed_count}/{total_count} Topics)</div>', unsafe_allow_html=True)
        st.progress(progress_percentage / 100.0)
        st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)
        

    api_configured = configure_gemini()


    # 2.5 Uploaded Material
    st.markdown('<h5>Uploaded Material</h5>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Notes (PDF)", 
        type=["pdf"],
        label_visibility="collapsed"
    )
    
    # Process newly uploaded file
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.pdf_metadata.get("file_id") != file_id:
            if not api_configured:
                st.error("Please set API key before processing.")
            else:
                with st.spinner("Processing PDF and indexing notes..."):
                    try:
                        reset_document_state()
                        raw_data = extract_text_from_pdf(uploaded_file)
                        st.session_state.pdf_raw_text = raw_data["full_text"]
                        st.session_state.pdf_metadata = {
                            "file_id": file_id,
                            "file_name": uploaded_file.name,
                            "page_count": raw_data["page_count"],
                            "char_count": raw_data["char_count"]
                        }
                        chunks = chunk_text(
                            raw_data["full_text"], 
                            chunk_size=config.CHUNK_SIZE, 
                            chunk_overlap=config.CHUNK_OVERLAP
                        )
                        st.session_state.processed_chunks = chunks
                        from utils.vector_store import index_pdf_chunks
                        index_pdf_chunks(chunks)
                        st.session_state.view_mode = "landing"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error analyzing document: {e}")
                        
    if st.session_state.pdf_metadata:
        st.markdown(f"""
        <div style="background-color: var(--info-bg); border: 1px solid var(--border-color); padding: 0.75rem; border-radius: 6px; font-size: 0.8rem; margin-top: 0.5rem;">
            <div style="font-weight: 600; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;"><i class="fa-solid fa-file-pdf" style="margin-right: 6px; color: #ef4444;"></i>{st.session_state.pdf_metadata['file_name']}</div>
            <div style="color: var(--text-secondary); margin-top: 0.25rem;">{st.session_state.pdf_metadata['page_count']} pages &bull; {st.session_state.pdf_metadata['char_count']:,} chars</div>
        </div>
        """, unsafe_allow_html=True)
# 3. View Routing
if st.session_state.view_mode == "landing":
    if not st.session_state.pdf_metadata:
        # Standard Welcome Landing Page (No PDF uploaded yet)
        st.markdown('<h1 class="main-header"><i class="fa-solid fa-graduation-cap" style="color: var(--primary-color); margin-right: 12px;"></i>StudyFlow AI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">A guided study platform that extracts a tailored curriculum from your notes, provides explanations, and diagnostics of your understanding.</p>', unsafe_allow_html=True)
        
        # Friendly instructional alert
        st.markdown("""
        <div class="info-box" style="margin-bottom: 2rem;">
            <span style="font-weight: bold; color: var(--primary-color);"><i class="fa-solid fa-circle-info" style="margin-right: 8px;"></i>Getting Started</span>
            <p style="margin: 0.25rem 0 0 0;">Please upload your study notes PDF in the sidebar to begin. StudyFlow AI will analyze your notes and prepare your interactive study session.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.markdown('<h4><i class="fa-solid fa-route" style="margin-right: 8px; color: var(--primary-color);"></i>Structured Path</h4>', unsafe_allow_html=True)
                st.markdown('<p style="font-size: 0.92rem; line-height: 1.5; color: var(--text-secondary);">Your notes are parsed into key sequential topics, creating an organized learning path that tracks your mastery as you study.</p>', unsafe_allow_html=True)
        with col2:
            with st.container(border=True):
                st.markdown('<h4><i class="fa-solid fa-sliders" style="margin-right: 8px; color: var(--primary-color);"></i>Study Goals</h4>', unsafe_allow_html=True)
                st.markdown('<p style="font-size: 0.92rem; line-height: 1.5; color: var(--text-secondary);">Select study modes tailored to your objective: Learn Concepts for a beginner curve, Exam Prep for test focus, or Quick Revision.</p>', unsafe_allow_html=True)
        with col3:
            with st.container(border=True):
                st.markdown('<h4><i class="fa-solid fa-clipboard-question" style="margin-right: 8px; color: var(--primary-color);"></i>Smart Quizzes</h4>', unsafe_allow_html=True)
                st.markdown('<p style="font-size: 0.92rem; line-height: 1.5; color: var(--text-secondary);">Assess your knowledge with questions mapped to notes, and identify specific topics needing revision with detailed diagnostics.</p>', unsafe_allow_html=True)
    else:
        # PDF is uploaded, but no plan or recall sheet is generated yet (Landing with PDF metadata)
        st.markdown('<h1 class="main-header"><i class="fa-solid fa-graduation-cap" style="color: var(--primary-color); margin-right: 12px;"></i>StudyFlow AI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Your notes have been successfully processed. Choose how you would like to proceed with your study session below.</p>', unsafe_allow_html=True)
        
        # Display uploaded file details
        meta = st.session_state.pdf_metadata
        st.markdown(f"""
        <div style="background-color: var(--info-bg); border: 1px solid var(--border-color); padding: 1.25rem; border-radius: 8px; margin-bottom: 2rem;">
            <div style="font-size: 1rem; font-weight: 600; color: var(--text-primary);"><i class="fa-solid fa-file-pdf" style="margin-right: 8px; color: #ef4444; font-size: 1.2rem;"></i>{meta['file_name']}</div>
            <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
                <strong>Pages:</strong> {meta['page_count']} &nbsp;&bull;&nbsp; 
                <strong>Characters:</strong> {meta['char_count']:,} &nbsp;&bull;&nbsp; 
                <strong>Active Study Mode:</strong> {st.session_state.study_mode}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Columns for option selection
        col_plan, col_recall = st.columns(2)
        
        with col_plan:
            with st.container(border=True):
                st.markdown('<h3 style="margin-top:0;"><i class="fa-solid fa-route" style="margin-right: 10px; color: var(--primary-color);"></i>Guided Learning Plan</h3>', unsafe_allow_html=True)
                st.markdown('<p style="font-size: 0.95rem; color: var(--text-secondary); min-height: 100px; line-height: 1.6;">Break your notes into topics, understand concepts,ask doubts, and test yourself with quizzes.</p>', unsafe_allow_html=True)
                if st.button("Generate Guided Learning Plan", key="landing_generate_lp", type="primary", use_container_width=True):
                    with st.spinner("Analyzing curriculum and extracting topics..."):
                        topics = extract_topics(st.session_state.pdf_raw_text, st.session_state.study_mode)
                        st.session_state.topics = topics
                    st.session_state.view_mode = "learning_plan"
                    st.rerun()
                    
        with col_recall:
            with st.container(border=True):
                st.markdown('<h3 style="margin-top:0;"><i class="fa-solid fa-bolt" style="margin-right: 10px; color: var(--warning-color);"></i>Exam Recall Sheet</h3>', unsafe_allow_html=True)
                st.markdown('<p style="font-size: 0.95rem; color: var(--text-secondary); min-height: 100px; line-height: 1.6;">A compressed revision sheet that helps you quickly remember everything you have studied before an exam.</p>', unsafe_allow_html=True)
                if st.button("Generate Exam Recall Sheet", key="landing_generate_rs", type="primary", use_container_width=True):
                    from services.recall_sheet_generator import generate_recall_sheet
                    with st.spinner("Generating Recall Sheet..."):
                        st.session_state.recall_sheet = generate_recall_sheet(st.session_state.pdf_raw_text)
                    st.session_state.view_mode = "recall_sheet"
                    st.rerun()

elif st.session_state.view_mode == "recall_sheet":
    # Show the Recall Sheet screen
    if not st.session_state.recall_sheet:
        from services.recall_sheet_generator import generate_recall_sheet
        with st.spinner("Generating Recall Sheet..."):
            st.session_state.recall_sheet = generate_recall_sheet(st.session_state.pdf_raw_text)
            
    col_rs_left, col_rs_mid, col_rs_right = st.columns([1, 4, 1])
    with col_rs_mid:
        with st.container(border=True):
            st.markdown('<h2 style="text-align: center; color: var(--primary-color); margin-top:0;"><i class="fa-solid fa-bolt" style="margin-right: 10px; color: var(--warning-color);"></i>Exam Recall Sheet</h2>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: var(--text-secondary); font-style: italic; font-size: 0.95rem; margin-bottom: 1.5rem;">Last-minute memory triggers. Read 10-15 minutes before the exam.</p>', unsafe_allow_html=True)
            st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1.5rem 0;'>", unsafe_allow_html=True)
            
            st.markdown(st.session_state.recall_sheet)
            
            st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 2rem 0;'>", unsafe_allow_html=True)
            
            # Action button to switch back to Learning Plan
            col_rs_btn_l, col_rs_btn_r = st.columns([2, 1])
            with col_rs_btn_l:
                st.markdown('<p style="font-size: 0.9rem; color: var(--text-secondary); margin: 0.5rem 0 0 0;">Ready for deeper study? Switch to the structured path.</p>', unsafe_allow_html=True)
            with col_rs_btn_r:
                if st.button("Go to Learning Plan →", key="recall_to_lp", type="primary", use_container_width=True):
                    if not st.session_state.topics:
                        with st.spinner("Analyzing curriculum and extracting topics..."):
                            topics = extract_topics(st.session_state.pdf_raw_text, st.session_state.study_mode)
                            st.session_state.topics = topics
                    st.session_state.view_mode = "learning_plan"
                    st.rerun()

elif st.session_state.view_mode == "learning_plan":
    # Core Study Board View
    # Ensure topics are extracted
    if not st.session_state.topics:
        with st.spinner("Analyzing curriculum and extracting topics..."):
            topics = extract_topics(st.session_state.pdf_raw_text, st.session_state.study_mode)
            st.session_state.topics = topics
            
    current_topic = st.session_state.topics[st.session_state.current_topic_index]
    topic_name = current_topic["name"]
    topic_priority = current_topic["priority"]
    total_topics = len(st.session_state.topics)
    quiz = st.session_state.quiz
    
    # 1. LMS Style Top Navigation buttons (Back/Next)
    col_nav_left, col_nav_right = st.columns([1, 1])
    with col_nav_left:
        # Render Left navigation button based on state
        if st.session_state.active_section == "quiz":
            if st.button("← Back to Lesson", key="nav_back_lesson", type="secondary"):
                st.session_state.active_section = "explanation"
                st.rerun()
        elif st.session_state.active_section == "analysis":
            if st.button("← Back to Quiz", key="nav_back_quiz", type="secondary"):
                st.session_state.active_section = "quiz"
                st.rerun()
        elif st.session_state.active_section == "explanation" and st.session_state.current_topic_index > 0:
            if st.button("← Previous Topic", key="nav_prev_topic", type="secondary"):
                st.session_state.current_topic_index -= 1
                st.session_state.active_section = "explanation"
                reset_quiz_state()
                st.rerun()
                
    with col_nav_right:
        # Render Right navigation button based on state
        if st.session_state.active_section == "explanation":
            if st.button("Start Assessment →", key="nav_next_quiz", type="primary"):
                st.session_state.active_section = "quiz"
                reset_quiz_state()
                st.rerun()
        elif st.session_state.active_section == "quiz" and quiz["completed"]:
            if st.button("View Analysis →", key="nav_view_analysis", type="primary"):
                st.session_state.active_section = "analysis"
                st.rerun()
        elif st.session_state.active_section == "analysis":
            if st.session_state.current_topic_index < total_topics - 1:
                if st.button("Next Topic →", key="nav_next_topic", type="primary"):
                    st.session_state.current_topic_index += 1
                    st.session_state.active_section = "explanation"
                    reset_quiz_state()
                    st.rerun()
            else:
                st.success("Congratulations! You have completed all topics in this path.")
                
    st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    
    # Header display (LMS breadcrumbs details)
    st.markdown(f'<div style="color: var(--primary-color); font-weight: 600; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.2rem;">Topic {st.session_state.current_topic_index + 1} of {total_topics}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="margin-top:0; margin-bottom:0.6rem; font-weight:800; font-size: 2.2rem; color: var(--text-primary);">{topic_name}</h1>', unsafe_allow_html=True)
    
    if st.session_state.study_mode == "Exam Preparation":
        priority_color = "var(--success-color)" if "Lower" in topic_priority else ("var(--warning-color)" if "Medium" in topic_priority else "red")
        st.markdown(f'<div style="font-size: 0.85rem; font-weight: 500;">Exam Target Priority: <span style="color: {priority_color}; font-weight: 600;">{topic_priority}</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Section Router
    if st.session_state.active_section == "explanation":
        # ------------------ Explanation & Chat Page ------------------
        if not api_configured:
            st.warning("Please set API key to generate lessons.")
        else:
            cache_key = f"{topic_name}_{st.session_state.study_mode}"
            
            # If the cached lesson is a fallback, clear it so we can retry with the working key/model
            if cache_key in st.session_state.explanations:
                cached_lesson = st.session_state.explanations[cache_key]
                if cached_lesson.get("is_fallback") or "Please configure API access." in cached_lesson.get("quick_recall", ""):
                    del st.session_state.explanations[cache_key]
                    
            if cache_key not in st.session_state.explanations:
                with st.spinner("Generating conceptual explanation tailored to your study goal..."):
                    other_topics = [t["name"] for t in st.session_state.topics if t["name"] != topic_name]
                    res = generate_topic_lesson(topic_name, st.session_state.study_mode, other_topics)
                    # Only cache successful API responses, do not cache fallbacks
                    if not res.get("is_fallback"):
                        st.session_state.explanations[cache_key] = res
                    lesson = res
            else:
                lesson = st.session_state.explanations[cache_key]
            
            # Sub-layout tabs for structured explanation
            sub_tab_1, sub_tab_2, sub_tab_3 = st.tabs(["Lesson Explanation", "Key Points", "Exam Focus"])
            
            with sub_tab_1:
                if lesson.get("quick_recall"):
                    st.markdown(f"""
                    <div class="info-box">
                        <span style="color: var(--primary-color); font-weight: bold; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;"><i class="fa-solid fa-bolt" style="margin-right: 6px;"></i>Quick Recall</span>
                        <p style="margin: 0.5rem 0 0 0; font-style: italic;">"{lesson['quick_recall']}"</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.markdown('<h3><i class="fa-solid fa-book-open" style="margin-right: 10px; color: var(--primary-color);"></i>Explanation</h3>', unsafe_allow_html=True)
                    st.write(lesson.get("explanation", ""))
                    
            with sub_tab_2:
                with st.container(border=True):
                    st.markdown('<h3><i class="fa-solid fa-list-check" style="margin-right: 10px; color: var(--primary-color);"></i>Key Points</h3>', unsafe_allow_html=True)
                    st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                    for point in lesson.get("key_points", []):
                        st.markdown(f'<div class="list-item"><i class="fa-solid fa-circle-check" style="color: var(--primary-color); margin-top: 4px; margin-right: 10px;"></i><span>{point}</span></div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
            with sub_tab_3:
                with st.container(border=True):
                    st.markdown('<h3><i class="fa-solid fa-bullseye" style="margin-right: 10px; color: var(--primary-color);"></i>Exam Focus</h3>', unsafe_allow_html=True)
                    st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                    exam_focus_data = lesson.get("exam_focus", [])
                    if isinstance(exam_focus_data, list):
                        for focus in exam_focus_data:
                            st.markdown(f'<div class="list-item"><i class="fa-solid fa-circle-notch" style="color: var(--warning-color); margin-top: 4px; margin-right: 10px;"></i><span>{focus}</span></div>', unsafe_allow_html=True)
                    else:
                        st.write(exam_focus_data)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
        # ChatGPT-Style Doubt chatbot (Directly integrated on the same page!)
        st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 2rem 0;'>", unsafe_allow_html=True)
        st.markdown('<h3><i class="fa-solid fa-circle-question" style="margin-right: 10px; color: var(--primary-color);"></i>Ask a Doubt</h3>', unsafe_allow_html=True)
        
        
        if not api_configured:
            st.warning("Please set API key to solve doubts.")
        else:
            if topic_name not in st.session_state.doubt_history:
                st.session_state.doubt_history[topic_name] = []
                
            history = st.session_state.doubt_history[topic_name]
            
            # Welcome message if chat history is empty
            if not history:
                st.markdown(
                    '<div class="info-box">'
                    '<i class="fa-solid fa-robot" style="margin-right: 8px;"></i>Have doubts or need another analogy? Enter your question below and I\'ll search your uploaded notes.'
                    '</div>',
                    unsafe_allow_html=True
                )
                
            # Display history
            for msg in history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
            # User input box
            user_question = st.chat_input("Ask a question about this topic...")
            
            if user_question:
                history.append({"role": "user", "content": user_question})
                with st.chat_message("user"):
                    st.write(user_question)
                    
                with st.spinner("Tutor is thinking..."):
                    reply = solve_doubt(user_question, topic_name, history[:-1])
                    
                history.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.write(reply)
                    st.rerun()
                    
            if history:
                st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                if st.button("Clear Conversation History", type="secondary"):
                    st.session_state.doubt_history[topic_name] = []
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
        # Bottom page Navigation Row
        st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 2rem 0;'>", unsafe_allow_html=True)
        col_bot_l, col_bot_r = st.columns([1, 1])
        with col_bot_l:
            if st.session_state.current_topic_index > 0:
                if st.button("← Previous Topic", key="bot_prev", type="secondary", use_container_width=True):
                    st.session_state.current_topic_index -= 1
                    st.session_state.active_section = "explanation"
                    reset_quiz_state()
                    st.rerun()
        with col_bot_r:
            if st.button("Start Assessment →", key="bot_quiz", type="primary", use_container_width=True):
                st.session_state.active_section = "quiz"
                reset_quiz_state()
                st.rerun()
                
    elif st.session_state.active_section == "quiz":
        # ------------------ Quiz Page ------------------
        st.markdown('<h3><i class="fa-solid fa-clipboard-check" style="margin-right: 10px; color: var(--primary-color);"></i>Practice Quiz</h3>', unsafe_allow_html=True)
        st.caption("Assess your understanding of the current topic with questions dynamically generated from your notes.")
        
        if not api_configured:
            st.warning("Please set API key to generate quizzes.")
        else:
            if not quiz["questions"]:
                with st.container(border=True):
                    st.markdown('<h5>Choose Quiz Length</h5>', unsafe_allow_html=True)
                    quiz_size = st.selectbox("Number of Questions", [3, 5, 10], index=1, label_visibility="collapsed")
                    st.session_state.quiz["size"] = quiz_size
                    
                    st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                    if st.button("Generate Custom Quiz", type="primary"):
                        with st.spinner("Analyzing notes and designing questions..."):
                            quiz_questions = generate_quiz(topic_name, size=quiz_size)
                            st.session_state.quiz["questions"] = quiz_questions
                            st.session_state.quiz["selected_answers"] = {}
                            st.session_state.quiz["completed"] = False
                            st.session_state.quiz["score"] = None
                            st.session_state.quiz["percentage"] = None
                            st.session_state.quiz["evaluation"] = None
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                with st.form("quiz_form"):
                    for i, q in enumerate(quiz["questions"]):
                        st.markdown(f"<div style='margin-top: 1.5rem; font-weight: 600; color: var(--text-primary);'>Question {i+1} of {len(quiz['questions'])}</div>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size: 1.05rem; color: var(--text-primary); font-weight: 500;'>{q['question']}</p>", unsafe_allow_html=True)
                        quiz["selected_answers"][i] = st.radio(
                            f"Options for Question {i+1}:",
                            options=q["options"],
                            key=f"q_{i}",
                            index=None,
                            label_visibility="collapsed"
                        )
                        st.markdown("<hr style='border-top: 1px solid var(--border-color); margin: 1.5rem 0;'>", unsafe_allow_html=True)
                        
                    submit_quiz = st.form_submit_button("Submit Answers →", type="primary")
                    
                    if submit_quiz:
                        unanswered = [i for i, ans in quiz["selected_answers"].items() if ans is None]
                        if unanswered:
                            st.warning("Please answer all questions before submitting.")
                        else:
                            evaluation_result = evaluate_quiz(quiz["questions"], quiz["selected_answers"])
                            st.session_state.quiz["score"] = evaluation_result["score"]
                            st.session_state.quiz["percentage"] = evaluation_result["percentage"]
                            st.session_state.quiz["evaluation"] = evaluation_result
                            st.session_state.quiz["completed"] = True
                            st.session_state.active_section = "analysis"
                            
                            # Add to completed topics if passed (60% or higher)
                            if evaluation_result["percentage"] >= 60.0:
                                if topic_name not in st.session_state.completed_topics:
                                    st.session_state.completed_topics.append(topic_name)
                            st.rerun()
                            
                st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                if st.button("← Cancel & Return to Lesson", type="secondary"):
                    st.session_state.active_section = "explanation"
                    reset_quiz_state()
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                    
    elif st.session_state.active_section == "analysis":
        # ------------------ Evaluation / Analysis Page ------------------
        eval_data = quiz["evaluation"]
        
        st.markdown('<h3><i class="fa-solid fa-chart-pie" style="margin-right: 10px; color: var(--primary-color);"></i>Quiz Results</h3>', unsafe_allow_html=True)
        st.caption("Review your score, strong concepts, and areas requiring further study.")
        
        col_score, col_percent = st.columns(2)
        with col_score:
            st.metric("Total Score", f"{st.session_state.quiz['score']} / {st.session_state.quiz['size']}")
        with col_percent:
            st.metric("Percentage", f"{st.session_state.quiz['percentage']}%")
            
        st.markdown("---")
        st.markdown('<h4><i class="fa-solid fa-microscope" style="margin-right: 8px; color: var(--primary-color);"></i>Performance Summary</h4>', unsafe_allow_html=True)
        
        col_strong, col_weak = st.columns(2)
        with col_strong:
            with st.container(border=True):
                st.markdown("<h5 style='color: var(--success-color);'><i class=\"fa-solid fa-circle-check\" style=\"margin-right: 8px;\"></i>Strong Concepts</h5>", unsafe_allow_html=True)
                st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
                if eval_data["strong_areas"]:
                    for area in eval_data["strong_areas"]:
                        st.markdown(f"<div style='margin-bottom: 0.5rem; font-weight: 500;'>{area}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-style: italic;'>No strong concepts identified yet. Keep practicing!</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
        with col_weak:
            with st.container(border=True):
                st.markdown("<h5 style='color: var(--warning-color);'><i class=\"fa-solid fa-triangle-exclamation\" style=\"margin-right: 8px;\"></i>Needs Revision</h5>", unsafe_allow_html=True)
                st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
                if eval_data["weak_areas"]:
                    for area in eval_data["weak_areas"]:
                        st.markdown(f"<div style='margin-bottom: 0.5rem; font-weight: 500;'>{area}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-style: italic;'>Outstanding! No weak concepts identified.</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("---")
        st.markdown('<h4><i class="fa-solid fa-list-ol" style="margin-right: 8px; color: var(--primary-color);"></i>Question Review</h4>', unsafe_allow_html=True)
        
        for idx, res in enumerate(eval_data["detailed_results"]):
            with st.container(border=True):
                symbol_html = '<span style="color: var(--success-color); font-weight: bold;"><i class="fa-solid fa-circle-check" style="margin-right: 6px;"></i>Correct</span>' if res["is_correct"] else '<span style="color: var(--warning-color); font-weight: bold;"><i class="fa-solid fa-circle-xmark" style="margin-right: 6px;"></i>Incorrect</span>'
                st.markdown(f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 0.75rem;'><strong>Question {idx+1}</strong> {symbol_html}</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.05rem; font-weight: 500; color: var(--text-primary);'>{res['question']}</p>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='margin-bottom: 0.5rem;'><strong>Your Answer:</strong> {res['selected']}</div>", unsafe_allow_html=True)
                if not res["is_correct"]:
                    st.markdown(f"<div style='margin-bottom: 0.5rem; color: var(--success-color);'><strong>Correct Answer:</strong> {res['correct']}</div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background-color: var(--info-bg); border-left: 3px solid var(--info-color); padding: 0.75rem; border-radius: 4px; margin-top: 0.75rem;">
                    <span style="font-size: 0.85rem; font-weight: bold; color: var(--info-color); text-transform: uppercase;">Explanation</span>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.92rem;">{res['explanation']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);'><i class='fa-solid fa-tag' style='margin-right: 4px;'></i>Sub-concept: {res['sub_concept']}</div>", unsafe_allow_html=True)
            
        col_anal_l, col_anal_r = st.columns([1, 1])
        with col_anal_l:
            if st.button("Retry Assessment", key="retry_quiz", type="secondary", use_container_width=True):
                reset_quiz_state()
                st.session_state.active_section = "quiz"
                st.rerun()
        with col_anal_r:
            if st.session_state.current_topic_index < total_topics - 1:
                if st.button("Continue Learning →", key="continue_learning", type="primary", use_container_width=True):
                    st.session_state.current_topic_index += 1
                    st.session_state.active_section = "explanation"
                    reset_quiz_state()
                    st.rerun()
            else:
                st.success("🎉 You've completed the last topic in the path!")

# Auto-save session state at the end of every rerun
save_session_state()
