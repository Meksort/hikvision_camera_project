#!/usr/bin/env python
"""
Скрипт для пересчета записей EntryExit из CameraEvent.
Можно запускать локально без Docker.

Использование:
    python recalculate_entries_exits.py
    python recalculate_entries_exits.py --start-date 2025-12-22
    python recalculate_entries_exits.py --start-date 2025-12-22 --end-date 2025-12-22
"""
import os
import sys
import argparse

# Настройка кодировки для Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import django
from datetime import datetime

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from django.utils import timezone
from camera_events.views import recalculate_entries_exits
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Пересчет записей EntryExit из CameraEvent')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Дата начала пересчета в формате YYYY-MM-DD (по умолчанию: 2025-12-22)',
        default='2025-12-22'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Дата окончания пересчета в формате YYYY-MM-DD (по умолчанию: та же дата, что и start-date)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Парсим даты
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = timezone.make_aware(start_date)
    except ValueError:
        logger.error(f"Неверный формат даты начала: {args.start_date}. Используйте YYYY-MM-DD")
        return
    
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            end_date = timezone.make_aware(end_date)
        except ValueError:
            logger.error(f"Неверный формат даты окончания: {args.end_date}. Используйте YYYY-MM-DD")
            return
    else:
        # Если end_date не указан, используем ту же дату, что и start_date
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    logger.info("=" * 80)
    logger.info(f"НАЧАЛО ПЕРЕСЧЕТА ENTRYEXIT")
    logger.info(f"Период: {start_date.strftime('%Y-%m-%d %H:%M:%S')} - {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        result = recalculate_entries_exits(start_date=start_date, end_date=end_date)
        
        logger.info("=" * 80)
        logger.info("ПЕРЕСЧЕТ ЗАВЕРШЕН")
        logger.info(f"Создано записей: {result.get('created', 0)}")
        logger.info(f"Обновлено записей: {result.get('updated', 0)}")
        if result.get('error'):
            logger.error(f"Ошибка: {result.get('error')}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА при пересчете: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()


