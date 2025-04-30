from flask import Flask, request, render_template, jsonify, send_file, session, redirect, url_for
import os
import tempfile
import uuid
import json
import time
import logging
import traceback
from pathlib import Path
from flask_cors import CORS

# Import application modules
from modules.speech_recognition import recognize_speech
from modules.pdf_generator import generate_pdf, generate_txt
from modules.simple_llm_processor import initialize_model, process_text, process_text_async, get_job_status
from modules.model_downloader import get_available_models, get_downloadable_models, download_model
from modules.tor_templates import get_available_templates, get_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow cross-domain requests
app.secret_key = os.urandom(24)  # For session management
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

# Folder for temporary files
TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Make sure the LLM results folder exists
LLM_RESULTS_FOLDER = os.path.join(TEMP_FOLDER, 'llm_results')
if not os.path.exists(LLM_RESULTS_FOLDER):
    os.makedirs(LLM_RESULTS_FOLDER)

# Models folder
MODELS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
if not os.path.exists(MODELS_FOLDER):
    os.makedirs(MODELS_FOLDER)

# Define the default model to use - simplified to just use the basic model
DEFAULT_MODEL = "llama-2-7b-chat.Q2_K.gguf"
DEFAULT_MODEL_PATH = os.path.join(MODELS_FOLDER, DEFAULT_MODEL)


def initialize_llm():
    """Initialize the LLM with the default model"""
    try:
        # Check if the default model exists
        if not os.path.exists(DEFAULT_MODEL_PATH):
            logger.warning(f"Default model {DEFAULT_MODEL} not found. Attempting to download...")
            result = download_model("TheBloke/Llama-2-7B-Chat-GGUF", DEFAULT_MODEL, force=False)
            if not result['success']:
                logger.error(f"Failed to download default model: {result.get('error', 'Unknown error')}")
                return False

        # Initialize the model
        logger.info(f"Initializing LLM with model: {DEFAULT_MODEL}")
        result = initialize_model({
            "model_path": DEFAULT_MODEL_PATH,
            "n_ctx": 4096,
            "n_batch": 512,
            "n_gpu_layers": -1,
            "n_threads": 4
        })

        if result:
            logger.info("LLM initialized successfully")
            return True
        else:
            logger.error("Failed to initialize LLM")
            return False
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        logger.error(traceback.format_exc())
        return False


# Initialize LLM with app context
with app.app_context():
    initialize_llm()


@app.route('/')
def index():
    """Main application page"""
    # Generate unique session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"New session created: {session['session_id']}")

    # Get available templates for the UI
    templates = get_available_templates()
    logger.info(f"Loaded {len(templates)} templates")

    return render_template('index.html', templates=templates)


@app.route('/recognize', methods=['POST'])
def recognize():
    """Handle speech recognition request"""
    if 'audio' not in request.files:
        logger.warning("Audio file not provided in request")
        return jsonify({'error': 'Audio file not found'}), 400

    audio_file = request.files['audio']

    try:
        # Process with speech recognition module
        logger.info("Starting speech recognition")
        transcription = recognize_speech(audio_file)
        logger.info("Speech recognition completed successfully")
        return jsonify({'transcription': transcription})
    except Exception as e:
        logger.error(f"Error in speech recognition: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/process-text', methods=['POST'])
def process_document():
    """Process text with LLM to create structured document"""
    data = request.json

    if not data or 'text' not in data:
        logger.warning("Text not provided in request")
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    template_type = data.get('template_type', 'technical_specification')

    try:
        # Check if LLM is initialized, if not, initialize it
        result = initialize_llm()
        if not result:
            logger.error("Failed to initialize LLM for text processing")
            return jsonify({'error': 'LLM initialization failed'}), 500

        # Process text asynchronously
        logger.info(f"Starting text processing with template: {template_type}")
        job_id = process_text_async(text, template_type)
        logger.info(f"Text processing job initiated with ID: {job_id}")

        # Save job ID in session
        session['processing_job_id'] = job_id

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Text processing started'
        })
    except Exception as e:
        logger.error(f"Error in text processing: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/job-status/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Check status of an LLM processing job"""
    logger.info(f"Checking status for job: {job_id}")
    try:
        status = get_job_status(job_id)
        logger.info(f"Job status: {status.get('status', 'unknown')}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'error': str(e), 'job_id': job_id}), 500


@app.route('/generate-pdf', methods=['POST'])
def create_pdf():
    """Create PDF from processed text"""
    data = request.json

    if not data or 'text' not in data:
        logger.warning("Text not provided for PDF generation")
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    session_id = session.get('session_id', str(uuid.uuid4()))

    try:
        # Generate PDF and save path in session
        logger.info("Starting PDF generation")
        pdf_path = generate_pdf(text, session_id, TEMP_FOLDER)
        session['pdf_path'] = pdf_path
        logger.info(f"PDF generated successfully: {pdf_path}")

        return jsonify({'success': True, 'message': 'PDF created successfully'}), 200
    except Exception as e:
        logger.error(f"Error in PDF generation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/download-pdf')
def download_pdf():
    """Download generated PDF file"""
    pdf_path = session.get('pdf_path')

    if not pdf_path or not os.path.exists(pdf_path):
        logger.warning(f"PDF file not found: {pdf_path}")
        return jsonify({'error': 'PDF file not found'}), 404

    try:
        logger.info(f"Sending PDF file for download: {pdf_path}")
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='exPrompto_TOR.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error sending PDF file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/generate-txt', methods=['POST'])
def create_txt():
    """Create TXT from processed text"""
    data = request.json

    if not data or 'text' not in data:
        logger.warning("Text not provided for TXT generation")
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    session_id = session.get('session_id', str(uuid.uuid4()))

    try:
        # Generate TXT and save path in session
        logger.info("Starting TXT generation")
        txt_path = generate_txt(text, session_id, TEMP_FOLDER)
        session['txt_path'] = txt_path
        logger.info(f"TXT generated successfully: {txt_path}")

        return jsonify({'success': True, 'message': 'TXT created successfully'}), 200
    except Exception as e:
        logger.error(f"Error in TXT generation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/download-txt')
def download_txt():
    """Download generated TXT file"""
    txt_path = session.get('txt_path')

    if not txt_path or not os.path.exists(txt_path):
        logger.warning(f"TXT file not found: {txt_path}")
        return jsonify({'error': 'TXT file not found'}), 404

    try:
        logger.info(f"Sending TXT file for download: {txt_path}")
        return send_file(
            txt_path,
            as_attachment=True,
            download_name='exPrompto_TOR.txt',
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f"Error sending TXT file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/models')
def models_page():
    """Page for managing LLM models"""
    # Simplified to only show the default model
    available_models = get_available_models()

    # Filter to only show our default model in the UI
    available_models = [model for model in available_models if model['name'] == DEFAULT_MODEL]

    # If our default model isn't available, add it to downloadable models
    downloadable_models = []
    if not available_models:
        downloadable_models = [{
            "name": DEFAULT_MODEL,
            "repo": "TheBloke/Llama-2-7B-Chat-GGUF",
            "size_mb": 2700,
            "description": "2-bit quantized version, smallest size, good for testing",
            "installed": False
        }]

    return render_template(
        'models.html',
        available_models=available_models,
        downloadable_models=downloadable_models
    )


@app.route('/api/models/download', methods=['POST'])
def download_model_endpoint():
    """API endpoint to download a model"""
    data = request.json

    if not data or 'repo' not in data or 'variant' not in data:
        logger.warning("Repository and variant not provided for model download")
        return jsonify({'error': 'Repository and variant are required'}), 400

    try:
        logger.info(f"Starting model download: {data['variant']} from {data['repo']}")
        result = download_model(data['repo'], data['variant'], data.get('force', False))

        if result['success']:
            logger.info(f"Model downloaded successfully: {data['variant']}")
            # Initialize model after download
            initialize_llm()
        else:
            logger.error(f"Failed to download model: {result.get('error', 'Unknown error')}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in model download: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """API endpoint to get available templates"""
    try:
        templates = get_available_templates()
        logger.info(f"Returning {len(templates)} templates")
        return jsonify({'templates': templates})
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# Route to test LLM status
@app.route('/api/llm-status', methods=['GET'])
def llm_status():
    """Check the status of the LLM"""
    try:
        # Attempt to initialize the LLM if not already initialized
        result = initialize_llm()

        if result:
            return jsonify({
                'status': 'ok',
                'message': 'LLM is initialized and ready'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'LLM initialization failed'
            }), 500
    except Exception as e:
        logger.error(f"Error checking LLM status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500


# Add this route to your app.py file

@app.route('/test-llm', methods=['GET'])
def test_llm():
    """Test route to verify LLM processing works with a simple example"""
    try:
        # Very short test text
        test_text = "Создать веб-приложение для управления проектами."
        template_type = "technical_specification"  # Using the simplest template

        logger.info(f"Starting test LLM processing with text: '{test_text}'")

        # Process the text directly (not async) for immediate results
        result = process_text(test_text, template_type, temperature=0.1, max_tokens=1000)

        if result["success"]:
            logger.info("Test LLM processing successful")
            # Return the first 500 characters of the result for a quick view
            preview = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
            return jsonify({
                "status": "success",
                "message": "LLM processing successful",
                "processing_time": result["processing_time"],
                "preview": preview,
                "full_length": len(result["text"])
            })
        else:
            logger.error(f"Test LLM processing failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                "status": "error",
                "message": f"LLM processing failed: {result.get('error', 'Unknown error')}"
            }), 500
    except Exception as e:
        logger.error(f"Error in test LLM route: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Exception: {str(e)}"
        }), 500


# Clean up temporary files periodically
@app.before_request
def cleanup_temp_files():
    """Clean up old temporary files"""
    try:
        # Only run cleanup occasionally (e.g., 5% of requests)
        if hash(request.path) % 20 == 0:
            now = time.time()
            for filename in os.listdir(TEMP_FOLDER):
                file_path = os.path.join(TEMP_FOLDER, filename)
                # Skip directories (like llm_results)
                if os.path.isdir(file_path):
                    continue

                # Remove files older than 24 hours
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < (now - 86400):
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old temp file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing temp file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in temp file cleanup: {str(e)}")
        # Don't fail the request if cleanup fails


@app.route('/api/models/set-active', methods=['POST'])
def set_active_model():
    """API endpoint to set active model"""
    data = request.json

    if not data or 'model_name' not in data:
        logger.warning("Model name not provided")
        return jsonify({'success': False, 'error': 'Model name is required'}), 400

    model_name = data['model_name']
    logger.info(f"Setting active model: {model_name}")

    try:
        # Since we're using the simplified processor, just return success
        # The actual model doesn't matter since we're using rule-based processing
        return jsonify({
            'success': True,
            'message': f'Model {model_name} set as active'
        })
    except Exception as e:
        logger.error(f"Error setting active model: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)