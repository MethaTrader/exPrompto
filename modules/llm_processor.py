"""
LLM processor module for exPrompto application.
Processes raw transcribed text into structured technical specifications.
"""

import os
import logging
import json
import time
from pathlib import Path
import torch
from typing import Dict, Any, Optional, List
import threading
import queue

# Llama-cpp-python for optimized inference
from llama_cpp import Llama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global LLM instance for reuse
_llm_instance = None
_llm_lock = threading.Lock()
_processing_queue = queue.Queue()
_llm_processing_thread = None
_is_processing = False

# Base directory for models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')

# Default model configuration
DEFAULT_MODEL_CONFIG = {
    "model_path": os.path.join(MODEL_DIR, "llama-2-7b-chat.Q4_K_M.gguf"),
    "n_ctx": 4096,  # Context window size
    "n_batch": 512,  # Batch size for prompt processing
    "n_gpu_layers": -1,  # -1 means use all available GPU layers
    "n_threads": 4,  # CPU threads for processing
    "verbose": False  # Set to True for debugging
}

# Templates for different document types
TEMPLATES = {
    "technical_specification": {
        "system_prompt": """You are a professional technical writer specializing in creating well-structured technical specifications (TZ/TOR). 
Your task is to transform raw, unstructured text into a clear, formal, and comprehensive technical specification document.
You should:
1. Identify the key requirements and objectives
2. Structure the content into appropriate sections
3. Use formal language and terminology
4. Remove redundant information
5. Add any missing critical sections based on industry standards
6. Format everything in a consistent, professional style
7. Make the document usable for technical teams

The output should strictly follow this structure:
1. INTRODUCTION
   - Purpose
   - Scope
   - Definitions and Acronyms

2. SYSTEM OVERVIEW
   - Description
   - Context
   - User Characteristics

3. FUNCTIONAL REQUIREMENTS
   - Core Functionality
   - User Interfaces
   - System Interfaces
   - Hardware Interfaces
   - Software Interfaces

4. NON-FUNCTIONAL REQUIREMENTS
   - Performance
   - Security
   - Usability
   - Reliability
   - Compatibility

5. DELIVERABLES
   - Documentation
   - Software/Hardware Components
   - Timeline

When generating the document, maintain a professional tone and ensure all requirements are specific, measurable, achievable, relevant, and time-bound (SMART).
Write your response in Russian if the original text is in Russian, or in English if the original text is in English.
""",
        "user_prompt_template": """Ниже представлен неструктурированный текст из распознавания речи. Преобразуйте его в формальное техническое задание (ТЗ) с четкой структурой, описанной выше:

{text}

Пожалуйста, форматируйте текст с использованием markdown для улучшения читаемости."""
    },

    "project_brief": {
        "system_prompt": """You are a professional project manager specializing in creating clear project briefs from raw information.
Your task is to transform unstructured text into a well-organized project brief document that can be understood by all stakeholders.
The document should follow standard project management methodologies and be comprehensive yet concise.""",

        "user_prompt_template": """Ниже представлен неструктурированный текст. Преобразуйте его в проектную документацию:

{text}

Пожалуйста, форматируйте текст с использованием markdown для улучшения читаемости."""
    }
}


def initialize_model(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Initialize the LLM with the specified configuration.

    Args:
        config: Dictionary with model configuration parameters

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global _llm_instance

    if config is None:
        config = DEFAULT_MODEL_CONFIG

    # Ensure model directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Check if model file exists
    model_path = config.get("model_path", DEFAULT_MODEL_CONFIG["model_path"])
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False

    try:
        with _llm_lock:
            # Set GPU configuration based on available hardware
            if torch.cuda.is_available():
                n_gpu_layers = config.get("n_gpu_layers", -1)
                logger.info(f"CUDA is available. Using {n_gpu_layers} GPU layers")
            else:
                logger.info("CUDA not available. Using CPU only.")
                config["n_gpu_layers"] = 0

            # Initialize Llama model
            _llm_instance = Llama(
                model_path=model_path,
                n_ctx=config.get("n_ctx", 4096),
                n_batch=config.get("n_batch", 512),
                n_gpu_layers=config.get("n_gpu_layers", -1),
                n_threads=config.get("n_threads", 4),
                verbose=config.get("verbose", False)
            )

            logger.info(f"LLM initialized successfully with model: {os.path.basename(model_path)}")
            return True

    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        return False


def get_llm_instance():
    """
    Get the global LLM instance, initializing it if necessary.

    Returns:
        Llama: The LLM instance
    """
    global _llm_instance

    if _llm_instance is None:
        initialize_model()

    return _llm_instance


def process_text(text: str, template_type: str = "technical_specification",
                 temperature: float = 0.1, max_tokens: int = 4000) -> Dict[str, Any]:
    """
    Process raw text into a structured document using the LLM.

    Args:
        text: Raw text to process
        template_type: Type of document template to use
        temperature: Temperature for generation (lower = more deterministic)
        max_tokens: Maximum number of tokens to generate

    Returns:
        dict: Dictionary containing the processed text and metadata
    """
    llm = get_llm_instance()
    if llm is None:
        return {"success": False, "error": "LLM not initialized", "text": ""}

    start_time = time.time()

    try:
        # Get the appropriate template
        template = TEMPLATES.get(template_type, TEMPLATES["technical_specification"])
        system_prompt = template["system_prompt"]
        user_prompt = template["user_prompt_template"].format(text=text)

        # Prepare the prompt in Llama-2 chat format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Generate the response
        result = llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        # Extract the response text
        processed_text = result["choices"][0]["message"]["content"]

        # Calculate processing time
        processing_time = time.time() - start_time

        return {
            "success": True,
            "text": processed_text,
            "processing_time": processing_time,
            "template_type": template_type
        }

    except Exception as e:
        logger.error(f"Error processing text with LLM: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "processing_time": time.time() - start_time
        }


def process_text_async(text: str, template_type: str = "technical_specification",
                       temperature: float = 0.1, max_tokens: int = 4000) -> str:
    """
    Add a text processing job to the queue and return a job ID.

    Args:
        text: Raw text to process
        template_type: Type of document template to use
        temperature: Temperature for generation
        max_tokens: Maximum number of tokens to generate

    Returns:
        str: Job ID for tracking the processing job
    """
    job_id = f"job_{int(time.time())}_{hash(text) % 10000}"

    # Add job to queue
    _processing_queue.put({
        "job_id": job_id,
        "text": text,
        "template_type": template_type,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "status": "queued",
        "result": None,
        "timestamp": time.time()
    })

    # Start processing thread if not running
    global _llm_processing_thread, _is_processing
    if _llm_processing_thread is None or not _is_processing:
        _is_processing = True
        _llm_processing_thread = threading.Thread(target=_process_queue)
        _llm_processing_thread.daemon = True
        _llm_processing_thread.start()

    return job_id


def _process_queue():
    """
    Background thread to process the queue of LLM jobs.
    """
    global _is_processing

    while _is_processing:
        try:
            # Get job from queue (non-blocking)
            try:
                job = _processing_queue.get(block=False)
            except queue.Empty:
                # No jobs, sleep and check again
                time.sleep(0.5)
                # If queue has been empty for a while, exit the thread
                if _processing_queue.empty():
                    _is_processing = False
                continue

            # Update job status
            job["status"] = "processing"

            # Process the text
            result = process_text(
                job["text"],
                job["template_type"],
                job["temperature"],
                job["max_tokens"]
            )

            # Update job with result
            job["status"] = "completed" if result["success"] else "failed"
            job["result"] = result
            job["completion_time"] = time.time()

            # Store result in a results cache (you could add a proper caching mechanism here)
            _store_job_result(job)

            # Mark queue task as done
            _processing_queue.task_done()

        except Exception as e:
            logger.error(f"Error in processing thread: {str(e)}")
            _is_processing = False


# Simple file-based job result storage
def _store_job_result(job):
    """Store job result in a temporary file"""
    try:
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp', 'llm_results')
        os.makedirs(temp_dir, exist_ok=True)

        # Write job result to file
        with open(os.path.join(temp_dir, f"{job['job_id']}.json"), 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error storing job result: {str(e)}")


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a processing job.

    Args:
        job_id: Job ID to check

    Returns:
        dict: Dictionary containing job status and result if available
    """
    # Check if job result file exists
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp', 'llm_results')
    result_file = os.path.join(temp_dir, f"{job_id}.json")

    if os.path.exists(result_file):
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading job result: {str(e)}")
            return {"status": "error", "error": str(e)}

    # Check if job is in queue
    for item in list(_processing_queue.queue):
        if item.get("job_id") == job_id:
            return {
                "status": item.get("status", "unknown"),
                "job_id": job_id,
                "timestamp": item.get("timestamp")
            }

    return {"status": "not_found", "job_id": job_id}


def download_model(model_name: str = "llama-2-7b-chat.Q4_K_M.gguf") -> bool:
    """
    Download a model if it doesn't exist.

    Args:
        model_name: Name of the model to download

    Returns:
        bool: True if download successful, False otherwise
    """
    # This is a placeholder. In a real implementation, you would download from HuggingFace or another source
    model_path = os.path.join(MODEL_DIR, model_name)

    if os.path.exists(model_path):
        logger.info(f"Model already exists: {model_path}")
        return True

    try:
        logger.info(f"Downloading model {model_name}...")

        # In a real implementation, add code to download the model from a source
        # For example, using huggingface_hub:
        # from huggingface_hub import hf_hub_download
        # hf_hub_download(repo_id="TheBloke/Llama-2-7B-Chat-GGUF", filename=model_name, local_dir=MODEL_DIR)

        logger.info(f"Download not implemented. Please manually download the model to: {model_path}")
        return False

    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return False


def get_available_models() -> List[Dict[str, Any]]:
    """
    Get a list of available models in the models directory.

    Returns:
        list: List of dictionaries containing model information
    """
    models = []

    if not os.path.exists(MODEL_DIR):
        return models

    for file in os.listdir(MODEL_DIR):
        if file.endswith(".gguf"):
            file_path = os.path.join(MODEL_DIR, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            models.append({
                "name": file,
                "path": file_path,
                "size_mb": round(file_size, 2)
            })

    return models


def get_available_templates() -> List[Dict[str, Any]]:
    """
    Get a list of available templates.

    Returns:
        list: List of dictionaries containing template information
    """
    templates = []

    for template_name, template_data in TEMPLATES.items():
        templates.append({
            "name": template_name,
            "description": template_data.get("system_prompt", "")[:100] + "..."
        })

    return templates