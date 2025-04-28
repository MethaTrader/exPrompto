"""
Utility for downloading and managing LLM models for exPrompto application.
"""

import os
import logging
import requests
import tqdm
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory for models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
MODEL_INFO_FILE = os.path.join(MODEL_DIR, 'model_info.json')

# Model repository information
MODEL_REPOS = {
    "TheBloke/Llama-2-7B-Chat-GGUF": {
        "base_url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/",
        "variants": {
            "llama-2-7b-chat.Q2_K.gguf": {
                "size": 2700,  # Size in MB (approximate)
                "description": "2-bit quantized version, smallest size, lowest quality"
            },
            "llama-2-7b-chat.Q4_K_M.gguf": {
                "size": 4200,  # Size in MB (approximate)
                "description": "4-bit quantized version, good balance of size and quality"
            },
            "llama-2-7b-chat.Q5_K_M.gguf": {
                "size": 5100,  # Size in MB (approximate)
                "description": "5-bit quantized version, better quality, larger size"
            }
        }
    },
    "minicpm/MiniCPM-2B-dpo-GGUF": {
        "base_url": "https://huggingface.co/minicpm/MiniCPM-2B-dpo-GGUF/resolve/main/",
        "variants": {
            "minicpm-2b-dpo.Q4_K_M.gguf": {
                "size": 1500,  # Size in MB (approximate)
                "description": "4-bit quantized version, very small model good for limited VRAM"
            }
        }
    },
    "IlyaGusev/saiga2_7b_gguf": {
        "base_url": "https://huggingface.co/IlyaGusev/saiga2_7b_gguf/resolve/main/",
        "variants": {
            "saiga2_7b-q4_k_m.gguf": {
                "size": 4200,  # Size in MB (approximate)
                "description": "4-bit Russian language model, based on Llama-2"
            }
        }
    }
}


def ensure_model_directory():
    """Create the model directory if it doesn't exist."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Create model info file if it doesn't exist
    if not os.path.exists(MODEL_INFO_FILE):
        with open(MODEL_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump({"models": {}}, f, ensure_ascii=False, indent=2)


def download_file(url: str, destination: str, chunk_size: int = 8192):
    """
    Download a file with progress bar.

    Args:
        url: URL to download from
        destination: Local destination path
        chunk_size: Download chunk size in bytes
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(destination, 'wb') as f, tqdm.tqdm(
                desc=os.path.basename(destination),
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        return True

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        # Remove partial download if it exists
        if os.path.exists(destination):
            os.remove(destination)
        return False


def calculate_md5(file_path: str) -> str:
    """
    Calculate MD5 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        str: MD5 hash as hexadecimal string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_model(
        repo: str,
        variant: str,
        force: bool = False
) -> Dict[str, Any]:
    """
    Download a model from a repository.

    Args:
        repo: Repository name
        variant: Model variant name
        force: Force download even if model exists

    Returns:
        dict: Status information about the download
    """
    ensure_model_directory()

    # Check if repo exists
    if repo not in MODEL_REPOS:
        return {"success": False, "error": f"Repository {repo} not found"}

    # Check if variant exists
    if variant not in MODEL_REPOS[repo]["variants"]:
        return {"success": False, "error": f"Variant {variant} not found in repository {repo}"}

    # Set download paths
    model_path = os.path.join(MODEL_DIR, variant)

    # Check if model already exists
    if os.path.exists(model_path) and not force:
        # Update model info
        update_model_info(repo, variant, model_path)
        return {"success": True, "message": f"Model already exists at {model_path}", "path": model_path}

    # Download the model
    url = MODEL_REPOS[repo]["base_url"] + variant
    logger.info(f"Downloading model from {url} to {model_path}")

    success = download_file(url, model_path)

    if success:
        # Update model info
        update_model_info(repo, variant, model_path)
        return {"success": True, "message": f"Model downloaded to {model_path}", "path": model_path}
    else:
        return {"success": False, "error": f"Failed to download model from {url}"}


def update_model_info(repo: str, variant: str, model_path: str):
    """
    Update the model information file with metadata about the downloaded model.

    Args:
        repo: Repository name
        variant: Model variant name
        model_path: Path to the model file
    """
    try:
        # Calculate file size and hash
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
        file_hash = calculate_md5(model_path)

        # Load existing model info
        with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
            model_info = json.load(f)

        # Add or update model info
        model_info["models"][variant] = {
            "repo": repo,
            "path": model_path,
            "size_mb": round(file_size, 2),
            "md5": file_hash,
            "date_added": Path(model_path).stat().st_mtime,
            "description": MODEL_REPOS[repo]["variants"][variant]["description"]
        }

        # Save updated model info
        with open(MODEL_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error updating model info: {str(e)}")


def get_available_models() -> List[Dict[str, Any]]:
    """
    Get information about available models.

    Returns:
        list: List of dictionaries with model information
    """
    ensure_model_directory()

    try:
        # Load model info
        with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
            model_info = json.load(f)

        # Collect information about available models
        models = []
        for variant, info in model_info.get("models", {}).items():
            if os.path.exists(info.get("path")):
                models.append({
                    "name": variant,
                    "path": info.get("path"),
                    "size_mb": info.get("size_mb", 0),
                    "description": info.get("description", ""),
                    "repo": info.get("repo", "")
                })

        return models

    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return []


def get_downloadable_models() -> List[Dict[str, Any]]:
    """
    Get information about models available for download.

    Returns:
        list: List of dictionaries with downloadable model information
    """
    # Collect information about available models
    models = []
    for repo, repo_info in MODEL_REPOS.items():
        for variant, variant_info in repo_info["variants"].items():
            models.append({
                "name": variant,
                "repo": repo,
                "size_mb": variant_info.get("size", 0),
                "description": variant_info.get("description", ""),
                "installed": os.path.exists(os.path.join(MODEL_DIR, variant))
            })

    return models


def remove_model(variant: str) -> Dict[str, Any]:
    """
    Remove a downloaded model.

    Args:
        variant: Model variant name

    Returns:
        dict: Status information about the removal
    """
    ensure_model_directory()

    model_path = os.path.join(MODEL_DIR, variant)

    if not os.path.exists(model_path):
        return {"success": False, "error": f"Model {variant} not found"}

    try:
        # Remove the model file
        os.remove(model_path)

        # Update model info
        with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
            model_info = json.load(f)

        if variant in model_info.get("models", {}):
            del model_info["models"][variant]

            # Save updated model info
            with open(MODEL_INFO_FILE, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": f"Model {variant} removed successfully"}

    except Exception as e:
        logger.error(f"Error removing model: {str(e)}")
        return {"success": False, "error": f"Error removing model: {str(e)}"}


if __name__ == "__main__":
    # Example usage
    ensure_model_directory()
    print("Available models for download:")
    models = get_downloadable_models()
    for i, model in enumerate(models):
        print(f"{i + 1}. {model['name']} ({model['size_mb']} MB) - {model['description']}")
        print(f"   Repository: {model['repo']}")
        print(f"   Installed: {'Yes' if model['installed'] else 'No'}")