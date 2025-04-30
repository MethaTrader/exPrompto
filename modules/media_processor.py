"""
Media processor module for handling audio extraction from video files.
"""

import os
import tempfile
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_audio_from_video(video_file_path, output_format="wav"):
    """
    Extract audio from a video file using ffmpeg.

    Args:
        video_file_path (str): Path to the video file
        output_format (str): Output audio format (default: wav)

    Returns:
        str: Path to the extracted audio file

    Raises:
        Exception: If audio extraction fails
    """
    try:
        # Create a temporary file for the extracted audio
        temp_audio = tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()

        logger.info(f"Extracting audio from video: {video_file_path} to {temp_audio_path}")

        # Run ffmpeg to extract audio
        cmd = [
            'ffmpeg',
            '-i', video_file_path,
            '-q:a', '0',  # Use highest quality
            '-map', 'a',  # Extract only audio
            '-y',  # Overwrite output file if it exists
            temp_audio_path
        ]

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check if ffmpeg command was successful
        if process.returncode != 0:
            logger.error(f"Error extracting audio: {process.stderr}")
            raise Exception(f"Failed to extract audio: {process.stderr}")

        logger.info(f"Audio extraction successful: {temp_audio_path}")
        return temp_audio_path

    except Exception as e:
        logger.error(f"Error in audio extraction: {str(e)}")
        # Clean up if needed
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        raise


def get_media_duration(file_path):
    """
    Get the duration of a media file using ffprobe.

    Args:
        file_path (str): Path to the media file

    Returns:
        float: Duration in seconds

    Raises:
        Exception: If ffprobe fails
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            logger.error(f"Error getting media duration: {process.stderr}")
            return None

        duration = float(process.stdout.strip())
        return duration

    except Exception as e:
        logger.error(f"Error getting media duration: {str(e)}")
        return None


def is_video_file(file_path):
    """
    Check if a file is a video file using ffprobe.

    Args:
        file_path (str): Path to the file

    Returns:
        bool: True if the file is a video, False otherwise
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',  # Select first video stream
            '-show_entries', 'stream=codec_type',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            return False

        output = process.stdout.strip()
        return output == 'video'

    except Exception as e:
        logger.error(f"Error checking if file is video: {str(e)}")
        return False