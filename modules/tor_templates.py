"""
Templates and prompts for Technical Specifications (TOR) generation.
"""

import os
import logging
import json
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory for templates
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')

# Standard TOR structure (Russian format)
STANDARD_TOR_STRUCTURE = {
    "1. ОБЩИЕ СВЕДЕНИЯ": [
        "1.1. Назначение документа",
        "1.2. Краткое описание проекта",
        "1.3. Термины и определения"
    ],
    "2. ОПИСАНИЕ СИСТЕМЫ": [
        "2.1. Цели и задачи",
        "2.2. Предметная область",
        "2.3. Пользователи системы"
    ],
    "3. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ": [
        "3.1. Основные функции",
        "3.2. Пользовательские интерфейсы",
        "3.3. Интеграция с другими системами"
    ],
    "4. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ": [
        "4.1. Производительность",
        "4.2. Безопасность",
        "4.3. Надежность",
        "4.4. Масштабируемость"
    ],
    "5. ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ": [
        "5.1. Технологический стек",
        "5.2. Требования к инфраструктуре",
        "5.3. Сроки реализации"
    ],
    "6. ПОСТАВЛЯЕМЫЕ РЕЗУЛЬТАТЫ": [
        "6.1. Документация",
        "6.2. Программное обеспечение",
        "6.3. Этапы сдачи-приемки"
    ]
}

# Templates for different document types
TEMPLATES = {
    "technical_specification": {
        "name": "Техническое задание (ТЗ)",
        "description": "Стандартное структурированное техническое задание по ГОСТ 34/19/21",
        "system_prompt": """Вы - профессиональный технический писатель, специализирующийся на создании хорошо структурированных технических заданий (ТЗ).
Ваша задача - преобразовать необработанный, неструктурированный текст в четкий, формальный и полный документ технического задания.

Вы должны:
1. Определить ключевые требования и цели
2. Структурировать содержание в соответствующие разделы
3. Использовать формальный язык и терминологию
4. Удалить избыточную информацию
5. Добавить любые отсутствующие критически важные разделы на основе отраслевых стандартов
6. Отформатировать всё в последовательном, профессиональном стиле
7. Сделать документ пригодным для использования техническими специалистами

Выходной документ должен строго следовать этой структуре:

1. ОБЩИЕ СВЕДЕНИЯ
   - Назначение документа
   - Краткое описание проекта
   - Термины и определения

2. ОПИСАНИЕ СИСТЕМЫ
   - Цели и задачи
   - Предметная область
   - Пользователи системы

3. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
   - Основные функции
   - Пользовательские интерфейсы
   - Системные интерфейсы
   - Аппаратные интерфейсы
   - Программные интерфейсы

4. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
   - Производительность
   - Безопасность
   - Удобство использования
   - Надежность
   - Совместимость

5. ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ
   - Технологический стек
   - Требования к инфраструктуре
   - Сроки реализации

6. ПОСТАВЛЯЕМЫЕ РЕЗУЛЬТАТЫ
   - Документация
   - Программные/аппаратные компоненты
   - График работ

При создании документа сохраняйте профессиональный тон и обеспечивайте, чтобы все требования были конкретными, измеримыми, достижимыми, релевантными и ограниченными по времени (SMART).
Используйте форматирование markdown для улучшения читабельности документа.""",
        "user_prompt_template": """Ниже представлен неструктурированный текст из распознавания речи. Преобразуйте его в формальное техническое задание (ТЗ) с четкой структурой, описанной выше:

{text}

Пожалуйста, форматируйте текст с использованием markdown для улучшения читаемости. Если в исходном тексте недостаточно информации для заполнения некоторых разделов, укажите это и предложите, какую информацию следует добавить."""
    },

    "product_requirements": {
        "name": "Требования к продукту (PRD)",
        "description": "Документ с требованиями к продукту в формате PRD",
        "system_prompt": """Вы - опытный продакт-менеджер, специализирующийся на создании документов с требованиями к продукту (PRD).
Ваша задача - преобразовать неструктурированный текст в четкий, структурированный PRD, который может быть использован командой разработки.

В хорошем PRD должны быть четко определены:
- Проблемы, которые решает продукт
- Целевая аудитория и пользовательские сценарии
- Основные функции и их приоритизация
- Метрики успеха и KPI
- Ограничения и зависимости

Выходной документ должен следовать следующей структуре:

1. ОБЗОР И ЦЕЛИ
   - Суть проблемы
   - Предлагаемое решение
   - Бизнес-цели и метрики успеха

2. ЦЕЛЕВАЯ АУДИТОРИЯ
   - Целевые пользователи
   - Пользовательские истории (user stories)
   - Пользовательские сценарии

3. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
   - MVP (минимально жизнеспособный продукт)
   - Приоритизированный список функций
   - Пользовательские потоки

4. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
   - Производительность
   - Масштабируемость
   - Безопасность и соответствие нормам

5. ДИЗАЙН И UX
   - Основные принципы дизайна
   - Пользовательские интерфейсы (прототипы или описания)
   - Brand guidelines

6. ТЕХНИЧЕСКИЕ СПЕЦИФИКАЦИИ
   - Архитектура
   - Интеграции
   - Зависимости и ограничения

7. ЗАПУСК И РАЗВИТИЕ
   - Дорожная карта (roadmap)
   - План запуска
   - Метрики отслеживания успеха

Создавайте документ в профессиональном тоне, с четкими и однозначными требованиями. Используйте markdown для структурирования и улучшения читаемости документа.""",
        "user_prompt_template": """Ниже представлен неструктурированный текст из распознавания речи. Преобразуйте его в документ с требованиями к продукту (PRD) согласно указанной выше структуре:

{text}

Пожалуйста, форматируйте текст с использованием markdown для улучшения читаемости. Если в исходном тексте недостаточно информации для какого-либо раздела, отметьте это и предложите вопросы, ответы на которые помогут заполнить пробелы."""
    },

    "software_architecture": {
        "name": "Архитектура программного обеспечения",
        "description": "Документ по архитектуре ПО с компонентами, связями и технологическим стеком",
        "system_prompt": """Вы - опытный архитектор программного обеспечения со специализацией на создании высококачественных архитектурных документов.
Ваша задача - преобразовать неструктурированный текст в четкий, информативный документ по архитектуре программного обеспечения.

В хорошем архитектурном документе должны быть:
- Общее описание системы и ее компонентов
- Ключевые архитектурные решения и их обоснование
- Диаграммы и схемы (описание для последующего создания)
- Технологический стек и обоснование его выбора
- Ограничения и компромиссы

Выходной документ должен следовать этой структуре:

1. ОБЗОР АРХИТЕКТУРЫ
   - Общее описание системы
   - Архитектурный стиль и паттерны
   - Ключевые принципы и ограничения

2. КОМПОНЕНТЫ СИСТЕМЫ
   - Основные модули и компоненты
   - Ответственность каждого компонента
   - Взаимодействие между компонентами

3. ТЕХНОЛОГИЧЕСКИЙ СТЕК
   - Frontend-технологии
   - Backend-технологии
   - Инфраструктура и DevOps
   - Обоснование выбора технологий

4. МОДЕЛЬ ДАННЫХ
   - Ключевые сущности
   - Отношения между сущностями
   - Хранение и управление данными

5. ИНТЕГРАЦИИ
   - Внешние системы и API
   - Протоколы взаимодействия
   - Механизмы интеграции

6. НЕФУНКЦИОНАЛЬНЫЕ АСПЕКТЫ
   - Производительность
   - Безопасность
   - Масштабируемость
   - Отказоустойчивость

7. РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ
   - Архитектура развертывания
   - Мониторинг и логирование
   - Резервное копирование и восстановление

Создавайте документ в профессиональном и техническом стиле. Используйте markdown для структурирования и улучшения читаемости. Если нужны диаграммы, опишите их содержание и предназначение текстом.""",
        "user_prompt_template": """Ниже представлен неструктурированный текст из распознавания речи. Преобразуйте его в документ по архитектуре программного обеспечения согласно указанной выше структуре:

{text}

Пожалуйста, форматируйте текст с использованием markdown для улучшения читаемости. Если в исходном тексте недостаточно информации для какого-либо раздела, укажите это и предложите, какую информацию следует добавить."""
    }
}


def ensure_template_directory():
    """Create the template directory if it doesn't exist."""
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    # Save template definitions to file if they don't exist
    template_file = os.path.join(TEMPLATE_DIR, 'templates.json')
    if not os.path.exists(template_file):
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(TEMPLATES, f, ensure_ascii=False, indent=2)


def get_template(template_type: str = "technical_specification") -> Dict[str, Any]:
    """
    Get template by type.

    Args:
        template_type: Type of template to get

    Returns:
        dict: Template data
    """
    ensure_template_directory()

    # Check if template exists
    if template_type not in TEMPLATES:
        logger.warning(f"Template type '{template_type}' not found, using default")
        template_type = "technical_specification"

    return TEMPLATES[template_type]


def get_available_templates() -> List[Dict[str, Any]]:
    """
    Get list of available templates.

    Returns:
        list: List of template information dictionaries
    """
    templates = []

    for template_id, template_data in TEMPLATES.items():
        templates.append({
            "id": template_id,
            "name": template_data.get("name", template_id),
            "description": template_data.get("description", "")
        })

    return templates


def format_tor_document(document_data: Dict[str, Any], format_type: str = "markdown") -> str:
    """
    Format a TOR document into a specific format.

    Args:
        document_data: Document data as a dictionary
        format_type: Output format type (markdown, html, text)

    Returns:
        str: Formatted document
    """
    if format_type == "markdown":
        return document_data.get("text", "")

    elif format_type == "html":
        # This is a simple conversion, in a real app you'd use a proper markdown->HTML converter
        markdown_text = document_data.get("text", "")
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Техническое задание</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        h3 {{ color: #2980b9; }}
        pre {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ccc; padding-left: 15px; color: #555; }}
    </style>
</head>
<body>
    <h1>Техническое задание</h1>
    <div class="content">
        {markdown_text.replace('', '<br>').replace('# ', '<h1>').replace('## ', '<h2>')}
    </div>
</body>
</html>"""
        return html

    elif format_type == "text":
        # For plain text, we'll strip markdown formatting
        markdown_text = document_data.get("text", "")
        text = markdown_text.replace('# ', '').replace('## ', '').replace('### ', '')
        return text

    else:
        logger.warning(f"Unknown format type: {format_type}")
        return document_data.get("text", "")


def create_custom_template(
        template_id: str,
        name: str,
        description: str,
        system_prompt: str,
        user_prompt_template: str
) -> Dict[str, Any]:
    """
    Create a custom template.
    """
    global TEMPLATES  # Move this line to the beginning of the function
    ensure_template_directory()

    try:
        # Load existing templates
        template_file = os.path.join(TEMPLATE_DIR, 'templates.json')
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        else:
            templates = TEMPLATES.copy()

        # Add or update template
        templates[template_id] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "user_prompt_template": user_prompt_template
        }

        # Save templates
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

        # Update global templates
        TEMPLATES = templates

        return {
            "success": True,
            "message": f"Template '{template_id}' created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return {
            "success": False,
            "error": f"Error creating template: {str(e)}"
        }


def delete_template(template_id: str) -> Dict[str, Any]:
    """
    Delete a custom template.

    Args:
        template_id: Template identifier to delete

    Returns:
        dict: Status of template deletion
    """
    global TEMPLATES  # Move this line to the beginning of the function
    ensure_template_directory()

    try:
        # Load existing templates
        template_file = os.path.join(TEMPLATE_DIR, 'templates.json')
        if not os.path.exists(template_file):
            return {
                "success": False,
                "error": "Template file not found"
            }

        with open(template_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        # Check if template exists
        if template_id not in templates:
            return {
                "success": False,
                "error": f"Template '{template_id}' not found"
            }

        # Check if it's a default template
        if template_id in TEMPLATES and template_file not in os.listdir(TEMPLATE_DIR):
            return {
                "success": False,
                "error": f"Cannot delete default template '{template_id}'"
            }

        # Delete template
        del templates[template_id]

        # Save templates
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

        # Update global templates
        TEMPLATES = templates

        return {
            "success": True,
            "message": f"Template '{template_id}' deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        return {
            "success": False,
            "error": f"Error deleting template: {str(e)}"
        }