#!/usr/bin/env python
"""
Скрипт для исправления времени входа в записях EntryExit.
Пересчитывает записи EntryExit из исходных событий CameraEvent, чтобы гарантировать правильность данных.

Использование:
    python fix_entry_times.py
    python fix_entry_times.py --start-date 2025-12-01 --end-date 2025-12-31
    python fix_entry_times.py --employee-id 00000025
"""
import os
import sys
import argparse

# Настройка кодировки для Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import django
from datetime import datetime, date

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from camera_events.models import EntryExit, Employee, CameraEvent
from camera_events.views import recalculate_entries_exits
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def fix_entry_times(start_date=None, end_date=None, employee_id=None):
    """
    Пересчитывает записи EntryExit из исходных событий CameraEvent.
    Это гарантирует правильность данных, используя самое раннее время входа за каждый день.
    
    Args:
        start_date: Дата начала (по умолчанию: 2025-12-01)
        end_date: Дата окончания (по умолчанию: текущая дата)
        employee_id: ID сотрудника для фильтрации (опционально)
    """
    if start_date is None:
        today = timezone.now().date()
        start_date = datetime(today.year, 12, 1).date()
    
    if end_date is None:
        end_date = timezone.now().date()
    
    # Конвертируем в datetime с временем
    start_datetime = datetime.combine(start_date, datetime.min.time())
    start_datetime = timezone.make_aware(start_datetime)
    end_datetime = datetime.combine(end_date, datetime.max.time())
    end_datetime = timezone.make_aware(end_datetime)
    
    logger.info("=" * 80)
    logger.info("ПЕРЕСЧЕТ ЗАПИСЕЙ ENTRYEXIT ИЗ ИСХОДНЫХ СОБЫТИЙ CAMERAEVENT")
    logger.info(f"Период: {start_date} - {end_date}")
    if employee_id:
        logger.info(f"Сотрудник: {employee_id}")
        # Если указан сотрудник, сначала удаляем его старые записи за этот период
        clean_id = employee_id.lstrip('0') or '0'
        deleted_count = EntryExit.objects.filter(
            hikvision_id__in=[clean_id, employee_id],
            entry_time__gte=start_datetime,
            entry_time__lte=end_datetime
        ).delete()[0]
        logger.info(f"Удалено старых записей EntryExit: {deleted_count}")
    logger.info("=" * 80)
    
    # Пересчитываем записи из исходных событий
    try:
        result = recalculate_entries_exits(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        logger.info("=" * 80)
        logger.info("ПЕРЕСЧЕТ ЗАВЕРШЕН")
        logger.info(f"Создано записей: {result.get('created', 0)}")
        logger.info(f"Обновлено записей: {result.get('updated', 0)}")
        if result.get('error'):
            logger.error(f"Ошибка: {result.get('error')}")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при пересчете: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Исправление времени входа в записях EntryExit')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Дата начала в формате YYYY-MM-DD (по умолчанию: 2025-12-01)',
        default='2025-12-01'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Дата окончания в формате YYYY-MM-DD (по умолчанию: текущая дата)',
        default=None
    )
    parser.add_argument(
        '--employee-id',
        type=str,
        help='ID сотрудника для фильтрации (например, 00000025)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Парсим даты
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Неверный формат даты начала: {args.start_date}. Используйте YYYY-MM-DD")
        return
    
    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Неверный формат даты окончания: {args.end_date}. Используйте YYYY-MM-DD")
            return
    
    try:
        result = fix_entry_times(
            start_date=start_date,
            end_date=end_date,
            employee_id=args.employee_id
        )
        
        logger.info(f"Результат: создано {result.get('created', 0)} записей, обновлено {result.get('updated', 0)} записей")
        
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

