#!/usr/bin/env python
"""
Скрипт для проверки данных за 20 и 21 декабря 2025 года для сотрудника "Абай Нурлан".
Проверяет все события CameraEvent и записи EntryExit за эти даты.
"""
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Q
from camera_events.models import CameraEvent, EntryExit, Employee
from collections import defaultdict

def check_december_20_21():
    """Проверяет все данные за 20 и 21 декабря 2025 года для сотрудника 'Абай Нурлан'."""
    
    # Ищем сотрудника
    employee_name = "Абай Нурлан"
    employee = Employee.objects.filter(name__icontains=employee_name).first()
    
    if not employee:
        print(f"❌ Сотрудник '{employee_name}' не найден в базе данных!")
        print("\nДоступные сотрудники с похожими именами:")
        similar = Employee.objects.filter(name__icontains="Абай") | Employee.objects.filter(name__icontains="Нурлан")
        for emp in similar[:10]:
            print(f"  - {emp.name} (ID: {emp.hikvision_id})")
        return
    
    print("=" * 80)
    print(f"ПРОВЕРКА ДАННЫХ ЗА 20 И 21 ДЕКАБРЯ 2025")
    print(f"Сотрудник: {employee.name} (ID: {employee.hikvision_id})")
    print(f"Подразделение: {employee.department.get_full_path() if employee.department else (employee.department_old or 'Не указано')}")
    print("=" * 80)
    print()
    
    hikvision_id = employee.hikvision_id
    
    # Проверяем обе даты
    for target_date in [date(2025, 12, 20), date(2025, 12, 21)]:
        start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
        
        print("=" * 80)
        print(f"ДАТА: {target_date.strftime('%d.%m.%Y (%A)')}")
        print("=" * 80)
        print()
        
        # 1. Проверяем CameraEvent (сырые события)
        print("1. СЫРЫЕ СОБЫТИЯ ИЗ CAMERA EVENT:")
        print("-" * 80)
        
        camera_events = CameraEvent.objects.filter(
            hikvision_id=hikvision_id,
            event_time__gte=start_datetime,
            event_time__lt=end_datetime
        ).order_by('event_time')
        
        print(f"Всего событий: {camera_events.count()}")
        print()
        
        if camera_events.count() == 0:
            print("  ⚠️ Нет событий CameraEvent за эту дату")
        else:
            for event in camera_events:
                local_time = timezone.localtime(event.event_time)
                device_info = event.device_name or "Не указано"
                
                # Пытаемся определить тип события
                event_type = "Не определен"
                camera_ip = None
                
                # Извлекаем IP из raw_data
                if event.raw_data and isinstance(event.raw_data, dict):
                    outer_event = event.raw_data.get("AccessControllerEvent", {})
                    if isinstance(outer_event, dict):
                        if "AccessControllerEvent" in outer_event:
                            inner_event = outer_event["AccessControllerEvent"]
                            if isinstance(inner_event, dict):
                                camera_ip = (
                                    inner_event.get("ipAddress") or
                                    inner_event.get("remoteHostAddr") or
                                    inner_event.get("ip") or
                                    None
                                )
                        if not camera_ip:
                            camera_ip = (
                                outer_event.get("ipAddress") or
                                outer_event.get("remoteHostAddr") or
                                outer_event.get("ip") or
                                None
                            )
                    if not camera_ip:
                        camera_ip = (
                            event.raw_data.get("ipAddress") or
                            event.raw_data.get("remoteHostAddr") or
                            event.raw_data.get("ip") or
                            None
                        )
                
                # Определяем тип по IP
                if camera_ip:
                    camera_ip_str = str(camera_ip)
                    if "192.168.1.143" in camera_ip_str or "143" in camera_ip_str:
                        event_type = "ВЫХОД"
                    elif "192.168.1.124" in camera_ip_str or "124" in camera_ip_str:
                        event_type = "ВХОД"
                    else:
                        event_type = f"IP: {camera_ip}"
                
                # Если не определили по IP, проверяем device_name
                if event_type == "Не определен":
                    device_lower = device_info.lower()
                    if any(word in device_lower for word in ['вход', 'entry', 'входная', 'вход 1', 'вход1', '124']):
                        event_type = "ВХОД"
                    elif any(word in device_lower for word in ['выход', 'exit', 'выходная', 'выход 1', 'выход1', '143']):
                        event_type = "ВЫХОД"
                
                print(f"  - {local_time.strftime('%d.%m.%Y %H:%M:%S')} | {event_type} | Устройство: {device_info}")
        
        print()
        print("-" * 80)
        
        # 2. Проверяем EntryExit (рассчитанные записи)
        print("2. РАССЧИТАННЫЕ ЗАПИСИ ENTRYEXIT:")
        print("-" * 80)
        
        entry_exits = EntryExit.objects.filter(
            hikvision_id=hikvision_id
        ).filter(
            Q(entry_time__gte=start_datetime, entry_time__lt=end_datetime) |
            Q(exit_time__gte=start_datetime, exit_time__lt=end_datetime)
        ).order_by('entry_time')
        
        print(f"Всего записей EntryExit: {entry_exits.count()}")
        print()
        
        if entry_exits.count() == 0:
            print("  ⚠️ Нет записей EntryExit за эту дату")
        else:
            for entry_exit in entry_exits:
                entry_local = timezone.localtime(entry_exit.entry_time) if entry_exit.entry_time else None
                exit_local = timezone.localtime(entry_exit.exit_time) if entry_exit.exit_time else None
                
                entry_str = entry_local.strftime('%d.%m.%Y %H:%M:%S') if entry_local else "НЕТ"
                exit_str = exit_local.strftime('%d.%m.%Y %H:%M:%S') if exit_local else "НЕТ"
                duration_str = entry_exit.work_duration_formatted if entry_exit.work_duration_seconds else "0ч 0м"
                
                status = "✅ ПОЛНЫЙ" if entry_exit.entry_time and entry_exit.exit_time else "⚠️ НЕПОЛНЫЙ"
                
                print(f"  {status}")
                print(f"    Вход:  {entry_str}")
                print(f"    Выход: {exit_str}")
                print(f"    Продолжительность работы: {duration_str}")
                print()
        
        print()
        print("=" * 80)
        print()
    
    print("=" * 80)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80)

if __name__ == "__main__":
    try:
        check_december_20_21()
    except Exception as e:
        import traceback
        print(f"❌ ОШИБКА: {e}")
        print("\nДетали ошибки:")
        traceback.print_exc()

