import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Регистрация шрифтов с поддержкой кириллицы
def register_fonts():
    """
    Регистрирует шрифты с поддержкой кириллицы для ReportLab.

    Функция пытается загрузить шрифт DejaVuSans. Если файл не найден,
    использует встроенный шрифт Helvetica (который, к сожалению,
    не поддерживает кириллицу полноценно).
    """
    # Пути к файлам шрифтов
    dejavu_sans_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'DejaVuSans.ttf')
    dejavu_sans_bold_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'DejaVuSans-Bold.ttf')

    # Проверяем наличие папки для шрифтов и создаем ее, если нужно
    fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
        logger.info(f"Создана директория для шрифтов: {fonts_dir}")

    try:
        # Пытаемся зарегистрировать шрифты DejaVuSans
        if os.path.exists(dejavu_sans_path) and os.path.exists(dejavu_sans_bold_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_sans_path))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_sans_bold_path))
            logger.info("Шрифты DejaVuSans успешно зарегистрированы")
            return True
        else:
            # Если шрифтов нет, выводим сообщение с инструкциями
            logger.warning("Файлы шрифтов DejaVuSans не найдены. "
                           f"Поместите файлы DejaVuSans.ttf и DejaVuSans-Bold.ttf в папку {fonts_dir}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при регистрации шрифтов: {str(e)}")
        return False


def generate_pdf(text, session_id, temp_folder):
    """
    Генерирует PDF-документ с распознанным текстом.

    Args:
        text (str): Распознанный текст для включения в PDF
        session_id (str): Уникальный идентификатор сессии
        temp_folder (str): Папка для временных файлов

    Returns:
        str: Путь к созданному PDF-файлу

    Raises:
        Exception: В случае ошибки при создании PDF
    """
    # Регистрируем шрифты
    fonts_registered = register_fonts()

    # Создаем имя файла на основе session_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"exPrompto_recognition_{session_id}_{timestamp}.pdf"
    pdf_path = os.path.join(temp_folder, pdf_filename)

    try:
        logger.info(f"Начало создания PDF: {pdf_path}")

        # Создаем PDF-документ
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            title="exPrompto - Результат распознавания речи",
            author="exPrompto",
            subject="Распознавание речи",
            creator="exPrompto Speech Recognition"
        )

        # Получаем стили
        styles = getSampleStyleSheet()

        # Создаем кастомные стили с поддержкой кириллицы
        if fonts_registered:
            # С кириллическими шрифтами
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName='DejaVuSans-Bold',
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=20
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName='DejaVuSans',
                fontSize=12,
                textColor=colors.grey,
                spaceAfter=30
            )
            text_style = ParagraphStyle(
                'CustomText',
                parent=styles['Normal'],
                fontName='DejaVuSans',
                fontSize=12,
                leading=16,
                spaceBefore=10
            )
        else:
            # Со стандартными шрифтами (не поддерживают кириллицу полноценно)
            title_style = styles['Title']
            subtitle_style = styles['Normal']
            text_style = styles['Normal']

        # Создаем элементы документа
        elements = []

        # Добавляем заголовок
        elements.append(Paragraph("exPrompto - Результат распознавания речи", title_style))

        # Добавляем дату создания
        current_date = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        elements.append(Paragraph(f"Дата создания: {current_date}", subtitle_style))

        # Добавляем разделитель
        elements.append(Spacer(1, 20))

        # Добавляем текст распознавания
        # Разбиваем текст на абзацы для лучшего форматирования
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():  # Пропускаем пустые строки
                elements.append(Paragraph(paragraph, text_style))
                elements.append(Spacer(1, 10))

        # Создаем PDF-документ
        doc.build(elements)

        logger.info(f"PDF успешно создан: {pdf_path}")
        return pdf_path

    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {str(e)}")
        # Если файл был создан, но произошла ошибка, удаляем его
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                logger.info(f"Удален неполный PDF-файл: {pdf_path}")
            except:
                pass
        raise Exception(f"Ошибка при создании PDF: {str(e)}")


def generate_txt(text, session_id, temp_folder):
    """
    Генерирует текстовый файл с распознанным текстом.

    Args:
        text (str): Распознанный текст для сохранения
        session_id (str): Уникальный идентификатор сессии
        temp_folder (str): Папка для временных файлов

    Returns:
        str: Путь к созданному текстовому файлу

    Raises:
        Exception: В случае ошибки при создании файла
    """
    # Создаем имя файла на основе session_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"exPrompto_recognition_{session_id}_{timestamp}.txt"
    txt_path = os.path.join(temp_folder, txt_filename)

    try:
        logger.info(f"Начало создания TXT: {txt_path}")

        # Создаем заголовок и дату для текстового файла
        current_date = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        header = "exPrompto - Результат распознавания речи\n"
        date_line = f"Дата создания: {current_date}\n"
        separator = "-" * 50 + "\n\n"

        # Записываем в файл
        with open(txt_path, 'w', encoding='utf-8') as file:
            file.write(header)
            file.write(date_line)
            file.write(separator)
            file.write(text)

        logger.info(f"TXT файл успешно создан: {txt_path}")
        return txt_path

    except Exception as e:
        logger.error(f"Ошибка при создании TXT файла: {str(e)}")
        # Если файл был создан, но произошла ошибка, удаляем его
        if os.path.exists(txt_path):
            try:
                os.remove(txt_path)
                logger.info(f"Удален неполный TXT-файл: {txt_path}")
            except:
                pass
        raise Exception(f"Ошибка при создании TXT файла: {str(e)}")