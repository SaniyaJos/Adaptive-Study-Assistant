from typing import List, Dict
from services.gemini_service import generate_response

def solve_doubt(query: str, topic_name: str, chat_history: List[Dict[str, str]]) -> str:
    """
    Answers a student's doubt about a specific topic using RAG from ChromaDB
    and preserving the chat history context.
    """
    from utils.vector_store import query_relevant_chunks

    search_query = f"{topic_name}: {query}"
    relevant_chunks = query_relevant_chunks(query=search_query, top_k=5)
    context_text = "\n\n".join(relevant_chunks) if relevant_chunks else "No source notes available."
    
    history_context = ""
    if chat_history:
        history_context = "Here is the conversation history on this topic so far:\n"
        for msg in chat_history[-6:]:  # Limit history context to the last 6 messages
            role_name = "Student" if msg["role"] == "user" else "Tutor"
            history_context += f"- {role_name}: {msg['content']}\n"
        history_context += "\n"
        
    system_instruction = (
        "You are StudyFlow AI, an expert, patient, and engaging academic tutor. "
        "Your task is to answer the student's doubt about the active topic. "
        "Use the provided context from the student's notes as your primary source of truth.\n\n"
        "Instructions:\n"
        "- Respond in a clear, pedagogical tone. Use analogies or examples if it helps clarify.\n"
        "- Base your answer strictly on the provided text chunks. Do not answer questions that are unrelated to the notes.\n"
        "- If the answer cannot be found or inferred from the notes context, or if the question is unrelated to the notes, "
        "do not attempt to answer using general knowledge. Instead, state exactly: "
        "'It is not possible to answer this question as it is unrelated to your uploaded notes.'\n"
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

