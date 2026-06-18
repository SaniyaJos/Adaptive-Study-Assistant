import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini API Configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-flash-lite-latest"

# Embedding & Vector Database Configurations
EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
CHROMA_COLLECTION_NAME = "studyflow_notes"

# Text Processing Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
