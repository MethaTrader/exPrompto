import os
import tempfile
import whisper
import logging
import shutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения загруженной модели
_whisper_model = None


def get_whisper_model(model_size="base"):
    """
    Загружает и возвращает модель Whisper.
    Если модель уже загружена, возвращает существующий экземпляр.

    Args:
        model_size (str): Размер модели Whisper ('tiny', 'base', 'small', 'medium', 'large')

    Returns:
        Загруженная модель Whisper
    """
    global _whisper_model

    # Если модель уже загружена, возвращаем её
    if _whisper_model is not None:
        return _whisper_model

    # Проверка валидности размера модели
    valid_sizes = ["tiny", "base", "small", "medium", "large"]
    if model_size not in valid_sizes:
        logger.warning(f"Неверный размер модели: {model_size}. Используется 'base'.")
        model_size = "base"

    # Загрузка модели
    logger.info(f"Загрузка модели Whisper размера '{model_size}'...")
    try:
        _whisper_model = whisper.load_model(model_size)
        logger.info("Модель Whisper успешно загружена")
        return _whisper_model
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели Whisper: {str(e)}")
        raise


def recognize_speech(audio_input, language=None, model_size="base"):
    """
    Распознает речь из аудиофайла.

    Args:
        audio_input: Объект файла Flask, путь к файлу или объект file-like
        language (str, optional): Язык для распознавания ('ru', 'uk', или None для автоопределения)
        model_size (str): Размер модели Whisper

    Returns:
        str: Распознанный текст

    Raises:
        Exception: В случае ошибки при распознавании
    """
    # Загружаем модель
    model = get_whisper_model(model_size)

    # Сохраняем временный файл
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

            # Handle different types of input
            if hasattr(audio_input, 'save'):  # Flask FileStorage object
                audio_input.save(temp_audio_path)
                logger.info(f"Flask FileStorage сохранен: {temp_audio_path}")
            elif hasattr(audio_input, 'read'):  # File-like object (e.g., open file or BytesIO)
                # Copy the file content
                with open(temp_audio_path, 'wb') as f:
                    shutil.copyfileobj(audio_input, f)
                logger.info(f"File-like объект скопирован: {temp_audio_path}")
            elif isinstance(audio_input, str):  # File path
                shutil.copy(audio_input, temp_audio_path)
                logger.info(f"Файл скопирован: {audio_input} -> {temp_audio_path}")
            else:
                raise TypeError(f"Неподдерживаемый тип аудио-входа: {type(audio_input)}")

        # Распознаем речь с помощью Whisper
        logger.info(f"Начало распознавания речи{' на языке: ' + language if language else ' с автоопределением языка'}...")

        # If language is specified, use it, otherwise let Whisper auto-detect
        if language:
            result = model.transcribe(temp_audio_path, language=language)
            detected_language = language
        else:
            # Auto-detect language
            result = model.transcribe(temp_audio_path)
            detected_language = result.get("language", "unknown")

        transcription = result["text"]
        logger.info(f"Распознавание речи завершено успешно, обнаруженный язык: {detected_language}")

        # Удаляем временный файл
        os.unlink(temp_audio_path)
        logger.info(f"Временный файл удален: {temp_audio_path}")

        return transcription

    except Exception as e:
        # В случае ошибки удаляем временный файл, если он был создан
        logger.error(f"Ошибка при распознавании речи: {str(e)}")
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                logger.info(f"Временный файл удален после ошибки: {temp_audio_path}")
            except Exception as cleanup_error:
                logger.error(f"Ошибка при удалении временного файла: {str(cleanup_error)}")

        raise Exception(f"Ошибка при распознавании речи: {str(e)}")
