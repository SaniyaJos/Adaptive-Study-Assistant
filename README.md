# StudyFlow AI — Adaptive Study Assistant & Smart Tutor

StudyFlow AI is an adaptive, offline-compatible learning platform designed to extract a structured curriculum from your lecture notes (PDF format), generate customized study materials based on your objectives, offer a conversational doubt-solving tutor, and diagnose your understanding through dynamic quizzes.

---

## 🌟 Key Features

1. **Structured Learning Path**: Automatically parses your lecture notes and extracts a sequential topic-by-topic curriculum.
2. **Personalized Study Modes**:
   - **Learn Concepts**: Geared for first-time learners. Introduces concepts with examples and lists characteristics clearly.
   - **Exam Preparation**: Maximum efficiency study focusing on definitions, core concepts, and commonly tested relationships.
   - **Quick Revision**: Rapid-fire summary using short bullet points and keywords, reviewable in under 1 minute.
3. **Conversational Doubt Solver**: Ask any question about a topic. Uses Retrieval-Augmented Generation (RAG) to fetch relevant references from your uploaded notes.
4. **Concept Assessments & Diagnostics**: Generate custom-length quizzes mapping directly to notes. The diagnostic report highlights your strong concepts and identifies areas needing revision.
5. **Seamless Session Persistence**: Your state (notes context, current topic, and study progress) survives browser refreshes but automatically wipes clean when you close the browser tab.

---

## 🛠️ Technology Stack

* **Frontend & Board UI**: Streamlit
* **AI Model Engine**: Google Gemini API (`gemini-flash-lite-latest`)
* **Embedding Model**: Sentence Transformers (`all-MiniLM-L6-v2` locally hosted)
* **Vector Store**: ChromaDB (persistent local client)
* **PDF Parser**: PyMuPDF

---

## 🚀 Quick Start Guide

### 1. Clone the Project
Navigate to the directory in your terminal.

### 2. Setup a Virtual Environment (Recommended)
```bash
# Create environment
python -m venv venv

# Activate on Windows (Command Prompt):
venv\Scripts\activate

# Activate on Windows (PowerShell):
venv\Scripts\Activate.ps1

# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
Copy the `.env.example` file to a new file named `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
> ⚠️ **Note**: Never share or commit your `.env` file to version control. The `.gitignore` is already configured to ignore it.

### 5. Run the Application
```bash
streamlit run app.py
```
Open the local URL displayed in the terminal (usually `http://localhost:8501`) in your browser.

---

## 📂 Project Structure

* `app.py`: Main dashboard layout, custom styles, and core Streamlit UI router.
* `config.py`: Local directories, embedding models, and Gemini model options.
* `requirements.txt`: Package dependencies list.
* `services/`:
  - `gemini_service.py`: Gemini client helper with caching and model configuration.
  - `tutor_engine.py`: Dynamic lesson generator with personalized prompts.
  - `doubt_solver.py`: RAG doubt resolver.
  - `quiz_generator.py`: Assessment generator and diagnostics parser.
  - `topic_extractor.py`: Curriculum extraction service.
* `utils/`:
  - `pdf_processor.py`: Text extractor and text-chunking tools.
  - `session_state.py`: Session initialization and JSON serialization handlers.
  - `vector_store.py`: ChromaDB connector.
