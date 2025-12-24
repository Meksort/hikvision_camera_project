#!/usr/bin/env python
"""
Скрипт для проверки данных за 22 декабря 2025 года.
Проверяет все события CameraEvent и записи EntryExit за эту дату.
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

def check_december_22():
    """Проверяет все данные за 22 декабря 2025 года."""
    
    target_date = date(2025, 12, 22)
    start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(target_date + timedelta(days=1), datetime.min.time()))
    
    print("=" * 80)
    print(f"ПРОВЕРКА ДАННЫХ ЗА {target_date.strftime('%d.%m.%Y')}")
    print("=" * 80)
    print()
    
    # 1. Проверяем CameraEvent (сырые события)
    print("1. СЫРЫЕ СОБЫТИЯ ИЗ CAMERA EVENT:")
    print("-" * 80)
    
    camera_events = CameraEvent.objects.filter(
        event_time__gte=start_datetime,
        event_time__lt=end_datetime,
        hikvision_id__isnull=False
    ).order_by('hikvision_id', 'event_time')
    
    events_by_employee = defaultdict(list)
    for event in camera_events:
        events_by_employee[event.hikvision_id].append(event)
    
    print(f"Всего событий: {camera_events.count()}")
    print(f"Уникальных сотрудников: {len(events_by_employee)}")
    print()
    
    # Выводим детали по каждому сотруднику
    for hikvision_id, events in sorted(events_by_employee.items()):
        employee = Employee.objects.filter(hikvision_id=hikvision_id).first()
        employee_name = employee.name if employee else "Неизвестный"
        
        print(f"  Сотрудник: {employee_name} (ID: {hikvision_id})")
        print(f"    Событий: {len(events)}")
        
        for event in events:
            local_time = timezone.localtime(event.event_time)
            device_info = event.device_name or "Не указано"
            
            # Пытаемся определить тип события (та же логика, что в recalculate_entries_exits)
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
            
            print(f"    - {local_time.strftime('%H:%M:%S')} | {event_type} | Устройство: {device_info}")
        
        print()
    
    print()
    print("=" * 80)
    
    # 2. Проверяем EntryExit (рассчитанные записи)
    print("2. РАССЧИТАННЫЕ ЗАПИСИ ENTRYEXIT:")
    print("-" * 80)
    
    entry_exits = EntryExit.objects.filter(
        Q(entry_time__gte=start_datetime, entry_time__lt=end_datetime) |
        Q(exit_time__gte=start_datetime, exit_time__lt=end_datetime)
    ).order_by('hikvision_id', 'entry_time')
    
    print(f"Всего записей EntryExit: {entry_exits.count()}")
    print()
    
    entry_exits_by_employee = defaultdict(list)
    for entry_exit in entry_exits:
        entry_exits_by_employee[entry_exit.hikvision_id].append(entry_exit)
    
    for hikvision_id, entries in sorted(entry_exits_by_employee.items()):
        employee = Employee.objects.filter(hikvision_id=hikvision_id).first()
        employee_name = employee.name if employee else "Неизвестный"
        
        print(f"  Сотрудник: {employee_name} (ID: {hikvision_id})")
        
        for entry_exit in entries:
            entry_local = timezone.localtime(entry_exit.entry_time) if entry_exit.entry_time else None
            exit_local = timezone.localtime(entry_exit.exit_time) if entry_exit.exit_time else None
            
            entry_str = entry_local.strftime('%H:%M:%S') if entry_local else "НЕТ"
            exit_str = exit_local.strftime('%H:%M:%S') if exit_local else "НЕТ"
            duration_str = entry_exit.work_duration_formatted if entry_exit.work_duration_seconds else "0ч 0м"
            
            status = "✅ ПОЛНЫЙ" if entry_exit.entry_time and entry_exit.exit_time else "⚠️ НЕПОЛНЫЙ"
            
            print(f"    {status} | Вход: {entry_str} | Выход: {exit_str} | Продолжительность: {duration_str}")
        
        print()
    
    print()
    print("=" * 80)
    
    # 3. Сравнение: кто есть в CameraEvent, но нет в EntryExit или неполный
    print("3. ПРОБЛЕМНЫЕ СЛУЧАИ (есть события, но нет полной записи EntryExit):")
    print("-" * 80)
    
    problems_found = False
    
    for hikvision_id in events_by_employee.keys():
        employee = Employee.objects.filter(hikvision_id=hikvision_id).first()
        employee_name = employee.name if employee else "Неизвестный"
        
        # Проверяем, есть ли полная запись EntryExit
        full_entry_exit = EntryExit.objects.filter(
            hikvision_id=hikvision_id,
            entry_time__gte=start_datetime,
            entry_time__lt=end_datetime,
            exit_time__isnull=False
        ).exists()
        
        if not full_entry_exit:
            problems_found = True
            events = events_by_employee[hikvision_id]
            # Подсчитываем события по типу (нужно проверить device_name и IP)
            entry_count = 0
            exit_count = 0
            for ev in events:
                device_lower = (ev.device_name or "").lower()
                # Проверяем device_name
                if any(word in device_lower for word in ['вход', 'entry', 'входная', 'вход 1', 'вход1', '124']):
                    entry_count += 1
                elif any(word in device_lower for word in ['выход', 'exit', 'выходная', 'выход 1', 'выход1', '143']):
                    exit_count += 1
                # Проверяем IP в raw_data
                elif ev.raw_data:
                    camera_ip = None
                    if isinstance(ev.raw_data, dict):
                        outer_event = ev.raw_data.get("AccessControllerEvent", {})
                        if isinstance(outer_event, dict):
                            if "AccessControllerEvent" in outer_event:
                                inner_event = outer_event["AccessControllerEvent"]
                                if isinstance(inner_event, dict):
                                    camera_ip = inner_event.get("ipAddress") or inner_event.get("remoteHostAddr") or inner_event.get("ip")
                            if not camera_ip:
                                camera_ip = outer_event.get("ipAddress") or outer_event.get("remoteHostAddr") or outer_event.get("ip")
                        if not camera_ip:
                            camera_ip = ev.raw_data.get("ipAddress") or ev.raw_data.get("remoteHostAddr") or ev.raw_data.get("ip")
                    if camera_ip:
                        camera_ip_str = str(camera_ip)
                        if "143" in camera_ip_str or "192.168.1.143" in camera_ip_str:
                            exit_count += 1
                        elif "124" in camera_ip_str or "192.168.1.124" in camera_ip_str:
                            entry_count += 1
            
            print(f"  ⚠️ {employee_name} (ID: {hikvision_id})")
            print(f"     Событий всего: {len(events)}")
            print(f"     Похожих на вход: {entry_count}")
            print(f"     Похожих на выход: {exit_count}")
            
            # Проверяем, есть ли хотя бы частичная запись
            partial = EntryExit.objects.filter(
                hikvision_id=hikvision_id
            ).filter(
                Q(entry_time__gte=start_datetime, entry_time__lt=end_datetime) |
                Q(exit_time__gte=start_datetime, exit_time__lt=end_datetime)
            ).first()
            
            if partial:
                print(f"     Есть частичная запись EntryExit (ID: {partial.id})")
                if partial.entry_time:
                    print(f"     Вход: {timezone.localtime(partial.entry_time).strftime('%H:%M:%S')}")
                if partial.exit_time:
                    print(f"     Выход: {timezone.localtime(partial.exit_time).strftime('%H:%M:%S')}")
            else:
                print(f"     ❌ НЕТ ЗАПИСИ EntryExit вообще!")
            
            print()
    
    if not problems_found:
        print("  ✅ Проблем не найдено - все сотрудники с событиями имеют полные записи EntryExit")
    
    print()
    print("=" * 80)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80)

if __name__ == "__main__":
    check_december_22()

