"""
Утилиты для работы с событиями камер Hikvision.
"""
from django.utils import timezone
from django.db.models import Q
from .models import Employee

# Попытка использовать zoneinfo (Python 3.9+), иначе используем настройки Django
try:
    from zoneinfo import ZoneInfo
    ALMATY_TZ = ZoneInfo('Asia/Almaty')
except ImportError:
    # Для Python < 3.9 используем настройки Django
    ALMATY_TZ = None


# Константы для дней недели
WEEKDAYS_SHORT = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']

# Маппинг типов графиков на русские названия
SCHEDULE_TYPE_MAP = {
    'regular': 'Обычный график',
    'floating': 'Плавающий график',
    'round_the_clock': 'Круглосуточный'
}

# Список подразделений для исключения
EXCLUDED_DEPARTMENTS = [
    "Маникюр Педикюр",
    "Массажистки ЖКБ",
    "Тренера и Инструкторы",
    "Массажист МКБ",
    "Массажистка МКБ",
    "Массажистки",
    "Косметолог",
    "Парильщицы ЖКБ",
    "Парильщик МКБ",
]


def clean_id(id_str):
    """Удаляет ведущие нули из ID."""
    if not id_str:
        return None
    s = str(id_str).strip()
    if s.replace('0', '') == '':
        return "0"
    return s.lstrip('0') or "0"


def ensure_aware(dt):
    """
    Преобразует наивный datetime в timezone-aware datetime.
    Если datetime уже aware, возвращает его без изменений.
    """
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def get_excluded_hikvision_ids():
    """
    Возвращает список hikvision_id сотрудников из исключенных подразделений.
    """
    employees = Employee.objects.filter(
        Q(department__name__in=EXCLUDED_DEPARTMENTS) | 
        Q(department_old__in=EXCLUDED_DEPARTMENTS)
    )
    return list(employees.values_list('hikvision_id', flat=True).exclude(hikvision_id__isnull=True))
