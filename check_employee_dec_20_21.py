#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для проверки данных за 20 и 21 декабря 2025 года для сотрудника "Абай Нурлан".
"""
import os
import sys
import django

print("Инициализация Django...")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')

try:
    django.setup()
    print("Django инициализирован успешно")
except Exception as e:
    print(f"Ошибка инициализации Django: {e}")
    sys.exit(1)

from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Q
from camera_events.models import CameraEvent, EntryExit, Employee

def main():
    print("\n" + "=" * 80)
    print("ПОИСК СОТРУДНИКА 'Абай Нурлан'")
    print("=" * 80)
    
    # Ищем сотрудника разными способами
    employee = None
    search_names = ["Абай Нурлан", "Абай", "Нурлан"]
    
    for name in search_names:
        employee = Employee.objects.filter(name__icontains=name).first()
        if employee:
            print(f"✓ Найден сотрудник: {employee.name} (ID: {employee.hikvision_id})")
            break
    
    if not employee:
        print("❌ Сотрудник не найден. Показываю первые 20 сотрудников:")
        for emp in Employee.objects.all()[:20]:
            print(f"  - {emp.name} (ID: {emp.hikvision_id})")
        return
    
    hikvision_id = employee.hikvision_id
    dept = employee.department.get_full_path() if employee.department else (employee.department_old or 'Не указано')
    
    print(f"\nПодразделение: {dept}")
    print("=" * 80)
    
    # Проверяем обе даты
    for target_date in [date(2025, 12, 20), date(2025, 12, 21)]:
        print("\n" + "=" * 80)
        print(f"ДАТА: {target_date.strftime('%d.%m.%Y')} ({['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][target_date.weekday()]})")
        print("=" * 80)
        
        start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
        
        # 1. CameraEvent (сырые события)
        print("\n1. СЫРЫЕ СОБЫТИЯ (CameraEvent):")
        print("-" * 80)
        
        camera_events = CameraEvent.objects.filter(
            hikvision_id=hikvision_id,
            event_time__gte=start_datetime,
            event_time__lt=end_datetime
        ).order_by('event_time')
        
        if camera_events.count() == 0:
            print("  ⚠️ Нет событий за эту дату")
        else:
            for event in camera_events:
                local_time = timezone.localtime(event.event_time)
                device = event.device_name or "Не указано"
                
                # Определяем тип события
                event_type = "?"
                if event.raw_data:
                    raw_str = str(event.raw_data)
                    if "192.168.1.143" in raw_str or "143" in raw_str or "выход" in device.lower():
                        event_type = "ВЫХОД"
                    elif "192.168.1.124" in raw_str or "124" in raw_str or "вход" in device.lower():
                        event_type = "ВХОД"
                
                print(f"  {local_time.strftime('%H:%M:%S')} | {event_type:6s} | {device}")
        
        # 2. EntryExit (рассчитанные записи)
        print("\n2. РАССЧИТАННЫЕ ЗАПИСИ (EntryExit):")
        print("-" * 80)
        
        entry_exits = EntryExit.objects.filter(
            hikvision_id=hikvision_id
        ).filter(
            Q(entry_time__gte=start_datetime, entry_time__lt=end_datetime) |
            Q(exit_time__gte=start_datetime, exit_time__lt=end_datetime)
        ).order_by('entry_time')
        
        if entry_exits.count() == 0:
            print("  ⚠️ Нет записей EntryExit за эту дату")
        else:
            for ee in entry_exits:
                entry_str = timezone.localtime(ee.entry_time).strftime('%H:%M:%S') if ee.entry_time else "НЕТ"
                exit_str = timezone.localtime(ee.exit_time).strftime('%H:%M:%S') if ee.exit_time else "НЕТ"
                duration = ee.work_duration_formatted if hasattr(ee, 'work_duration_formatted') and ee.work_duration_seconds else "0ч 0м"
                
                status = "✅" if ee.entry_time and ee.exit_time else "⚠️"
                print(f"  {status} Вход: {entry_str:8s} | Выход: {exit_str:8s} | Продолжительность: {duration}")
        
        print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n❌ ОШИБКА: {e}")
        traceback.print_exc()

