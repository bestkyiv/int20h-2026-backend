
from logging_singleton import get_logger

# Import your routers here

logger = get_logger(__name__)

# --- 1. DEFINE CUSTOM MESSAGES ---
# Maps field names to error types (e.g., 'missing', 'string_too_short', etc.)
CUSTOM_ERROR_MESSAGES = {
    # --- Text Fields ---
    "full_name": {
        "missing": "Будь ласка, введіть ваше ім'я.",
        "string_too_short": "Ім'я має містити щонайменше 2 символи.",
        "string_too_long": "Ім'я занадто довге (максимум 100 символів).",
    },
    "email": {
        "missing": "Будь ласка, введіть Email.",
        "string_too_long": "Email занадто довгий (максимум 100 символів).",
    },
    "telegram": {
        "missing": "Будь ласка, введіть Telegram нікнейм.",
        "string_too_short": "Telegram нікнейм не може бути порожнім.",
        "string_too_long": "Telegram нікнейм занадто довгий (максимум 100 символів).",
    },
    "phone": {
        "missing": "Будь ласка, введіть номер телефону.",
        "string_too_long": "Номер телефону занадто довгий.",
        "value_error": "Невірний формат номеру телефону.",  # Catches normalize_phone_number errors
    },
    "team_name": {
        "string_too_long": "Назва команди занадто довга (максимум 100 символів)."
    },
    "job_description": {
        "string_too_long": "Опис роботи не може перевищувати 2000 символів."
    },
    "source": {
        "missing": "Будь ласка, вкажіть, звідки ви дізналися про подію.",
        "string_too_short": "Поле джерела не може бути порожнім.",
        "string_too_long": "Текст джерела занадто довгий (максимум 100 символів).",
    },
    "otherSource": {
        "string_too_long": "Текст іншого джерела занадто довгий (максимум 100 символів)."
    },
    "comment": {"string_too_long": "Коментар занадто довгий (максимум 2000 символів)."},
    # --- Links ---
    "cv": {"string_too_long": "Посилання на CV занадто довге (максимум 100 символів)."},
    "linkedin": {
        "string_too_long": "Посилання на LinkedIn занадто довге (максимум 100 символів)."
    },
    # --- Dropdowns / Enums / IDs ---
    "category_id": {
        "missing": "Будь ласка, оберіть категорію.",
        "int_parsing": "ID категорії має бути числом.",
    },
    "study_year": {
        "missing": "Будь ласка, вкажіть ваш курс.",
        "enum": "Оберіть коректний курс зі списку.",
        "int_parsing": "Курс має бути числом.",
    },
    "format": {
        "missing": "Будь ласка, оберіть формат участі.",
        "enum": "Оберіть 'online' або 'offline'.",
    },
    # --- Booleans ---
    "has_team": {
        "missing": "Вкажіть, чи є у вас команда.",
        "bool_parsing": "Очікується логічне значення (true/false).",
    },
    "team_leader": {
        "missing": "Вкажіть, чи ви є лідером команди.",
        "bool_parsing": "Очікується логічне значення (true/false).",
    },
    "wants_job": {
        "missing": "Вкажіть, чи ви шукаєте роботу.",
        "bool_parsing": "Очікується логічне значення (true/false).",
    },
    "work_consent": {
        "missing": "Вкажіть згоду на умови роботи.",
        "bool_parsing": "Очікується логічне значення (true/false).",
    },
    # --- Arrays ---
    "skills": {
        "missing": "Будь ласка, вкажіть хоча б одну навичку.",
        "list_type": "Навички мають бути списком.",
    },
    # --- Consent ---
    "personal_data_consent": {
        "missing": "Необхідна згода на обробку персональних даних.",
        "literal_error": "Необхідна згода на обробку персональних даних.",
    },
}
