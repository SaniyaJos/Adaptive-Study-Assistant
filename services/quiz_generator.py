import json
import re
import random
from typing import List, Dict, Any
from services.gemini_service import generate_response

def generate_quiz(topic_name: str, size: int = 5) -> List[Dict[str, Any]]:
    """
    Dynamically generates a quiz based on the specified topic and size.
    
    Args:
        topic_name: Name of the topic (e.g., "Paging").
        size: Number of questions (3, 5, or 10).
        
    Returns:
        List[Dict[str, Any]]: List of question dictionaries.
    """
    from utils.vector_store import query_relevant_chunks

    # 1. Fetch relevant note chunks from vector database
    relevant_chunks = query_relevant_chunks(query=topic_name, top_k=5)
    context_text = "\n\n".join(relevant_chunks) if relevant_chunks else "No source notes available."
    
    # 2. Setup the custom quiz constructor prompt
    system_instruction = (
        "You are StudyFlow AI, an expert exam designer and academic tutor. "
        "Your task is to generate a multiple-choice quiz based ONLY on the provided notes context. "
        "Do not use general external knowledge or test concepts not present in the notes.\n\n"
        "You must respond ONLY with a valid JSON array of objects, where each object matches this schema exactly:\n"
        "{\n"
        '  "question": "The question text, testing a specific concept.",\n'
        '  "options": [\n'
        '    "Distractor option 1",\n'
        '    "Correct answer option",\n'
        '    "Distractor option 2",\n'
        '    "Distractor option 3"\n'
        '  ],\n'
        '  "correct_answer": "The correct answer option (must match one of the elements in the options array exactly).",\n'
        '  "explanation": "A short, clear explanation of why this answer is correct according to the notes.",\n'
        '  "sub_concept": "The specific granular sub-concept being tested (e.g. \'Internal Fragmentation\', \'Page Table Entry\')."\n'
        "}\n\n"
        "Ensure options are randomly ordered so the correct answer is not always in the same position. "
        "Do not include markdown wraps."
    )
    
    prompt = (
        f"Generate a quiz on the topic: '{topic_name}'\n"
        f"Number of questions requested: {size}\n\n"
        f"Use the following notes context as the sole source of truth for the questions:\n"
        f"--- CONTEXT START ---\n"
        f"{context_text}\n"
        f"--- CONTEXT END ---\n\n"
        f"Generate the JSON array of {size} quiz questions now:"
    )
    
    try:
        response_text = generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=True
        )
        
        # Clean markdown wrappers if returned
        clean_json = response_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
            clean_json = re.sub(r"\n```$", "", clean_json)
            clean_json = clean_json.strip()
            
        questions = json.loads(clean_json)
        
        if isinstance(questions, list):
            # Shuffle options and validate each question structure
            validated_questions = []
            for q in questions[:size]:
                if all(k in q for k in ["question", "options", "correct_answer", "explanation", "sub_concept"]):
                    # Ensure options has exactly 4 items and contains correct_answer
                    opts = list(q["options"])
                    correct = q["correct_answer"]
                    if correct not in opts:
                        opts.append(correct)
                    # Deduplicate options
                    opts = list(dict.fromkeys(opts))
                    while len(opts) < 4:
                        opts.append(f"Incorrect fallback distractor {len(opts)}")
                    opts = opts[:4]
                    # Make sure the correct answer is still in there
                    if correct not in opts:
                        opts[0] = correct
                    random.shuffle(opts)
                    
                    validated_questions.append({
                        "question": q["question"],
                        "options": opts,
                        "correct_answer": correct,
                        "explanation": q["explanation"],
                        "sub_concept": q["sub_concept"].strip()
                    })
            return validated_questions
            
    except Exception as e:
        print(f"Error generating quiz JSON: {e}")
        
    # Standby fallback quiz questions in case of JSON parse or API failure
    fallback_opts = ["Option A", "Option B", "Option C", "Option D"]
    return [
        {
            "question": f"Which of the following is a key component of {topic_name}?",
            "options": fallback_opts,
            "correct_answer": "Option A",
            "explanation": "Option A is the correct answer based on standard course material.",
            "sub_concept": "General Concepts"
        }
    ]

def evaluate_quiz(questions: List[Dict[str, Any]], selected_answers: Dict[int, str]) -> Dict[str, Any]:
    """
    Evaluates the student's answers, calculates scores, and diagnoses strong/weak sub-concepts.
    
    Args:
        questions: List of question dicts generated by generate_quiz.
        selected_answers: Dict mapping question index (int) -> selected option string (str).
        
    Returns:
        Dict containing score, percentage, strong_areas, weak_areas, and detailed results list.
    """
    score = 0
    detailed_results = []
    
    # Track performance on granular sub-concepts
    sub_concept_stats = {}  # sub_concept -> {"correct": int, "total": int}
    
    for idx, q in enumerate(questions):
        user_ans = selected_answers.get(idx, "")
        correct_ans = q["correct_answer"]
        is_correct = (user_ans == correct_ans)
        
        if is_correct:
            score += 1
            
        sub_c = q["sub_concept"]
        if sub_c not in sub_concept_stats:
            sub_concept_stats[sub_c] = {"correct": 0, "total": 0}
        sub_concept_stats[sub_c]["total"] += 1
        if is_correct:
            sub_concept_stats[sub_c]["correct"] += 1
            
        detailed_results.append({
            "question": q["question"],
            "selected": user_ans if user_ans else "Unanswered",
            "correct": correct_ans,
            "is_correct": is_correct,
            "explanation": q["explanation"],
            "sub_concept": sub_c
        })
        
    total_questions = len(questions)
    percentage = (score / total_questions * 100) if total_questions > 0 else 0.0
    
    strong_areas = []
    weak_areas = []
    
    # Categorize sub-concepts based on success rates
    for sub_c, stats in sub_concept_stats.items():
        success_rate = stats["correct"] / stats["total"]
        if success_rate >= 0.8:
            strong_areas.append(sub_c)
        else:
            weak_areas.append(sub_c)
            
    return {
        "score": score,
        "total": total_questions,
        "percentage": round(percentage, 1),
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "detailed_results": detailed_results
    }
