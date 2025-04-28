import os
import tempfile
import whisper
import logging

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


def recognize_speech(audio_file, language="ru", model_size="base"):
    """
    Распознает речь из аудиофайла.

    Args:
        audio_file: Объект файла Flask из request.files['audio']
        language (str): Язык для распознавания
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
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name

        logger.info(f"Аудиофайл временно сохранен: {temp_audio_path}")

        # Распознаем речь с помощью Whisper
        logger.info("Начало распознавания речи...")
        result = model.transcribe(temp_audio_path, language=language)
        transcription = result["text"]
        logger.info("Распознавание речи завершено успешно")

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