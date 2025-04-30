from flask import Flask, request, render_template, jsonify, session
import os
import uuid
import logging
from modules.speech_recognition import recognize_speech
from modules.prompt_generation import generate_prompt

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
app.secret_key = os.urandom(24)  # For session management
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

# Folder for temporary files
TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

@app.route('/')
def index():
    """Main application page"""
    # Generate unique session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"New session created: {session['session_id']}")
    return render_template('index.html')

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

        # Generate prompt from transcription
        logger.info("Starting prompt generation")
        prompt_result = generate_prompt(transcription)

        response_data = {'transcription': transcription}

        # Add prompt to response if successful
        if prompt_result['success']:
            response_data['prompt'] = prompt_result['prompt']
            logger.info("Prompt generation completed successfully")
        else:
            response_data['prompt_error'] = prompt_result['error']
            logger.warning(f"Prompt generation failed: {prompt_result['error']}")

        logger.info("Speech recognition completed successfully")
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in speech recognition: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
