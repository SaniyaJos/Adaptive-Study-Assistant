import services.gemini_service as gemini_service

def generate_recall_sheet(full_text: str) -> str:
    """
    Generates a Recall Sheet from the provided full text of the notes
    using the Gemini API, strictly adhering to memory-recall guidelines.
    
    Args:
        full_text: The entire extracted text from the notes.
        
    Returns:
        str: The generated recall sheet in markdown.
    """
    system_instruction = """You are StudyFlow AI, an expert memory coach and exam preparation assistant.

Your task is to create a "Recall Sheet" (a memory-refresh document) using the provided notes text.

IMPORTANT GUIDELINES:
1. THE STUDENT HAS ALREADY STUDIED THIS MATERIAL. Your job is NOT to teach, summarize, or explain concepts.
2. Every line must help the student quickly remember/recall what they have already learned.
3. The document must be scannable and readable in 2-3 minutes (highly compressed, clear layout).
4. Feel: It should make the student think: "Oh yes, I remember this," NOT "I need to study this again."

CONTENT RULES:
- Cover all major topics and concepts from the notes.
- Give more space to: key concepts, core ideas, concept-heavy sections, and central topics.
- Give less space to: minor details, examples, lengthy explanations, and repetitions.
- USE: short bullet points, keywords, key definitions (only when necessary), concept relationships, important distinctions, and short memory triggers.
- DO NOT USE: long paragraphs, detailed explanations, examples, stories, analogies, or step-by-step teaching.

OUTPUT STYLE:
Follow this formatting structure strictly for each topic, separating topics with "---":

TOPIC NAME
• Key concept or definition
• Important keyword
• Critical relationship or comparison
• Important distinction

Remember:
• Short memory trigger or critical catchphrase

---

TOPIC NAME
• Key concept
• Key concept

Remember:
• Short memory trigger
"""

    prompt = (
        "Generate a Recall Sheet for the following study notes:\n"
        "--- NOTES TEXT START ---\n"
        f"{full_text}\n"
        "--- NOTES TEXT END ---\n\n"
        "Draft the Recall Sheet now:"
    )

    try:
        response_text = gemini_service.generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=False
        )
        return response_text
    except Exception as e:
        print(f"Error generating recall sheet: {e}")
        return (
            "### Recall Sheet Generation Failed\n\n"
            "We encountered an error communicating with the Gemini API. Please check your API key and network connection."
        )
