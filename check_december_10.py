#!/usr/bin/env python
"""
Скрипт для проверки данных за 10 декабря.
Проверяет, почему записи за эту дату не попадают в отчет.
"""
import os
import sys

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
from camera_events.models import EntryExit, Employee, CameraEvent
from camera_events.utils import clean_id
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_december_10(employee_id=None):
    """
    Проверяет данные за 10 декабря 2025.
    """
    target_date = date(2025, 12, 10)
    start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
    
    print("=" * 80)
    print(f"ПРОВЕРКА ДАННЫХ ЗА {target_date.strftime('%d.%m.%Y')}")
    print("=" * 80)
    
    # 1. Проверяем CameraEvent (исходные события)
    print("\n1. ИСХОДНЫЕ СОБЫТИЯ (CameraEvent):")
    print("-" * 80)
    
    camera_events = CameraEvent.objects.filter(
        event_time__gte=start_datetime,
        event_time__lt=end_datetime
    )
    
    if employee_id:
        clean_id_str = clean_id(employee_id)
        camera_events = camera_events.filter(
            hikvision_id__in=[clean_id_str, employee_id]
        )
    
    camera_events = camera_events.order_by('hikvision_id', 'event_time')
    
    events_by_employee = {}
    for event in camera_events:
        if event.hikvision_id not in events_by_employee:
            events_by_employee[event.hikvision_id] = []
        
        local_time = timezone.localtime(event.event_time)
        events_by_employee[event.hikvision_id].append({
            'time': local_time,
            'device': event.device_name or 'Не указано',
            'raw_data': event.raw_data
        })
    
    if not events_by_employee:
        print("  ⚠️ Нет событий CameraEvent за эту дату")
    else:
        for hikvision_id, events in events_by_employee.items():
            try:
                employee = Employee.objects.filter(hikvision_id=hikvision_id).first()
                emp_name = employee.name if employee else f"ID: {hikvision_id}"
                print(f"\n  Сотрудник: {emp_name} (ID: {hikvision_id})")
                for event in events:
                    print(f"    {event['time'].strftime('%H:%M:%S')} | {event['device']}")
            except Exception as e:
                print(f"  Ошибка при обработке сотрудника {hikvision_id}: {e}")
    
    # 2. Проверяем EntryExit (рассчитанные записи)
    print("\n2. РАССЧИТАННЫЕ ЗАПИСИ (EntryExit):")
    print("-" * 80)
    
    # Записи, где вход 10 декабря
    entry_exits_entry = EntryExit.objects.filter(
        entry_time__isnull=False,
        entry_time__gte=start_datetime,
        entry_time__lt=end_datetime
    )
    
    # Записи, где выход 10 декабря (но вход может быть 9 декабря)
    entry_exits_exit = EntryExit.objects.filter(
        exit_time__isnull=False,
        exit_time__gte=start_datetime,
        exit_time__lt=end_datetime
    )
    
    if employee_id:
        clean_id_str = clean_id(employee_id)
        entry_exits_entry = entry_exits_entry.filter(
            hikvision_id__in=[clean_id_str, employee_id]
        )
        entry_exits_exit = entry_exits_exit.filter(
            hikvision_id__in=[clean_id_str, employee_id]
        )
    
    print("\n  Записи с ВХОДОМ 10 декабря:")
    entry_exits_entry_list = list(entry_exits_entry.order_by('hikvision_id', 'entry_time'))
    if not entry_exits_entry_list:
        print("    ⚠️ Нет записей с входом 10 декабря")
    else:
        for ee in entry_exits_entry_list:
            try:
                employee = Employee.objects.filter(hikvision_id=ee.hikvision_id).first()
                emp_name = employee.name if employee else f"ID: {ee.hikvision_id}"
                
                entry_local = timezone.localtime(ee.entry_time) if ee.entry_time else None
                exit_local = timezone.localtime(ee.exit_time) if ee.exit_time else None
                
                entry_str = entry_local.strftime('%H:%M:%S') if entry_local else 'НЕТ'
                exit_str = exit_local.strftime('%Y-%m-%d %H:%M:%S') if exit_local else 'НЕТ'
                
                print(f"    {emp_name} (ID: {ee.hikvision_id})")
                print(f"      Вход: {entry_str}")
                print(f"      Выход: {exit_str}")
                if ee.exit_time:
                    duration = ee.exit_time - ee.entry_time
                    print(f"      Продолжительность: {duration}")
                else:
                    print(f"      ⚠️ НЕТ ВЫХОДА - запись неполная!")
            except Exception as e:
                print(f"    Ошибка при обработке записи EntryExit id={ee.id}: {e}")
    
    print("\n  Записи с ВЫХОДОМ 10 декабря (вход может быть 9 декабря):")
    entry_exits_exit_list = list(entry_exits_exit.order_by('hikvision_id', 'exit_time'))
    if not entry_exits_exit_list:
        print("    ⚠️ Нет записей с выходом 10 декабря")
    else:
        for ee in entry_exits_exit_list:
            try:
                employee = Employee.objects.filter(hikvision_id=ee.hikvision_id).first()
                emp_name = employee.name if employee else f"ID: {ee.hikvision_id}"
                
                entry_local = timezone.localtime(ee.entry_time) if ee.entry_time else None
                exit_local = timezone.localtime(ee.exit_time) if ee.exit_time else None
                
                entry_str = entry_local.strftime('%Y-%m-%d %H:%M:%S') if entry_local else 'НЕТ'
                exit_str = exit_local.strftime('%H:%M:%S') if exit_local else 'НЕТ'
                
                print(f"    {emp_name} (ID: {ee.hikvision_id})")
                print(f"      Вход: {entry_str}")
                print(f"      Выход: {exit_str}")
            except Exception as e:
                print(f"    Ошибка при обработке записи EntryExit id={ee.id}: {e}")
    
    # 3. Проверяем, какие записи попадут в отчет
    print("\n3. АНАЛИЗ ДЛЯ ОТЧЕТА:")
    print("-" * 80)
    
    # Записи, которые должны попасть в отчет за 10 декабря
    # Это записи с входом 10 декабря И с выходом
    valid_entries = EntryExit.objects.filter(
        entry_time__isnull=False,
        exit_time__isnull=False,
        entry_time__gte=start_datetime,
        entry_time__lt=end_datetime
    )
    
    if employee_id:
        clean_id_str = clean_id(employee_id)
        valid_entries = valid_entries.filter(
            hikvision_id__in=[clean_id_str, employee_id]
        )
    
    valid_entries_list = list(valid_entries.order_by('hikvision_id', 'entry_time'))
    
    print(f"\n  Записей, которые ДОЛЖНЫ попасть в отчет за 10 декабря: {len(valid_entries_list)}")
    
    if not valid_entries_list:
        print("\n  ⚠️ ПРОБЛЕМА: Нет записей EntryExit с входом И выходом за 10 декабря!")
        print("  Возможные причины:")
        print("    1. Нет записей с входом 10 декабря")
        print("    2. Записи с входом 10 декабря не имеют выхода (exit_time IS NULL)")
        print("    3. Записи были удалены или не созданы")
    else:
        print("\n  Записи, которые попадут в отчет:")
        for ee in valid_entries_list:
            try:
                employee = Employee.objects.filter(hikvision_id=ee.hikvision_id).first()
                emp_name = employee.name if employee else f"ID: {ee.hikvision_id}"
                
                entry_local = timezone.localtime(ee.entry_time)
                exit_local = timezone.localtime(ee.exit_time)
                
                period_date = entry_local.date()
                
                print(f"    {emp_name} (ID: {ee.hikvision_id})")
                print(f"      period_date (дата отчета): {period_date}")
                print(f"      Вход: {entry_local.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      Выход: {exit_local.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if period_date != target_date:
                    print(f"      ⚠️ ВНИМАНИЕ: period_date ({period_date}) не совпадает с целевой датой ({target_date})!")
            except Exception as e:
                print(f"    Ошибка при обработке записи EntryExit id={ee.id}: {e}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    import argparse
    from datetime import timedelta
    
    parser = argparse.ArgumentParser(description='Проверка данных за 10 декабря')
    parser.add_argument(
        '--employee-id',
        type=str,
        help='ID сотрудника для фильтрации (например, 00000025)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        check_december_10(employee_id=args.employee_id)
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        sys.exit(1)






