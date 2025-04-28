from flask import Flask, request, render_template, jsonify, send_file, session, redirect, url_for
import os
import tempfile
import uuid
import json
import time
from flask_cors import CORS

# Import application modules
from modules.speech_recognition import recognize_speech
from modules.pdf_generator import generate_pdf, generate_txt
from modules.llm_processor import initialize_model, process_text, process_text_async, get_job_status
from modules.model_downloader import get_available_models, get_downloadable_models, download_model
from modules.tor_templates import get_available_templates, get_template

app = Flask(__name__)
CORS(app)  # Allow cross-domain requests
app.secret_key = os.urandom(24)  # For session management

# Folder for temporary files
TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Models folder
MODELS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
if not os.path.exists(MODELS_FOLDER):
    os.makedirs(MODELS_FOLDER)


# With this:
with app.app_context():
    # Your existing setup_application code here
    # Check for available models
    available_models = get_available_models()
    if available_models:
        # Use the first available model
        model_path = available_models[0]["path"]
        initialize_model({
            "model_path": model_path,
            "n_ctx": 4096,
            "n_batch": 512,
            "n_gpu_layers": -1,
            "n_threads": 4
        })
        app.logger.info(f"LLM initialized with model: {os.path.basename(model_path)}")
    else:
        app.logger.warning("No LLM models found. LLM processing will not be available until a model is downloaded.")


@app.route('/api/models/set-active', methods=['POST'])
def set_active_model():
    """API endpoint to set active model"""
    data = request.json

    if not data or 'model_name' not in data:
        return jsonify({'success': False, 'error': 'Model name is required'}), 400

    model_name = data['model_name']

    try:
        # Get available models
        available_models = get_available_models()

        # Check if requested model exists
        model_exists = False
        model_path = None

        for model in available_models:
            if model['name'] == model_name:
                model_exists = True
                model_path = model['path']
                break

        if not model_exists:
            return jsonify({'success': False, 'error': f'Model {model_name} not found'}), 404

        # Initialize model with the selected one
        result = initialize_model({"model_path": model_path})

        if result:
            return jsonify({'success': True, 'message': f'Model {model_name} set as active'})
        else:
            return jsonify({'success': False, 'error': 'Failed to initialize model'}), 500

    except Exception as e:
        app.logger.error(f"Error setting active model: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/')
def index():
    """Main application page"""
    # Generate unique session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    # Get available templates for the UI
    templates = get_available_templates()

    return render_template('index.html', templates=templates)


@app.route('/recognize', methods=['POST'])
def recognize():
    """Handle speech recognition request"""
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio file not found'}), 400

    audio_file = request.files['audio']

    try:
        # Process with speech recognition module
        transcription = recognize_speech(audio_file)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process-text', methods=['POST'])
def process_document():
    """Process text with LLM to create structured document"""
    data = request.json

    if not data or 'text' not in data:
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    template_type = data.get('template_type', 'technical_specification')

    try:
        # Process text asynchronously
        job_id = process_text_async(text, template_type)

        # Save job ID in session
        session['processing_job_id'] = job_id

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Text processing started'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/job-status/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Check status of an LLM processing job"""
    status = get_job_status(job_id)
    return jsonify(status)


@app.route('/generate-pdf', methods=['POST'])
def create_pdf():
    """Create PDF from processed text"""
    data = request.json

    if not data or 'text' not in data:
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    session_id = session.get('session_id', str(uuid.uuid4()))

    try:
        # Generate PDF and save path in session
        pdf_path = generate_pdf(text, session_id, TEMP_FOLDER)
        session['pdf_path'] = pdf_path

        return jsonify({'success': True, 'message': 'PDF created successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download-pdf')
def download_pdf():
    """Download generated PDF file"""
    pdf_path = session.get('pdf_path')

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF file not found'}), 404

    try:
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='exPrompto_TOR.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-txt', methods=['POST'])
def create_txt():
    """Create TXT from processed text"""
    data = request.json

    if not data or 'text' not in data:
        return jsonify({'error': 'Text not provided'}), 400

    text = data['text']
    session_id = session.get('session_id', str(uuid.uuid4()))

    try:
        # Generate TXT and save path in session
        txt_path = generate_txt(text, session_id, TEMP_FOLDER)
        session['txt_path'] = txt_path

        return jsonify({'success': True, 'message': 'TXT created successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download-txt')
def download_txt():
    """Download generated TXT file"""
    txt_path = session.get('txt_path')

    if not txt_path or not os.path.exists(txt_path):
        return jsonify({'error': 'TXT file not found'}), 404

    try:
        return send_file(
            txt_path,
            as_attachment=True,
            download_name='exPrompto_TOR.txt',
            mimetype='text/plain'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# LLM Model Management Routes
@app.route('/models')
def models_page():
    """Page for managing LLM models"""
    available_models = get_available_models()
    downloadable_models = get_downloadable_models()

    return render_template(
        'models.html',
        available_models=available_models,
        downloadable_models=downloadable_models
    )


@app.route('/api/models', methods=['GET'])
def get_models():
    """API endpoint to get available and downloadable models"""
    available_models = get_available_models()
    downloadable_models = get_downloadable_models()

    return jsonify({
        'available_models': available_models,
        'downloadable_models': downloadable_models
    })


@app.route('/api/models/download', methods=['POST'])
def download_model_endpoint():
    """API endpoint to download a model"""
    data = request.json

    if not data or 'repo' not in data or 'variant' not in data:
        return jsonify({'error': 'Repository and variant are required'}), 400

    result = download_model(data['repo'], data['variant'], data.get('force', False))

    if result['success']:
        # Initialize model after download if no model is currently loaded
        if not hasattr(app, 'llm_initialized') or not app.llm_initialized:
            initialize_model({"model_path": result['path']})
            app.llm_initialized = True

    return jsonify(result)


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """API endpoint to get available templates"""
    templates = get_available_templates()
    return jsonify({'templates': templates})


# Clean up temporary files
@app.teardown_appcontext
def cleanup_temp_files(exception=None):
    """Clean up temporary files when request context ends"""
    # Find and delete old temporary files
    # (You can implement more sophisticated cleanup logic based on file age)
    pass


if __name__ == '__main__':
    app.run(debug=True)