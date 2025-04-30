"""
CPU-Only LLM processor module for exPrompto application.
This version forces CPU-only processing for better compatibility.
"""

import os
import logging
import json
import time
from pathlib import Path
import threading
import queue

# Llama-cpp-python for optimized inference
from llama_cpp import Llama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_processor.log"),
        logging.StreamHandler()
    ]
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

# Default model configuration - CPU ONLY VERSION
DEFAULT_MODEL_CONFIG = {
    "model_path": os.path.join(MODEL_DIR, "llama-2-7b-chat.Q2_K.gguf"),
    "n_ctx": 2048,  # Reduced context window size
    "n_batch": 512,  # Batch size for prompt processing
    "n_gpu_layers": 0,  # FORCE CPU ONLY MODE
    "n_threads": 4,  # CPU threads for processing
}

# Simple template for testing
SIMPLE_TEMPLATE = """You are a technical writer.
Convert this input into a short technical specification: {text}
Keep it under 500 words."""


def initialize_model(config=None):
    """Initialize the LLM with CPU-only configuration"""
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
            # Force CPU only mode
            config["n_gpu_layers"] = 0
            logger.info("Using CPU-only mode for maximum compatibility")

            # Initialize Llama model with progress feedback
            logger.info(f"Initializing LLM with model: {os.path.basename(model_path)}")
            logger.info(f"Model configuration: {config}")

            _llm_instance = Llama(
                model_path=model_path,
                n_ctx=config.get("n_ctx", 2048),
                n_batch=config.get("n_batch", 512),
                n_gpu_layers=0,  # Force CPU-only mode
                n_threads=config.get("n_threads", 4),
                verbose=True  # Enable verbose mode for debugging
            )

            logger.info(f"LLM initialized successfully with model: {os.path.basename(model_path)}")
            return True

    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def simple_test():
    """Run a simple test to verify LLM functionality"""
    if _llm_instance is None:
        if not initialize_model():
            return {"success": False, "error": "Failed to initialize LLM"}

    try:
        # Simple test
        logger.info("Running simple LLM test")
        start_time = time.time()

        # Use a very simple prompt
        test_prompt = "Translate to French: Hello world"

        # Generate the response
        result = _llm_instance(test_prompt, max_tokens=20)

        processing_time = time.time() - start_time
        logger.info(f"Test completed in {processing_time:.2f} seconds")

        return {
            "success": True,
            "text": result,
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error(f"Error in simple test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


def process_simple_text(text):
    """Process text with a simple template - no async, no queuing"""
    if _llm_instance is None:
        if not initialize_model():
            return {"success": False, "error": "Failed to initialize LLM"}

    try:
        # Process with a simple template
        logger.info(f"Processing text with simple template, length: {len(text)} chars")
        start_time = time.time()

        # Prepare simple prompt
        prompt = SIMPLE_TEMPLATE.format(text=text)

        # Generate the response with timeout
        logger.info("Starting LLM inference")
        max_tokens = 500  # Limit output size

        # Run inference
        result = _llm_instance(prompt, max_tokens=max_tokens)

        processing_time = time.time() - start_time
        logger.info(f"Processing completed in {processing_time:.2f} seconds")

        return {
            "success": True,
            "text": result,
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Simple test when run directly
    print("Initializing LLM...")
    if initialize_model():
        print("LLM initialized successfully")
        result = simple_test()
        print(f"Test result: {result}")
    else:
        print("LLM initialization failed")