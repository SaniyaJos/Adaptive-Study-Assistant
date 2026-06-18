import json
import re
from typing import Dict, Any, List, Optional
from services.gemini_service import generate_response

def generate_topic_lesson(topic_name: str, study_mode: str, other_topics: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Retrieves relevant note chunks for the specified topic and generates a
    highly structured lesson lesson tailored to the selected study mode.
    
    Args:
        topic_name: Name of the topic/concept.
        study_mode: The active study mode ("Learn Concepts", "Exam Preparation", "Quick Revision").
        other_topics: Optional list of other topics in the curriculum to avoid repetition.
        
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
    
    # Construct details about other topics to avoid repetition
    avoid_instruction = ""
    if other_topics:
        valid_others = [t for t in other_topics if t and t.strip()]
        if valid_others:
            avoid_instruction = (
                "\nCRITICAL TOPIC FOCUS RULES:\n"
                "The student has already completed (or will separately study) the following topics in this notes curriculum:\n"
                + "\n".join(f"- {t}" for t in valid_others) + "\n"
                + f"Do NOT explain, define, or list any general definitions, terms, or mechanisms that belong to those other topics. "
                f"For example, do NOT define basic terms like 'Process' or 'Thread' if the current topic is a specific sub-topic (like 'Thread Attributes' or 'Applications of Multithreading'). "
                f"Focus ONLY and EXCLUSIVELY on the concepts, subtopics, attributes, and mechanisms that are unique to the current topic '{topic_name}'."
            )
    
    # Customize system instruction and prompts dynamically based on study_mode
    if study_mode == "Learn Concepts":
        system_instruction = f"""You are StudyFlow AI, an excellent, friendly academic tutor.
Your goal is to thoroughly explain the topic to a student encountering it for the first time, ensuring they build a deep, intuitive understanding.

RULES FOR "Learn Concepts" MODE:
- Focus STRICTLY on the requested topic: '{topic_name}'. Do NOT re-explain basic definitions or concepts from other chapters/lessons that the student has studied or will study separately.
{avoid_instruction}
- Start with a clear, friendly definition of the topic.
- Explain the underlying intuition: why this concept exists and what problem it solves.
- Break down how it works step-by-step using clear headings.
- Provide a relatable, real-world analogy to make the abstract concept concrete.
- Include detailed explanations of the mechanisms rather than just listing them.
- Use a warm, encouraging, and engaging tone.
- Use markdown formatting (bolding, lists, headers) to make the rich explanation highly readable. Do not worry about keeping paragraphs under 4 lines, but make sure they are clear and well-spaced.

Output ONLY valid JSON matching this schema:
{{
  "explanation": "Detailed, thorough explanation starting with definition, intuition, step-by-step mechanism breakdown, and an intuitive analogy. Make it rich, friendly, and complete.",
  "key_points": [
    "Core takeaway definition/concept",
    "Crucial explanation point",
    "Why this concept is fundamental"
  ],
  "exam_focus": [
    "How this concept forms the foundation for other topics",
    "Key question style testing basic comprehension"
  ],
  "quick_recall": "A clear, intuitive summary sentence summarizing the core analogy/concept."
}}"""
        prompt_focus = f"""Thoroughly teach the topic '{topic_name}' to a beginner.
Goal: The student should finish this section feeling: "I genuinely understand this concept."

Make sure to cover:
- What the concept is (clear definition).
- Why it is important (the core problem it solves).
- A detailed step-by-step explanation of how it works.
- A friendly, concrete analogy (e.g. relating it to everyday life).
- Explain all subtopics and mechanisms in detail.
{avoid_instruction}"""

    elif study_mode == "Exam Preparation":
        system_instruction = f"""You are StudyFlow AI, a focused exam coach.
Your goal is to help the student master the topic specifically for exams. Assume they have limited time and need to maximize their marks.

RULES FOR "Exam Preparation" MODE:
- Focus STRICTLY on the requested topic: '{topic_name}'. Do NOT re-explain basic definitions or concepts from other chapters/lessons that the student has studied or will study separately.
{avoid_instruction}
- Keep paragraphs short (under 4 lines) and highly focused.
- Focus heavily on core concepts, precise definitions, and key comparisons.
- Use bold text frequently for critical terms, formulas, and definitions.
- Organize content with clean subheadings and bullet lists for scannability.
- Highlight potential exam pitfalls and common mistakes.
- Exclude unnecessary background history, fluff, or casual analogies.

Output ONLY valid JSON matching this schema:
{{
  "explanation": "Highly structured, mark-focused explanation highlighting core formulas/definitions. Use bolding and short, punchy paragraphs (<4 lines) to make points stand out.",
  "key_points": [
    "Key definition/formula likely to be tested",
    "Critical relationship or comparison",
    "Crucial technical constraint or mechanism"
  ],
  "exam_focus": [
    "Frequently tested exam questions (e.g. Compare X vs Y)",
    "Points to include to get full marks",
    "Common examiner tricks or mistakes to avoid"
  ],
  "quick_recall": "A punchy, one-line summary focusing on definitions or core relationships."
}}"""
        prompt_focus = f"""Explain the topic '{topic_name}' for exam preparation.
Goal: "I may be seeing this for the first time, but I need to understand it quickly and score marks."

Focus on:
- Core concepts and precise definitions.
- Commonly tested ideas and relations.
- Keep the explanation highly targeted, with 2-3 short, focused paragraphs (<4 lines each).
- Highlight key terms in bold.
{avoid_instruction}"""

    else:  # "Quick Revision"
        system_instruction = f"""You are StudyFlow AI, a rapid-review assistant.
Your goal is to create a dense, highly scannable cheat sheet for last-minute revision.

RULES FOR "Quick Revision" MODE:
- Focus STRICTLY on the requested topic: '{topic_name}'. Do NOT re-explain basic definitions or concepts from other chapters/lessons that the student has studied or will study separately.
{avoid_instruction}
- Do NOT write paragraphs. Use ONLY bullet points, short lists, and bolded keywords.
- TOUCH EVERY SINGLE SUBTOPIC, term, and mechanism found in the provided notes context THAT IS UNIQUE to '{topic_name}'. Do NOT list general background terms or concepts belonging to other topics.
- For each subtopic/term, write a 1-sentence definition or summary highlighting key inputs/outputs or roles.
- The style must be extremely condensed so the user can review all subtopics in under one minute.
- Zero explanation, zero analogies, zero introductory or concluding sentences.

Output ONLY valid JSON matching this schema:
{{
  "explanation": "A bulleted cheat sheet covering all subtopics, terms, and mechanisms in the context. Format as:\n- **Subtopic/Term A**: Ultra-short 1-sentence revision summary.\n- **Subtopic/Term B**: Ultra-short 1-sentence revision summary.",
  "key_points": [
    "Critical keyword/fact 1",
    "Critical keyword/fact 2",
    "Critical formula/constant"
  ],
  "exam_focus": [
    "Quick question/answer pair or formula recall tip"
  ],
  "quick_recall": "A dense list of keywords separated by commas."
}}"""
        prompt_focus = f"""Create a rapid revision guide for '{topic_name}'.
Goal: "Exam is tomorrow or in a few hours." Focus on recall rather than teaching.

Requirements:
- List and cover EVERY single subtopic, definition, term, and mechanism present in the context below that is unique to '{topic_name}'.
- Do not write any paragraphs. Write only bullet points where each bullet is: '**Term/Subtopic**: [1-sentence summary/role]'.
- Extremely concise, zero fluff.
{avoid_instruction}"""

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
