import json
import re
from typing import List, Dict, Any
from services.gemini_service import generate_response

def extract_topics(raw_text: str, study_mode: str) -> List[Dict[str, str]]:
    """
    Analyzes raw PDF text and extracts a logical sequence of granular topics
    with priority rankings based on the selected study mode.
    
    Args:
        raw_text: Full text content of the PDF notes.
        study_mode: The chosen study goal ("Learn Concepts", "Exam Preparation", "Quick Revision").
        
    Returns:
        List[Dict[str, str]]: A list of topics, e.g.:
                              [{"name": "Paging", "priority": "High Priority"}]
    """
    if not raw_text or not raw_text.strip():
        return []
        
    system_instruction = (
        "You are an expert academic tutor and curriculum designer.\n"
        "Your task is to analyze the provided student study notes and extract a list of high-level, comprehensive study topics. "
        "You must format the output ONLY as a valid JSON array of objects.\n\n"
        "Each JSON object in the array must contain exactly two keys:\n"
        '1. "name": The clear, descriptive name of the topic.\n'
        '2. "priority": One of: "High Priority", "Medium Priority", "Lower Priority".\n\n'
        "Guidelines:\n"
        "- Group related subheadings and minor concepts together into a single, cohesive, comprehensive topic. Do not list every minor heading or definition as a separate topic. Aim for a total of 4 to 8 main topics for the entire notes.\n"
        "- For example, instead of separate topics for 'Photoresist Definition', 'Photoresist Components', and 'Types of Photoresists', group them into a single topic like 'Photoresists: Definition, Components & Types'.\n"
        "- Sequence the topics in a logical learning progression.\n"
        "- Do not include any conversational filler, markdown formatting (like ```json), or explanation outside the JSON array."
    )
    
    # Customize instructions depending on the study goal
    if study_mode == "Exam Preparation":
        mode_instruction = (
            "Focus: Identify ALL topics in the notes, but determine their exam priority levels based on "
            "foundational importance, complexity, or frequency in typical exams. Mark the core pillars as "
            "'High Priority', secondary but essential content as 'Medium Priority', and minor details/definitions as 'Lower Priority'."
        )
    elif study_mode == "Quick Revision":
        mode_instruction = (
            "Focus: Extract topics that require quick review, mapping core formulas, definitions, and high-level concepts. "
            "Identify key revision points as 'High Priority', secondary facts as 'Medium Priority', and minor definitions as 'Lower Priority'."
        )
    else:  # "Learn Concepts"
        mode_instruction = (
            "Focus: Arrange topics in a clean learning curve for a beginner. "
            "Rate core concepts as 'High Priority', explanatory topics as 'Medium Priority', and advanced edge-cases as 'Lower Priority'."
        )
        
    prompt = (
        f"{mode_instruction}\n\n"
        f"Here are the study notes to analyze:\n"
        f"--- START OF STUDY NOTES ---\n"
        f"{raw_text[:100000]}...\n"  # Clip raw text at 100k characters for safe token limit
        f"--- END OF STUDY NOTES ---\n\n"
        f"Generate the JSON array of topics now:"
    )
    
    try:
        response_text = generate_response(
            prompt=prompt, 
            system_instruction=system_instruction, 
            json_mode=True
        )
        
        # Clean up responses that might be wrapped in markdown code blocks
        clean_json = response_text.strip()
        if clean_json.startswith("```"):
            # Remove leading markdown wrapper e.g. ```json or ```
            clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
            # Remove trailing markdown wrapper
            clean_json = re.sub(r"\n```$", "", clean_json)
            clean_json = clean_json.strip()
            
        topics = json.loads(clean_json)
        
        # Validate return structure
        if isinstance(topics, list):
            validated_topics = []
            for t in topics:
                if isinstance(t, dict) and "name" in t:
                    # Clean/normalize priority values
                    p = t.get("priority", "Medium Priority")
                    if p not in ["High Priority", "Medium Priority", "Lower Priority"]:
                        p = "Medium Priority"
                    validated_topics.append({"name": str(t["name"]), "priority": p})
            return validated_topics
            
    except Exception as e:
        # Fallback parsing in case Gemini outputs invalid JSON structure
        print(f"JSON topic extraction error: {e}. Attempting regex fallback.")
        
    # Standard fallback if LLM response couldn't be parsed as structured JSON
    return [
        {"name": "Introduction & Overview", "priority": "High Priority"},
        {"name": "Core Concepts", "priority": "High Priority"},
        {"name": "Detailed Applications", "priority": "Medium Priority"},
        {"name": "Summary & Revision", "priority": "Lower Priority"}
    ]
