from typing import List, Dict
from services.gemini_service import generate_response

def solve_doubt(query: str, topic_name: str, chat_history: List[Dict[str, str]]) -> str:
    """
    Answers a student's doubt about a specific topic using RAG from ChromaDB
    and preserving the chat history context.
    
    Args:
        query: The student's question/doubt.
        topic_name: The current active topic/concept.
        chat_history: List of prior messages: [{"role": "user"|"assistant", "content": str}]
        
    Returns:
        str: The AI tutor's response in markdown.
    """
    from utils.vector_store import query_relevant_chunks

    # 1. Retrieve notes context from ChromaDB using a combination of the topic and the query
    search_query = f"{topic_name}: {query}"
    relevant_chunks = query_relevant_chunks(query=search_query, top_k=5)
    context_text = "\n\n".join(relevant_chunks) if relevant_chunks else "No source notes available."
    
    # 2. Format the chat history for conversational continuity
    history_context = ""
    if chat_history:
        history_context = "Here is the conversation history on this topic so far:\n"
        for msg in chat_history[-6:]:  # Limit history context to the last 6 messages
            role_name = "Student" if msg["role"] == "user" else "Tutor"
            history_context += f"- {role_name}: {msg['content']}\n"
        history_context += "\n"
        
    # 3. Setup prompt instructions
    system_instruction = (
        "You are StudyFlow AI, an expert, patient, and engaging academic tutor. "
        "Your task is to answer the student's doubt about the active topic. "
        "Use the provided context from the student's notes as your primary source of truth.\n\n"
        "Instructions:\n"
        "- Respond in a clear, pedagogical tone. Use analogies or examples if it helps clarify.\n"
        "- Base your answer on the provided text chunks whenever possible.\n"
        "- If the answer cannot be found or inferred from the notes context, answer the query "
        "accurately using your general knowledge, but begin your answer by saying: "
        "'[Supplementing your notes]: ' so the student knows this information wasn't in their uploaded PDF.\n"
        "- Keep answers clear, structured, and easy to read. Use formatting like bold terms, bullet lists, "
        "or small tables where helpful.\n"
        "- Do not make up facts or equations."
    )
    
    prompt = (
        f"Active Topic: {topic_name}\n"
        f"Student's Doubt: {query}\n\n"
        f"{history_context}"
        f"Here is the context extracted from the student's study notes:\n"
        f"--- CONTEXT START ---\n"
        f"{context_text}\n"
        f"--- CONTEXT END ---\n\n"
        f"Draft your helpful answer to the doubt:"
    )
    
    try:
        response_text = generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=False
        )
        return response_text
        
    except Exception as e:
        return f"Sorry, I encountered an error answering your question: {e}. Please check your API key or try again."
