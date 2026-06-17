import json
import re
from typing import Dict, Any
from services.gemini_service import generate_response

def generate_topic_lesson(topic_name: str, study_mode: str) -> Dict[str, Any]:
    """
    Retrieves relevant note chunks for the specified topic and generates a
    highly structured lesson lesson tailored to the selected study mode.
    
    Args:
        topic_name: Name of the topic/concept.
        study_mode: The active study mode ("Learn Concepts", "Exam Preparation", "Quick Revision").
        
    Returns:
        Dict: A structured lesson dictionary containing:
              - "explanation": str
              - "key_points": List[str]
              - "exam_focus": List[str]
              - "quick_recall": str
    """
    from utils.vector_store import query_relevant_chunks

    # 1. Retrieve the most relevant source note context from ChromaDB
    relevant_chunks = query_relevant_chunks(query=topic_name, top_k=6)
    context_text = "\n\n".join(relevant_chunks) if relevant_chunks else "No source notes available."
    
    # 2. Setup the custom AI tutor system instructions
    system_instruction = """You are StudyFlow AI, an excellent tutor.

Your goal is to teach the topic quickly, clearly, and engagingly.

GLOBAL FORMATTING RULES (Apply strictly to all fields, especially "explanation"):
- Never generate large walls of text.
- Keep paragraphs under 4 lines.
- Prefer bullets for lists of concepts, features, steps, advantages, or characteristics.
- Use whitespace generously.
- Make content extremely easy to scan.
- Students should understand the structure within a few seconds of opening the page.

Core Rules:
1. Preserve all important concepts, definitions, mechanisms, relationships, and exam-relevant information from the provided notes.
2. Remove repetition, textbook wording, filler explanations, and unnecessary details.
3. Explain the topic as if you are helping a friend understand it before an exam.
4. Do NOT copy the notes structure.
5. Merge related concepts together whenever possible.
6. Keep explanations concise but complete.
7. Focus on understanding first, memorization second.
8. Use simple, clear language.
9. Every sentence should provide useful information.
10. Avoid long introductions and conclusions.

Output ONLY valid JSON matching this schema:
{
  "explanation": "Markdown string containing the main explanation. Follow all formatting rules: short paragraphs (<4 lines), bullet lists, and clear headers where applicable.",
  "key_points": [
    "Most important point (under 1-2 lines)",
    "Most important point",
    "Most important point"
  ],
  "exam_focus": [
    "Important exam point/question style",
    "Frequently tested area",
    "Common comparison or key definition"
  ],
  "quick_recall": "One-line revision summary of the entire topic."
}"""
    
    # Adjust explanation behavior based on the study mode
    if study_mode == "Exam Preparation":
        prompt_focus = """Teach this topic for exam preparation.
Goal: "I may be seeing this for the first time, but I need to understand it quickly and score marks."
This is the most important mode. Assume the student has limited time.

Focus on:
- core concepts
- important definitions
- commonly tested ideas
- relationships between concepts

Presentation Style:
- Maximum 2-3 short paragraphs in "explanation".
- Use bullets heavily.
- Highlight important terms naturally (e.g. using bold text **like this**).
- Remove unnecessary theory.
- Keep only information useful for understanding and answering exam questions.
- The student should be able to understand the topic within a few minutes. Do not create another chapter of notes."""
    elif study_mode == "Quick Revision":
        prompt_focus = """Create a rapid revision guide.
Goal: "Exam is tomorrow or in a few hours." Assume the student wants to refresh the topic quickly. Focus on recall rather than teaching.

Presentation Style:
- Extremely concise.
- Prefer bullets over paragraphs.
- Use keywords and short explanations.
- Include only the most important concepts.
- Remove all non-essential details.
- The entire topic should be reviewable in under one minute."""
    else:  # "Learn Concepts"
        prompt_focus = """Teach this topic to a student encountering it for the first time.
Goal: "I'm learning this for the first time." The student should finish this section feeling: "I genuinely understand this concept."

Presentation Style:
- Start with a clear explanation of what the concept is.
- Explain why it is important.
- Use short paragraphs.
- Use bullets when listing features, advantages, steps, or characteristics.
- Use examples whenever they improve understanding.
- Avoid long walls of text.
- Keep explanations engaging but concise."""
        
    prompt = (
        f"Topic to explain: '{topic_name}'\n"
        f"Active Study Mode: {study_mode}\n\n"
        f"{prompt_focus}\n\n"
        f"Here is the context extracted from the student's study notes:\n"
        f"--- CONTEXT START ---\n"
        f"{context_text}\n"
        f"--- CONTEXT END ---\n\n"
        f"Draft the structured lesson JSON now:"
    )
    
    try:
        response_text = generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=True
        )
        
        # Clean markdown formatting wraps if any
        clean_json = response_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
            clean_json = re.sub(r"\n```$", "", clean_json)
            clean_json = clean_json.strip()
            
        lesson_data = json.loads(clean_json)
        
        # Ensure all keys exist
        default_keys = {
            "explanation": "",
            "key_points": [],
            "exam_focus": [],
            "quick_recall": ""
        }
        for k, default_val in default_keys.items():
            if k not in lesson_data:
                lesson_data[k] = default_val
                
        return lesson_data
        
    except Exception as e:
        print(f"Error generating or parsing lesson JSON: {e}")
        
    # Robust fallback dictionary in case of API or JSON failures
    return {
        "explanation": f"Welcome to the lesson on **{topic_name}**. We retrieved your notes, but could not connect to the explanation engine.",
        "key_points": [
            "Please verify your Gemini API key in the sidebar.",
            "Make sure your internet connection is active."
        ],
        "exam_focus": [
            "Expect questions asking you to compare this concept with related terms."
        ],
        "quick_recall": f"Quick review of {topic_name}: Please configure API access.",
        "is_fallback": True
    }
