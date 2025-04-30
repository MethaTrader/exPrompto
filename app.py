from flask import Flask, request, render_template, jsonify, session
import os
import uuid
import logging
import tempfile
from modules.speech_recognition import recognize_speech
from modules.media_processor import extract_audio_from_video, is_video_file, get_media_duration

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
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 500MB max upload

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


@app.route('/upload')
def upload_page():
    """File upload page for audio/video transcription"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"New session created: {session['session_id']}")
    return render_template('upload.html')


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
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Handle audio/video file transcription request"""
    if 'audio' not in request.files:
        logger.warning("Media file not provided in request")
        return jsonify({'error': 'File not found'}), 400

    media_file = request.files['audio']

    if media_file.filename == '':
        logger.warning("Empty filename provided")
        return jsonify({'error': 'No file selected'}), 400

    # Get language parameter (default to auto-detection if not provided)
    language = request.form.get('language', 'auto')
    logger.info(f"Using language setting: {language}")

    # Save the uploaded file temporarily
    temp_media = tempfile.NamedTemporaryFile(delete=False)
    temp_media_path = temp_media.name
    media_file.save(temp_media_path)
    temp_media.close()

    try:
        # Check if it's a video file
        is_video = is_video_file(temp_media_path)
        logger.info(f"File type detection: {'Video' if is_video else 'Audio'}")

        # Get media duration for metadata
        duration = get_media_duration(temp_media_path)
        duration_formatted = f"{int(duration//60)}:{int(duration%60):02d}" if duration else "Unknown"

        # If it's a video, extract the audio
        if is_video:
            logger.info(f"Extracting audio from video file: {media_file.filename}")
            audio_path = extract_audio_from_video(temp_media_path)

            # Process the extracted audio
            with open(audio_path, 'rb') as audio_file:
                logger.info(f"Starting transcription of extracted audio with language: {language}")
                # Pass the selected language to recognize_speech
                transcription = recognize_speech(audio_file, language=language if language != 'auto' else None)

            # Clean up the extracted audio file
            os.unlink(audio_path)
            logger.info(f"Removed temporary audio file: {audio_path}")
        else:
            # Process the audio file directly
            with open(temp_media_path, 'rb') as audio_file:
                logger.info(f"Starting transcription of audio file with language: {language}")
                # Pass the selected language to recognize_speech
                transcription = recognize_speech(audio_file, language=language if language != 'auto' else None)

        # Clean up the temporary media file
        os.unlink(temp_media_path)
        logger.info(f"Removed temporary media file: {temp_media_path}")

        logger.info("Transcription completed successfully")

        # Return the transcription along with media metadata
        return jsonify({
            'transcription': transcription,
            'media_type': 'video' if is_video else 'audio',
            'duration': duration_formatted,
            'file_name': media_file.filename,
            'language': language
        })

    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # Clean up temporary files in case of error
        if os.path.exists(temp_media_path):
            os.unlink(temp_media_path)
            logger.info(f"Removed temporary media file after error: {temp_media_path}")

        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
