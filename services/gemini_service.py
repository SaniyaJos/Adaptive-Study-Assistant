import google.generativeai as genai
import config
from functools import lru_cache
from typing import Optional

def configure_gemini(api_key: Optional[str] = None) -> bool:
    """
    Configures the google-generativeai SDK with the provided API key 
    or falls back to the key specified in config.py.
    
    Args:
        api_key: Optional string containing Gemini API key.
        
    Returns:
        bool: True if key is successfully configured, False otherwise.
    """
    from dotenv import load_dotenv
    import importlib
    
    # Reload environment variables from .env to pick up updates on Streamlit rerun
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
    
    Args:
        prompt: User prompt content.
        system_instruction: System persona or behavioral instruction.
        json_mode: If True, forces model to respond in valid JSON format.
        
    Returns:
        str: Response text from the model.
    """
    # Verify API config (in case configuration hasn't run yet)
    configure_gemini()
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    # Enable JSON mode structure
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
        # Return empty string or handle gracefully
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
