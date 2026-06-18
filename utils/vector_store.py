import os
import chromadb
from chromadb.api.types import Documents, Embeddings
from typing import List
import config
from services.gemini_service import configure_gemini

_query_cache = {}

class GoogleEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom ChromaDB EmbeddingFunction to generate embeddings using Google's Gemini API.
    """
    def __init__(self, model_name: str = config.EMBEDDING_MODEL_NAME):
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        import google.generativeai as genai
        # Ensure Gemini is configured
        configure_gemini()
        try:
            # Generate embeddings using Google's text-embedding-004 model
            result = genai.embed_content(
                model=self.model_name,
                content=input,
                task_type="retrieval_document"
            )
            embeddings = result.get("embedding", [])
            if len(input) > 0 and len(embeddings) > 0 and not isinstance(embeddings[0], list):
                embeddings = [embeddings]
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to generate Google embeddings: {e}")

# Global variable to cache the embedding function singleton
_embedding_fn = None

def get_embedding_function() -> GoogleEmbeddingFunction:
    """
    Lazy-loads and returns the singleton GoogleEmbeddingFunction instance.
    """
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = GoogleEmbeddingFunction()
    return _embedding_fn

def get_chroma_collection():
    """
    Initializes a persistent ChromaDB client and returns the collection.
    """
    # Ensure Chroma persistence directory exists
    os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
    
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    embedding_fn = get_embedding_function()
    
    collection = client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    return collection

def index_pdf_chunks(chunks: List[str]):
    """
    Clears the current collection and indexes a new list of text chunks.
    
    Args:
        chunks: List of string chunks to store in ChromaDB.
    """
    # Initialize persistent client to delete the collection if it already exists
    # to avoid dimension conflicts (e.g. switching from local 384 dimensions to cloud 3072 dimensions)
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    try:
        client.delete_collection(name=config.CHROMA_COLLECTION_NAME)
    except Exception:
        pass
        
    collection = get_chroma_collection()
    
    # 2. Add new chunks to the collection
    if not chunks:
        return
        
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_idx": i} for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )
    _query_cache.clear()


def clear_query_cache():
    """Clears cached similarity lookups when the underlying collection changes."""
    _query_cache.clear()

def query_relevant_chunks(query: str, top_k: int = 4) -> List[str]:
    """
    Queries ChromaDB for the most relevant text chunks matching the query.
    
    Args:
        query: The search query text (e.g. user doubt).
        top_k: Number of relevant chunks to retrieve.
        
    Returns:
        List[str]: The text content of the matching chunks, ordered by similarity.
    """
    if not query.strip():
        return []

    cache_key = (query.strip(), top_k)
    if cache_key in _query_cache:
        return _query_cache[cache_key]
        
    collection = get_chroma_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    # Extract list of matched text documents
    if results and "documents" in results and results["documents"]:
        _query_cache[cache_key] = results["documents"][0]
        return _query_cache[cache_key]
        
    _query_cache[cache_key] = []
    return []
