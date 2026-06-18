import google.generativeai as genai
import config
from functools import lru_cache
from typing import Optional

def configure_gemini(api_key: Optional[str] = None) -> bool:
    """
    Configures the google-generativeai SDK with the provided API key 
    or falls back to the key specified in config.py.
    """
    from dotenv import load_dotenv
    import importlib
    
    # Reload environment variables to pick up updates dynamically on Streamlit rerun
    load_dotenv(override=True)
    importlib.reload(config)
    
    key = api_key or config.GEMINI_API_KEY
    if not key or key == "your_gemini_api_key_here":
        return False
        
    genai.configure(api_key=key)
    return True

@lru_cache(maxsize=256)
def _cached_generate_response(
    prompt: str,
    system_instruction: str,
    json_mode: bool,
    model_name: str,
) -> str:
    """
    Helper function to prompt the gemini-1.5-flash model.
    """
    configure_gemini()
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
        
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=system_instruction or None
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Error communicating with Gemini API: {str(e)}")


def generate_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    json_mode: bool = False
) -> str:
    """
    Cached wrapper around the Gemini request so repeated reruns and repeated
    prompts do not consume extra API calls.
    """
    return _cached_generate_response(
        prompt=prompt,
        system_instruction=system_instruction or "",
        json_mode=json_mode,
        model_name=config.GEMINI_MODEL,
    )

