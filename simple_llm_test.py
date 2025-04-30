"""
Simple LLM Test - A minimal script to test the LLM functionality
Save this as simple_llm_test.py in your project root directory
"""

import os
import time
import sys

# Try to import the llama-cpp-python library directly
try:
    from llama_cpp import Llama

    print("Successfully imported Llama from llama_cpp")
except ImportError:
    print("Failed to import Llama from llama_cpp. Installing...")
    # Try to install it if not available
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python"])
    try:
        from llama_cpp import Llama

        print("Successfully installed and imported Llama")
    except ImportError:
        print("Failed to install llama-cpp-python. Please install it manually.")
        sys.exit(1)

# Define the model path
script_path = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(script_path, 'models')
default_model = "llama-2-7b-chat.Q2_K.gguf"
model_path = os.path.join(models_dir, default_model)

# Check for available models
print(f"Checking for models in {models_dir}")
if not os.path.exists(models_dir):
    print(f"Models directory not found: {models_dir}")
    sys.exit(1)

available_models = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]
if not available_models:
    print(f"No GGUF models found in {models_dir}")
    sys.exit(1)

print(f"Found {len(available_models)} model(s):")
for model in available_models:
    model_file = os.path.join(models_dir, model)
    size_mb = os.path.getsize(model_file) / (1024 * 1024)
    print(f"  - {model} ({size_mb:.2f} MB)")

# If default model doesn't exist, use the first available model
if not os.path.exists(model_path) and available_models:
    model_path = os.path.join(models_dir, available_models[0])
    print(f"Default model not found, using: {available_models[0]}")

# Load and test the model
print(f"Loading model from: {model_path}")
print("This may take a while...")

try:
    # Track time
    start_time = time.time()

    # Initialize the model with minimal settings
    llm = Llama(
        model_path=model_path,
        n_ctx=512,  # Small context window for testing
        n_batch=512,  # Batch size
        n_gpu_layers=0,  # Use CPU only for compatibility
        n_threads=4,  # Use 4 CPU threads
        verbose=True  # Enable verbose mode
    )

    load_time = time.time() - start_time
    print(f"Model loaded successfully in {load_time:.2f} seconds")

    # Run a simple inference
    print("Running a simple test...")
    test_start = time.time()

    output = llm("Translate this to Spanish: Hello, my name is Claude")

    test_time = time.time() - test_start
    print(f"Test completed in {test_time:.2f} seconds")
    print(f"Output: {output}")

    print("SIMPLE TEST PASSED! Your LLM is working correctly.")

except Exception as e:
    print(f"ERROR: {str(e)}")
    print("Test failed. See the error message above for details.")