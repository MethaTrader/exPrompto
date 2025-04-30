"""
LLM Diagnostics - A standalone script to test LLM functionality
Save this as diagnose_llm.py in your project root directory
"""

import os
import sys
import time
import logging
import torch
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("llm-diagnostics")

# Get the absolute path of the current script
script_path = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to sys.path
sys.path.insert(0, script_path)

# Attempt to import from modules
try:
    from modules.llm_processor import Llama

    logger.info("Successfully imported Llama from llm_processor")
except ImportError:
    logger.error("Failed to import Llama from llm_processor")
    try:
        from llama_cpp import Llama

        logger.info("Imported Llama directly from llama_cpp")
    except ImportError:
        logger.error("Failed to import Llama from llama_cpp. Make sure it's installed: pip install llama-cpp-python")
        sys.exit(1)


def diagnose_gpu():
    """Check GPU availability and memory"""
    logger.info("Checking GPU availability...")

    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        logger.info(f"CUDA is available. Found {device_count} GPU(s)")

        for i in range(device_count):
            device_name = torch.cuda.get_device_name(i)
            total_memory = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)  # Convert to GB
            free_memory = torch.cuda.memory_reserved(i) / (1024 ** 3)  # Convert to GB
            used_memory = torch.cuda.memory_allocated(i) / (1024 ** 3)  # Convert to GB

            logger.info(f"GPU {i}: {device_name}")
            logger.info(f"  Total memory: {total_memory:.2f} GB")
            logger.info(f"  Reserved memory: {free_memory:.2f} GB")
            logger.info(f"  Allocated memory: {used_memory:.2f} GB")

        return True
    else:
        logger.info("CUDA is not available. Will use CPU only.")
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Total system memory: {memory.total / (1024 ** 3):.2f} GB")
        logger.info(f"Available memory: {memory.available / (1024 ** 3):.2f} GB")
        logger.info(f"Memory usage: {memory.percent}%")
        return False


def check_model_file(model_path):
    """Check if the model file exists and get its size"""
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False

    size_bytes = os.path.getsize(model_path)
    size_mb = size_bytes / (1024 * 1024)
    logger.info(f"Model file exists: {model_path}")
    logger.info(f"Model file size: {size_mb:.2f} MB")

    # Very basic check - if the file is too small, it might be corrupted or incomplete
    if size_mb < 100:  # Most GGUF models are at least several hundred MB
        logger.warning(f"Model file seems too small ({size_mb:.2f} MB). It might be corrupted or incomplete.")

    return True


def test_llm_inference(model_path, n_gpu_layers=-1, n_threads=4):
    """Test basic LLM inference with a simple prompt"""
    logger.info(f"Testing LLM inference with model: {model_path}")
    logger.info(f"Using {n_gpu_layers} GPU layers and {n_threads} CPU threads")

    start_time = time.time()
    logger.info("Initializing LLM (this may take a while)...")

    try:
        # Initialize model with progress feedback
        llm = Llama(
            model_path=model_path,
            n_ctx=512,  # Small context for testing
            n_batch=512,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            verbose=True  # Enable verbose mode for more feedback
        )

        init_time = time.time() - start_time
        logger.info(f"LLM initialized in {init_time:.2f} seconds")

        # Simple prompt for testing
        logger.info("Running inference with a test prompt...")
        inference_start = time.time()

        output = llm("Translate this to French: Hello, world!")

        inference_time = time.time() - inference_start
        logger.info(f"Inference completed in {inference_time:.2f} seconds")
        logger.info(f"Output: {output}")

        return True
    except Exception as e:
        logger.error(f"Error during LLM initialization or inference: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        return False


def main():
    """Main diagnostic function"""
    logger.info("Starting LLM diagnostics...")

    # Locate model directory and default model
    models_dir = os.path.join(script_path, 'models')
    default_model = "llama-2-7b-chat.Q2_K.gguf"
    model_path = os.path.join(models_dir, default_model)

    # Check if models directory exists
    if not os.path.exists(models_dir):
        logger.error(f"Models directory not found: {models_dir}")
        return

    # List available models
    logger.info(f"Checking models directory: {models_dir}")
    available_models = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]

    if not available_models:
        logger.error(f"No GGUF models found in {models_dir}")
        return

    logger.info(f"Found {len(available_models)} model(s):")
    for model in available_models:
        model_file = os.path.join(models_dir, model)
        size_mb = os.path.getsize(model_file) / (1024 * 1024)
        logger.info(f"  - {model} ({size_mb:.2f} MB)")

    # If default model doesn't exist, use the first available model
    if not os.path.exists(model_path) and available_models:
        model_path = os.path.join(models_dir, available_models[0])
        logger.info(f"Default model not found, using: {available_models[0]}")

    # Check GPU/CPU resources
    has_gpu = diagnose_gpu()

    # Check model file
    if not check_model_file(model_path):
        return

    # Test LLM
    n_gpu_layers = -1 if has_gpu else 0
    test_llm_inference(model_path, n_gpu_layers=n_gpu_layers)

    logger.info("LLM diagnostics completed")


if __name__ == "__main__":
    main()