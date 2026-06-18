import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-flash-lite-latest"

EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
CHROMA_COLLECTION_NAME = "studyflow_notes"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

