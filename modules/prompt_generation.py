import requests
import logging
import os
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "mistralai/mistral-small"  # Free model


def generate_prompt(text: str) -> Dict[str, Any]:
    """
    Generate a structured prompt based on the given text using OpenRouter API.

    Args:
        text (str): The input text (transcription) to generate a prompt from

    Returns:
        Dict[str, Any]: A dictionary containing the generated prompt or error information
    """
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key is not set")
        return {"success": False, "error": "OpenRouter API key not configured"}

    try:
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": DEFAULT_MODEL,  # Using a free model
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate a structured prompt based on the following transcription. Make it concise but effective for an AI assistant: {text}"
                }
            ]
        }

        # Make the request to OpenRouter API
        logger.info("Sending request to OpenRouter API")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)

        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            generated_prompt = result["choices"][0]["message"]["content"]
            logger.info("Successfully generated prompt")
            return {"success": True, "prompt": generated_prompt}
        else:
            error_message = f"OpenRouter API error: {response.status_code} - {response.text}"
            logger.error(error_message)
            return {"success": False, "error": error_message}

    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}