import streamlit as st
import json
import os
import uuid

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")

def get_session_id() -> str:
    """Gets or generates a unique session ID from the query parameters."""
    if "session_id" in st.query_params:
        return st.query_params["session_id"]
    else:
        session_id = uuid.uuid4().hex
        st.query_params["session_id"] = session_id
        return session_id

def get_state_file_path() -> str:
    """Gets the path to the JSON session file, ensuring the directory exists."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    return os.path.join(SESSIONS_DIR, f"{get_session_id()}.json")

def save_session_state():
    """Serializes and saves the current state to the session-specific JSON file."""
    state_keys = [
        "pdf_raw_text",
        "processed_chunks",
        "pdf_metadata",
        "study_mode",
        "topics",
        "current_topic_index",
        "completed_topics",
        "active_section",
        "explanations",
        "doubt_history",
        "quiz"
    ]
    data = {}
    for key in state_keys:
        if key in st.session_state:
            data[key] = st.session_state[key]
    try:
        with open(get_state_file_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving session state: {e}")

def load_session_state() -> bool:
    """Loads state from the session-specific JSON file into st.session_state."""
    filepath = get_state_file_path()
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, val in data.items():
            st.session_state[key] = val
        return True
    except Exception as e:
        print(f"Error loading session state: {e}")
        return False

def clear_saved_session_state():
    """Deletes the current session file and removes the session_id from query parameters."""
    filepath = get_state_file_path()
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error removing session state file: {e}")
    if "session_id" in st.query_params:
        del st.query_params["session_id"]

def init_session_state():
    """
    Initializes all required keys in st.session_state if they do not already exist.
    This ensures state persistence across Streamlit page reruns.
    """
    # Only load from saved state file on the very first run of the session
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        if load_session_state():
            return
    # 1. Document Loading & Processing State
    if "pdf_raw_text" not in st.session_state:
        st.session_state.pdf_raw_text = None
    if "processed_chunks" not in st.session_state:
        st.session_state.processed_chunks = []
    if "pdf_metadata" not in st.session_state:
        st.session_state.pdf_metadata = {}  # E.g., page_count, char_count, file_name
    
    # 2. Study Goal & Learning Path Navigation
    if "study_mode" not in st.session_state:
        st.session_state.study_mode = "Learn Concepts"  # "Learn Concepts" | "Exam Preparation" | "Quick Revision"
    if "topics" not in st.session_state:
        st.session_state.topics = []  # List of dicts: {"name": str, "priority": str}
    if "current_topic_index" not in st.session_state:
        st.session_state.current_topic_index = 0
    if "completed_topics" not in st.session_state:
        st.session_state.completed_topics = []  # List of topic names that have been completed (quiz passed)
    if "active_section" not in st.session_state:
        st.session_state.active_section = "explanation"  # "explanation" | "quiz" | "analysis"
        
    # 3. Topic Explanations Cache (to avoid re-querying Gemini for the same topic/mode)
    if "explanations" not in st.session_state:
        st.session_state.explanations = {}  # Maps "topic_name_study_mode" -> dict of parsed sections
        
    # 4. Doubt Solving Chat History
    if "doubt_history" not in st.session_state:
        st.session_state.doubt_history = {}  # Maps topic name -> list of dicts: {"role": "user"|"assistant", "content": str}
        
    # 5. Dynamic Quiz State
    if "quiz" not in st.session_state:
        st.session_state.quiz = {
            "questions": [],            # List of quiz question dicts
            "current_question_idx": 0,  # Active question index
            "selected_answers": {},     # Maps question index -> selected option (str)
            "score": None,              # Final score (int)
            "percentage": None,         # Final percentage (float)
            "evaluation": None,         # Evaluation dict (strong areas, weak areas, revision tips)
            "completed": False,         # Whether quiz has been submitted
            "size": 5                   # Quiz length (3, 5, or 10)
        }


def reset_document_state():
    """
    Clears all document-specific states when a new PDF is uploaded.
    """
    st.session_state.pdf_raw_text = None
    st.session_state.processed_chunks = []
    st.session_state.pdf_metadata = {}
    st.session_state.topics = []
    st.session_state.completed_topics = []
    st.session_state.current_topic_index = 0
    st.session_state.active_section = "explanation"
    st.session_state.explanations = {}
    st.session_state.doubt_history = {}
    reset_quiz_state()
    clear_saved_session_state()

def reset_quiz_state():
    """
    Clears active quiz questions and options for a topic retry.
    """
    st.session_state.quiz = {
        "questions": [],
        "current_question_idx": 0,
        "selected_answers": {},
        "score": None,
        "percentage": None,
        "evaluation": None,
        "completed": False,
        "size": st.session_state.quiz.get("size", 5)
    }
