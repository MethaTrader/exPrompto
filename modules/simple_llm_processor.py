"""
Ultra Simple LLM processor for exPrompto application.
This version is extremely simplified for maximum compatibility.
"""

import os
import logging
import json
import time
import signal
from pathlib import Path
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_simple.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base directory for models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Temp directory for job results
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp', 'llm_results')
os.makedirs(TEMP_DIR, exist_ok=True)

# In-memory storage for job results
_job_results = {}

# Default model
DEFAULT_MODEL = "llama-2-7b-chat.Q2_K.gguf"

# Simple template that will work with any input
SIMPLE_TEMPLATE = """
Преобразуй следующий текст в формальное техническое задание с разделами:
1. Введение
2. Цели и задачи
3. Функциональные требования
4. Нефункциональные требования
5. Сроки выполнения

Текст: {text}

Пожалуйста, используй формат markdown.
"""


class TimeoutError(Exception):
    """Exception raised when a function call times out"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutError("LLM processing timed out")


def process_simple_text(text, output_format="markdown"):
    """
    Process text with enhanced text analysis to create more accurate technical specifications
    based on the actual content of the input text.
    """
    logger.info(f"Processing text with enhanced text analysis, length: {len(text)} chars")

    # Basic text cleaning
    text = text.strip()
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    if not paragraphs:
        logger.warning("Empty input text")
        paragraphs = ["Техническое задание"]

    # Extract what looks like a title - first sentence or paragraph
    title = paragraphs[0].split('.')[0] if paragraphs else "Техническое задание"
    if len(title) > 100:  # If title is too long, truncate
        title = title[:100] + "..."

    # Initialize sections that will be populated from the input text
    sections = {
        "Введение": {},
        "Цели и задачи": {},
        "Функциональные требования": {},
        "Нефункциональные требования": {},
        "Технические требования": {},
        "Сроки и этапы реализации": {}
    }

    # Text analysis to extract key information

    # Keywords for categorization
    keywords = {
        "цели": "Цели и задачи",
        "задачи": "Цели и задачи",
        "назначение": "Введение",
        "функции": "Функциональные требования",
        "функционал": "Функциональные требования",
        "должен": "Функциональные требования",
        "производительность": "Нефункциональные требования",
        "безопасность": "Нефункциональные требования",
        "надежность": "Нефункциональные требования",
        "масштабируемость": "Нефункциональные требования",
        "технологии": "Технические требования",
        "архитектура": "Технические требования",
        "платформа": "Технические требования",
        "база данных": "Технические требования",
        "срок": "Сроки и этапы реализации",
        "этап": "Сроки и этапы реализации",
        "неделя": "Сроки и этапы реализации",
        "месяц": "Сроки и этапы реализации",
        "deadline": "Сроки и этапы реализации",
        "дедлайн": "Сроки и этапы реализации",
    }

    # Categorize paragraphs based on keywords
    categorized_paragraphs = {}
    for section in sections.keys():
        categorized_paragraphs[section] = []

    # First pass: categorize by keywords
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        assigned = False

        # Skip very short paragraphs unless they contain critical information
        if len(paragraph) < 10 and not any(kw in paragraph_lower for kw in keywords.keys()):
            continue

        # Check if paragraph explicitly belongs to a category by keywords
        for keyword, section in keywords.items():
            if keyword in paragraph_lower:
                categorized_paragraphs[section].append(paragraph)
                assigned = True
                break

        # If not assigned, add to default category based on text length and content
        if not assigned:
            # By default, longer paragraphs likely describe functional requirements
            if len(paragraph) > 50:
                categorized_paragraphs["Функциональные требования"].append(paragraph)
            else:
                # Add to goals if it looks like a short goal statement
                goal_indicators = ["цель", "предназначен", "задач", "обеспечит", "позволит"]
                if any(indicator in paragraph_lower for indicator in goal_indicators):
                    categorized_paragraphs["Цели и задачи"].append(paragraph)
                else:
                    # As fallback, add to intro
                    categorized_paragraphs["Введение"].append(paragraph)

    # Extract potential timeframes from the text
    timeframe_paragraphs = categorized_paragraphs["Сроки и этапы реализации"]
    timeframe_indicators = ["недель", "месяц", "дней", "день", "срок", "этап", "стадия", "фаза"]

    if not timeframe_paragraphs:
        # Try to find timeframes in other paragraphs
        for section, section_paragraphs in categorized_paragraphs.items():
            if section == "Сроки и этапы реализации":
                continue

            for i, paragraph in enumerate(section_paragraphs):
                if any(indicator in paragraph.lower() for indicator in timeframe_indicators):
                    timeframe_paragraphs.append(paragraph)
                    section_paragraphs.pop(i)

    # Create Introduction subsections
    if categorized_paragraphs["Введение"]:
        intro_paragraphs = categorized_paragraphs["Введение"]
        sections["Введение"] = {
            "Назначение документа": "Данный документ представляет собой техническое задание (ТЗ) на разработку программного обеспечения, описанного ниже.",
            "Область применения": intro_paragraphs[
                0] if intro_paragraphs else "Определяется на основе требований заказчика.",
        }

        # If we have more intro paragraphs, use them
        if len(intro_paragraphs) > 1:
            sections["Введение"]["Общее описание"] = "\n\n".join(intro_paragraphs[1:])
    else:
        # Default introduction
        sections["Введение"] = {
            "Назначение документа": "Данный документ представляет собой техническое задание (ТЗ) на разработку программного обеспечения.",
            "Область применения": "Определяется на основе анализа требований."
        }

    # Create Goals subsections
    if categorized_paragraphs["Цели и задачи"]:
        goals_paragraphs = categorized_paragraphs["Цели и задачи"]

        # First paragraph as main goal
        main_goal = goals_paragraphs[
            0] if goals_paragraphs else "Разработка программного обеспечения в соответствии с требованиями."

        # Extract tasks from remaining paragraphs
        tasks = []
        for i, paragraph in enumerate(goals_paragraphs[1:], 1):
            tasks.append(f"{i}. {paragraph}")

        sections["Цели и задачи"] = {
            "Основная цель": main_goal,
            "Задачи": "\n".join(tasks) if tasks else "Задачи будут определены на основе требований."
        }
    else:
        # Try to generate a goal from the title or first paragraph
        possible_goal = title if title != "Техническое задание" else "Разработка программного обеспечения"
        sections["Цели и задачи"] = {
            "Основная цель": f"Разработка и внедрение системы для {possible_goal.lower()}.",
            "Задачи": "Задачи определяются на основе функциональных требований."
        }

    # Process functional requirements
    func_reqs = categorized_paragraphs["Функциональные требования"]
    if func_reqs:
        # Format as numbered list
        formatted_reqs = []
        for i, req in enumerate(func_reqs, 1):
            formatted_reqs.append(f"{i}. {req}")

        sections["Функциональные требования"] = {
            "Основной функционал": "\n\n".join(formatted_reqs)
        }
    else:
        # If no explicit functional requirements, try to extract from other parts
        all_text = " ".join(paragraphs)
        if "должен" in all_text.lower() or "необходимо" in all_text.lower():
            sections["Функциональные требования"] = {
                "Основной функционал": "Функциональные требования требуют уточнения. На основе предоставленного текста можно предположить, что система должна выполнять следующие функции:\n\n1. Обработка и структурирование текста\n2. Управление моделями для анализа данных"
            }
        else:
            sections["Функциональные требования"] = {
                "Основной функционал": "Функциональные требования будут определены на основе дальнейшего анализа и требований заказчика."
            }

    # Process non-functional requirements
    non_func_reqs = categorized_paragraphs["Нефункциональные требования"]
    if non_func_reqs:
        # Try to categorize non-functional requirements by type
        perf_reqs = []
        security_reqs = []
        compat_reqs = []
        other_reqs = []

        for req in non_func_reqs:
            req_lower = req.lower()
            if any(kw in req_lower for kw in ["производительность", "скорость", "отклик", "время"]):
                perf_reqs.append(req)
            elif any(kw in req_lower for kw in ["безопасность", "защита", "шифрование"]):
                security_reqs.append(req)
            elif any(kw in req_lower for kw in ["совместимость", "интеграция", "поддержка"]):
                compat_reqs.append(req)
            else:
                other_reqs.append(req)

        nf_sections = {}
        if perf_reqs:
            nf_sections["Производительность"] = "\n\n".join(perf_reqs)
        if security_reqs:
            nf_sections["Безопасность"] = "\n\n".join(security_reqs)
        if compat_reqs:
            nf_sections["Совместимость"] = "\n\n".join(compat_reqs)
        if other_reqs:
            nf_sections["Другие требования"] = "\n\n".join(other_reqs)

        if nf_sections:
            sections["Нефункциональные требования"] = nf_sections
        else:
            sections["Нефункциональные требования"] = {
                "Общие нефункциональные требования": "\n\n".join(non_func_reqs)
            }
    else:
        # Default non-functional requirements
        sections["Нефункциональные требования"] = {
            "Производительность": "Система должна обеспечивать приемлемое время отклика при выполнении основных операций.",
            "Безопасность": "Система должна соответствовать основным требованиям информационной безопасности."
        }

    # Process technical requirements
    tech_reqs = categorized_paragraphs["Технические требования"]
    if tech_reqs:
        tech_sections = {
            "Технологический стек": "\n\n".join(tech_reqs)
        }
        sections["Технические требования"] = tech_sections
    else:
        # Default technical requirements
        sections["Технические требования"] = {
            "Платформа": "Определяется на этапе проектирования.",
            "Технологический стек": "Выбор технологического стека осуществляется исполнителем с учетом требований к системе."
        }

    # Process timeframes
    if timeframe_paragraphs:
        # Try to identify discrete phases
        phases = {}
        phase_count = 0

        for para in timeframe_paragraphs:
            # Try to match patterns like "Этап X" or "Фаза X" or numbered items
            import re
            phase_match = re.search(r'(этап|фаза|стадия)\s*[:-]?\s*(\d+|[IVX]+)', para.lower())
            if phase_match:
                phase_num = phase_match.group(2)
                phases[f"Этап {phase_num}"] = para
                phase_count += 1
            else:
                # Add to general timeframe section
                if "Общие сроки" not in phases:
                    phases["Общие сроки"] = para
                else:
                    phases["Общие сроки"] += "\n\n" + para

        # If no phases were found, but we have timeframe information
        if phase_count == 0 and timeframe_paragraphs:
            sections["Сроки и этапы реализации"] = {
                "Общие сроки": "\n\n".join(timeframe_paragraphs)
            }
        else:
            sections["Сроки и этапы реализации"] = phases
    else:
        # Default timeframes
        sections["Сроки и этапы реализации"] = {
            "Предварительные сроки": "Сроки реализации проекта определяются на этапе планирования.",
            "Этапы": "1. Анализ и проектирование\n2. Разработка\n3. Тестирование\n4. Внедрение"
        }

    # Format as markdown with enhanced structure
    result = f"# {title}\n\n"

    for section, subsections in sections.items():
        result += f"## {section}\n\n"

        if isinstance(subsections, dict):
            for subsection, content in subsections.items():
                result += f"### {subsection}\n\n{content}\n\n"
        else:
            result += f"{subsections}\n\n"

    logger.info("Enhanced text analysis processing completed")
    return result


def process_text_async(text, template_type="technical_specification", temperature=0.1, max_tokens=5000):
    """
    Simulate async LLM processing with deterministic fallback
    """
    job_id = f"job_{int(time.time())}_{hash(text) % 10000}"
    logger.info(f"Created job: {job_id}")

    # Create job structure
    job = {
        "job_id": job_id,
        "text": text,
        "template_type": template_type,
        "status": "processing",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "timestamp": time.time()
    }

    # Store in memory cache
    _job_results[job_id] = job

    # Save to file
    result_file = os.path.join(TEMP_DIR, f"{job_id}.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

    # Start processing in a separate thread
    thread = threading.Thread(target=_process_job, args=(job_id, text, template_type))
    thread.daemon = True
    thread.start()

    return job_id


def _process_job(job_id, text, template_type):
    """Process a job in a separate thread"""
    try:
        logger.info(f"Processing job {job_id}")

        # Simulate processing time (3-5 seconds)
        time.sleep(3)

        # Process text with rule-based approach
        result_text = process_simple_text(text)

        # Update job status
        job = _job_results.get(job_id, {
            "job_id": job_id,
            "text": text,
            "template_type": template_type,
            "status": "processing",
            "timestamp": time.time()
        })

        job["status"] = "completed"
        job["completion_time"] = time.time()
        job["processing_time"] = job["completion_time"] - job["timestamp"]
        job["result"] = {
            "success": True,
            "text": result_text,
            "processing_time": job["processing_time"],
            "template_type": template_type
        }

        # Update in-memory cache
        _job_results[job_id] = job

        # Save to file
        result_file = os.path.join(TEMP_DIR, f"{job_id}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # Update job as failed
        job = _job_results.get(job_id, {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        })

        job["status"] = "failed"
        job["completion_time"] = time.time()
        job["error"] = str(e)

        # Update in-memory cache
        _job_results[job_id] = job

        # Save to file
        result_file = os.path.join(TEMP_DIR, f"{job_id}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False, indent=2)


def get_job_status(job_id):
    """Get status of a processing job"""
    logger.info(f"Checking status for job: {job_id}")

    # First check in-memory cache
    if job_id in _job_results:
        logger.info(f"Found job in memory cache with status: {_job_results[job_id].get('status', 'unknown')}")
        return _job_results[job_id]

    # Then check file
    result_file = os.path.join(TEMP_DIR, f"{job_id}.json")
    if os.path.exists(result_file):
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                job = json.load(f)

            # Add to memory cache
            _job_results[job_id] = job

            logger.info(f"Found job in file with status: {job.get('status', 'unknown')}")
            return job
        except Exception as e:
            logger.error(f"Error reading job file: {str(e)}")
            return {"status": "error", "job_id": job_id, "error": str(e)}

    logger.warning(f"Job not found: {job_id}")
    return {"status": "not_found", "job_id": job_id}


# Dummy functions to maintain API compatibility
def initialize_model(config=None):
    """Dummy function to maintain API compatibility"""
    logger.info("Using simplified LLM processor (rule-based)")
    return True


def process_text(text, template_type="technical_specification", temperature=0.1, max_tokens=5000):
    """Direct text processing function"""
    logger.info(f"Direct processing with template: {template_type}")

    try:
        # Process with rule-based approach
        result_text = process_simple_text(text)

        return {
            "success": True,
            "text": result_text,
            "processing_time": 1.0,
            "template_type": template_type
        }
    except Exception as e:
        logger.error(f"Error in direct processing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        return {
            "success": False,
            "error": str(e),
            "text": "",
            "processing_time": 0
        }


def get_available_templates():
    """Get available templates"""
    return [
        {"id": "technical_specification", "name": "Техническое задание",
         "description": "Стандартное техническое задание с разделами: введение, цели, требования и сроки."},
        {"id": "project_brief", "name": "Краткое описание проекта",
         "description": "Краткое описание проекта с основными целями и задачами."},
        {"id": "software_architecture", "name": "Архитектура ПО",
         "description": "Описание архитектуры программного обеспечения с компонентами и взаимодействиями."}
    ]