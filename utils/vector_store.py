import os
import chromadb
from chromadb.api.types import Documents, Embeddings
from sentence_transformers import SentenceTransformer
from typing import List
import config

_query_cache = {}

class LocalEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom ChromaDB EmbeddingFunction to generate embeddings locally using Sentence Transformers.
    """
    def __init__(self, model_name: str = config.EMBEDDING_MODEL_NAME):
        # Load the SentenceTransformer model (cached in memory)
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        # Convert documents to local embeddings and return them as a list of lists (floats)
        embeddings = self.model.encode(input).tolist()
        return embeddings

# Global variable to cache the embedding function singleton
_embedding_fn = None

def get_embedding_function() -> LocalEmbeddingFunction:
    """
    Lazy-loads and returns the singleton LocalEmbeddingFunction instance to avoid
    re-instantiating the SentenceTransformer model.
    """
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = LocalEmbeddingFunction()
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
    collection = get_chroma_collection()
    
    # 1. Clear any existing documents in the collection
    existing_docs = collection.get()
    if existing_docs and existing_docs["ids"]:
        collection.delete(ids=existing_docs["ids"])
        
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
