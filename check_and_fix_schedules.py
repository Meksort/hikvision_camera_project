#!/usr/bin/env python
"""
Скрипт для проверки и исправления графиков работы сотрудников.
Проверяет всех сотрудников на наличие неполных или пустых графиков за декабрь 2025.
Создает недостающие записи для указанных сотрудников.
"""
import os
import sys

# Настройка кодировки для Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import django
from datetime import datetime, date, timedelta, time
from typing import Dict, List, Tuple, Optional

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from django.utils import timezone
from django.db.models import Q
from camera_events.models import EntryExit, Employee, WorkSchedule
from camera_events.utils import clean_id
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Данные для создания записей (из запроса пользователя)
EMPLOYEE_SCHEDULE_DATA = {
    'Касымшалов': {
        'dates': [5, 14, 23],
        'department_hint': 'СВК'
    },
    'Сыздыкова': {
        'dates': [23],
        'department_hint': ''
    },
    'Сарсекенов': {
        'dates': [2, 5, 20, 23],
        'department_hint': 'СВК'
    },
    'Мусаева': {
        'dates': [1, 14],
        'department_hint': 'СВК'
    },
    'Укенбаева': {
        'dates': [11],
        'department_hint': 'СВК'
    },
    'Кужахметов': {
        'dates': [1, 7, 13, 19, 22, 24, 31],
        'department_hint': ''
    },
    'Тортаев': {
        'dates': [26, 29],
        'department_hint': ''
    },
    'Кадирбаев': {
        'dates': [23],
        'department_hint': 'СВК'
    },
    'Тайтелиева': {
        'dates': [12],
        'department_hint': 'СВК'
    },
    'Сегизбай': {
        'dates': [21, 24, 30],
        'department_hint': 'СВК'
    },
}


def find_employee_by_name(name_part: str, department_hint: str = '') -> Optional[Employee]:
    """
    Находит сотрудника по части имени и подсказке о подразделении.
    
    Args:
        name_part: Часть имени сотрудника
        department_hint: Подсказка о подразделении (например, 'СВК')
        
    Returns:
        Employee объект или None
    """
    try:
        query = Employee.objects.filter(name__icontains=name_part)
        
        if department_hint:
            query = query.filter(
                Q(department__name__icontains=department_hint) |
                Q(department_old__icontains=department_hint)
            )
        
        employees = list(query)
        
        if len(employees) == 1:
            return employees[0]
        elif len(employees) > 1:
            logger.warning(f"Найдено несколько сотрудников с именем '{name_part}': {[e.name for e in employees]}")
            # Пытаемся найти наиболее подходящего
            for emp in employees:
                if department_hint and (
                    (emp.department and department_hint in emp.department.name) or
                    (emp.department_old and department_hint in emp.department_old)
                ):
                    logger.info(f"Выбран сотрудник: {emp.name} (ID: {emp.hikvision_id})")
                    return emp
            logger.info(f"Выбран первый найденный сотрудник: {employees[0].name} (ID: {employees[0].hikvision_id})")
            return employees[0]  # Возвращаем первого, если не нашли более подходящего
        
        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске сотрудника '{name_part}': {e}")
        return None


def has_shift_on_date(employee: Employee, check_date: date) -> bool:
    """
    Проверяет, была ли смена (24 часа работы) в указанный день.
    "24" в табеле = была смена = есть запись EntryExit с продолжительностью около 20-30 часов.
    
    Args:
        employee: Сотрудник
        check_date: Дата для проверки
        
    Returns:
        True, если была смена (24 часа), False если выходной
    """
    start_datetime = timezone.make_aware(datetime.combine(check_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(check_date + timedelta(days=1), datetime.min.time()))
    
    # Ищем записи с входом в этот день
    entries = EntryExit.objects.filter(
        hikvision_id=employee.hikvision_id,
        entry_time__gte=start_datetime,
        entry_time__lt=end_datetime,
        exit_time__isnull=False
    )
    
    # Проверяем, есть ли запись с продолжительностью около 20-30 часов (смена = 24 в табеле)
    for entry in entries:
        if entry.work_duration_seconds:
            duration_hours = entry.work_duration_seconds / 3600
            # Если продолжительность 20-30 часов - это смена (24 в табеле)
            if 20 <= duration_hours <= 30:
                return True  # Была смена
    
    # Если нет записей с продолжительностью 20-30 часов, проверяем выход на следующий день
    next_day = check_date + timedelta(days=1)
    next_day_start = timezone.make_aware(datetime.combine(next_day, datetime.min.time()))
    next_day_end = timezone.make_aware(datetime.combine(next_day + timedelta(days=1), datetime.min.time()))
    
    next_day_exits = EntryExit.objects.filter(
        hikvision_id=employee.hikvision_id,
        exit_time__gte=next_day_start,
        exit_time__lt=next_day_end
    )
    
    # Проверяем продолжительность от входа до выхода на следующий день
    for entry in entries:
        for exit_entry in next_day_exits:
            if exit_entry.entry_time and entry.entry_time:
                duration = exit_entry.exit_time - entry.entry_time
                duration_hours = duration.total_seconds() / 3600
                if 20 <= duration_hours <= 30:
                    return True  # Была смена
    
    return False  # Нет смены - выходной


def check_employee_schedule(employee: Employee, start_date: date, end_date: date) -> Dict:
    """
    Проверяет график работы сотрудника за указанный период.
    
    Returns:
        Словарь с результатами проверки:
        {
            'employee': Employee,
            'total_days': int,
            'days_with_entry': int,
            'days_with_exit': int,
            'days_complete': int,
            'days_incomplete': int,
            'days_empty': int,
            'incomplete_dates': List[date],
            'empty_dates': List[date]
        }
    """
    result = {
        'employee': employee,
        'total_days': 0,
        'days_with_entry': 0,
        'days_with_exit': 0,
        'days_complete': 0,
        'days_incomplete': 0,
        'days_empty': 0,
        'incomplete_dates': [],
        'empty_dates': []
    }
    
    current_date = start_date
    while current_date <= end_date:
        result['total_days'] += 1
        
        # Проверяем записи за этот день
        start_datetime = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(current_date + timedelta(days=1), datetime.min.time()))
        
        # Записи с входом в этот день
        entries = EntryExit.objects.filter(
            hikvision_id=employee.hikvision_id,
            entry_time__gte=start_datetime,
            entry_time__lt=end_datetime
        )
        
        # Записи с выходом в этот день (или на следующий день для круглосуточных графиков)
        exits = EntryExit.objects.filter(
            hikvision_id=employee.hikvision_id,
            exit_time__gte=start_datetime,
            exit_time__lt=end_datetime + timedelta(days=1)
        )
        
        has_entry = entries.exists()
        has_exit = exits.exists()
        
        # Проверяем полные записи (с входом и выходом)
        complete_entries = EntryExit.objects.filter(
            hikvision_id=employee.hikvision_id,
            entry_time__gte=start_datetime,
            entry_time__lt=end_datetime,
            exit_time__isnull=False
        )
        
        # Получаем график работы для проверки типа
        schedule = employee.work_schedules.first()
        is_round_the_clock = schedule and schedule.schedule_type == 'round_the_clock'
        
        # Проверяем, была ли смена (24 часа) в этот день
        # "24" в табеле = была смена = есть запись с продолжительностью 20-30 часов
        had_shift = has_shift_on_date(employee, current_date)
        
        # Проверяем качество записей
        has_valid_entry = False
        has_invalid_duration = False
        
        if complete_entries.exists():
            for ee in complete_entries:
                entry_local = timezone.localtime(ee.entry_time)
                exit_local = timezone.localtime(ee.exit_time)
                
                # Для круглосуточных графиков проверяем продолжительность
                if is_round_the_clock:
                    # Проверяем, что вход в окне 07:00-10:00
                    entry_time_local = entry_local.time()
                    if time(7, 0) <= entry_time_local <= time(10, 0):
                        duration_seconds = int((exit_local - entry_local).total_seconds())
                        duration_hours = duration_seconds / 3600
                        
                        # Для круглосуточных графиков продолжительность должна быть около 20-30 часов (смена)
                        if 20 <= duration_hours <= 30:
                            has_valid_entry = True
                        else:
                            has_invalid_duration = True
                            logger.debug(
                                f"{employee.name} {current_date}: неправильная продолжительность "
                                f"{duration_hours:.1f}ч (ожидается ~24ч)"
                            )
                else:
                    has_valid_entry = True
        elif has_entry and not has_exit:
            # Есть вход, но нет выхода
            pass  # Будет обработано ниже
        
        if has_entry:
            result['days_with_entry'] += 1
        if has_exit:
            result['days_with_exit'] += 1
        
        # Для круглосуточных графиков: если в табеле "24" (была смена), но нет записи - это проблема
        if is_round_the_clock and had_shift and not has_valid_entry:
            # В табеле была смена, но в базе нет правильной записи
            result['days_incomplete'] += 1
            result['incomplete_dates'].append(current_date)
        elif has_valid_entry:
            result['days_complete'] += 1
        elif has_invalid_duration:
            # Есть запись, но с неправильной продолжительностью
            result['days_incomplete'] += 1
            result['incomplete_dates'].append(current_date)
        elif has_entry and not has_exit:
            # Есть вход, но нет выхода
            result['days_incomplete'] += 1
            result['incomplete_dates'].append(current_date)
        elif not has_entry and not has_exit:
            # Нет ни входа, ни выхода
            # Если это не выходной по графику, отмечаем как пустой день
            if is_round_the_clock and not had_shift:
                # Выходной - это нормально
                pass
            else:
                result['days_empty'] += 1
                result['empty_dates'].append(current_date)
        
        current_date += timedelta(days=1)
    
    return result


def get_default_times_for_employee(employee: Employee) -> Tuple[time, time, int, int]:
    """
    Определяет время входа/выхода для сотрудника на основе его графика работы
    или существующих записей.
    
    Returns:
        Кортеж (entry_time, exit_time, entry_date_offset, exit_date_offset)
    """
    # Получаем график работы сотрудника
    schedule = employee.work_schedules.first()
    
    if schedule and schedule.schedule_type == 'round_the_clock':
        # Для круглосуточных графиков: вход утром (07:00-09:00), выход на следующий день
        # Пытаемся определить среднее время входа из существующих записей
        existing_entries = EntryExit.objects.filter(
            hikvision_id=employee.hikvision_id,
            entry_time__isnull=False
        ).order_by('-entry_time')[:10]
        
        if existing_entries:
            # Вычисляем среднее время входа
            entry_times = []
            for ee in existing_entries:
                entry_local = timezone.localtime(ee.entry_time)
                entry_times.append(entry_local.time())
            
            # Берем медианное время
            entry_times.sort()
            median_idx = len(entry_times) // 2
            entry_time = entry_times[median_idx]
            
            # Для выхода берем то же время на следующий день
            exit_time = entry_time
        else:
            # По умолчанию для круглосуточных графиков
            entry_time = time(8, 0)
            exit_time = time(8, 0)
        
        return entry_time, exit_time, 0, 1  # Вход в тот же день, выход на следующий
    else:
        # Для обычных графиков используем время из графика
        if schedule and schedule.start_time and schedule.end_time:
            entry_time = schedule.start_time
            exit_time = schedule.end_time
            # Если выход раньше входа, значит смена через полночь
            if exit_time < entry_time:
                return entry_time, exit_time, 0, 1
            else:
                return entry_time, exit_time, 0, 0
        else:
            # По умолчанию
            return time(8, 0), time(17, 0), 0, 0


def create_entry_exit_for_date(
    employee: Employee,
    target_date: date,
    entry_time: Optional[time] = None,
    exit_time: Optional[time] = None,
    entry_date_offset: Optional[int] = None,
    exit_date_offset: Optional[int] = None
) -> Tuple[EntryExit, bool]:
    """
    Создает или исправляет запись EntryExit для указанной даты.
    
    Args:
        employee: Сотрудник
        target_date: Целевая дата (дата графика)
        entry_time: Время входа (если None, определяется автоматически)
        exit_time: Время выхода (если None, определяется автоматически)
        entry_date_offset: Смещение даты входа относительно target_date (если None, определяется автоматически)
        exit_date_offset: Смещение даты выхода относительно target_date (если None, определяется автоматически)
        
    Returns:
        Кортеж (EntryExit объект, created: bool)
    """
    # Получаем график работы сотрудника
    schedule = employee.work_schedules.first()
    is_round_the_clock = schedule and schedule.schedule_type == 'round_the_clock'
    
    # Проверяем существующие записи за этот день и соседние дни
    start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(target_date + timedelta(days=2), datetime.min.time()))
    
    existing_entries = EntryExit.objects.filter(
        hikvision_id=employee.hikvision_id,
        entry_time__gte=start_datetime,
        entry_time__lt=end_datetime
    ).order_by('entry_time')
    
    # Ищем запись, которая относится к target_date
    existing = None
    for ee in existing_entries:
        entry_local = timezone.localtime(ee.entry_time)
        entry_date_local = entry_local.date()
        
        # Для круглосуточных графиков: запись относится к target_date, если вход в окне 07:00-10:00 в target_date
        if is_round_the_clock:
            if entry_date_local == target_date:
                entry_time_local = entry_local.time()
                if time(7, 0) <= entry_time_local <= time(10, 0):
                    existing = ee
                    break
        else:
            if entry_date_local == target_date:
                existing = ee
                break
    
    # Если нашли существующую запись
    if existing:
        entry_local = timezone.localtime(existing.entry_time)
        actual_entry_time = entry_local.time()
        actual_entry_date = entry_local.date()
        
        # Проверяем, нужно ли исправить запись
        needs_fix = False
        
        if existing.exit_time is None:
            # Нет выхода - нужно добавить
            needs_fix = True
        elif is_round_the_clock:
            # Для круглосуточных графиков проверяем продолжительность
            exit_local = timezone.localtime(existing.exit_time)
            duration_seconds = int((exit_local - entry_local).total_seconds())
            duration_hours = duration_seconds / 3600
            
            # Если продолжительность меньше 20 часов - это неправильно для круглосуточного графика
            if duration_hours < 20:
                needs_fix = True
                logger.info(
                    f"Найдена запись с неправильной продолжительностью для {employee.name} на {target_date}: "
                    f"{duration_hours:.1f}ч (ожидается ~24ч)"
                )
        
        if needs_fix:
            # Исправляем запись
            if is_round_the_clock:
                # Для круглосуточных: ищем реальный выход на следующий день в базе данных
                next_day = actual_entry_date + timedelta(days=1)
                next_day_start = timezone.make_aware(datetime.combine(next_day, datetime.min.time()))
                next_day_end = timezone.make_aware(datetime.combine(next_day + timedelta(days=1), datetime.min.time()))
                
                # Ищем записи с выходом на следующий день
                next_day_exits = EntryExit.objects.filter(
                    hikvision_id=employee.hikvision_id,
                    exit_time__gte=next_day_start,
                    exit_time__lt=next_day_end
                ).order_by('exit_time')
                
                # Ищем записи с входом на следующий день (может быть выход предыдущей смены)
                next_day_entries = EntryExit.objects.filter(
                    hikvision_id=employee.hikvision_id,
                    entry_time__gte=next_day_start,
                    entry_time__lt=next_day_end
                ).order_by('entry_time')
                
                found_real_exit = False
                exit_datetime = None
                
                # Приоритет 1: Выход на следующий день
                if next_day_exits.exists():
                    real_exit = next_day_exits.first()
                    exit_local = timezone.localtime(real_exit.exit_time)
                    exit_time_local = exit_local.time()
                    if time(6, 0) <= exit_time_local <= time(12, 0):
                        exit_datetime = real_exit.exit_time
                        found_real_exit = True
                
                # Приоритет 2: Вход на следующий день в окне 07:00-10:00
                if not found_real_exit and next_day_entries.exists():
                    real_entry = next_day_entries.first()
                    entry_local = timezone.localtime(real_entry.entry_time)
                    entry_time_local = entry_local.time()
                    if time(7, 0) <= entry_time_local <= time(10, 0):
                        exit_datetime = real_entry.entry_time
                        found_real_exit = True
                
                # Если не нашли реальный выход, используем примерное время
                if not found_real_exit:
                    exit_date = actual_entry_date + timedelta(days=1)
                    exit_time_to_use = actual_entry_time
                    if actual_entry_time < time(7, 0):
                        exit_time_to_use = time(8, 0)
                    elif actual_entry_time > time(10, 0):
                        exit_time_to_use = actual_entry_time
                    exit_datetime = timezone.make_aware(datetime.combine(exit_date, exit_time_to_use))
            else:
                # Для обычных графиков используем логику из графика
                if entry_time is None or exit_time is None or entry_date_offset is None or exit_date_offset is None:
                    default_entry, default_exit, default_entry_offset, default_exit_offset = get_default_times_for_employee(employee)
                    if entry_time is None:
                        entry_time = default_entry
                    if exit_time is None:
                        exit_time = default_exit
                    if entry_date_offset is None:
                        entry_date_offset = default_entry_offset
                    if exit_date_offset is None:
                        exit_date_offset = default_exit_offset
                
                exit_date = target_date + timedelta(days=exit_date_offset)
                exit_time_to_use = exit_time
            
            exit_datetime = timezone.make_aware(datetime.combine(exit_date, exit_time_to_use))
            
            existing.exit_time = exit_datetime
            existing.work_duration_seconds = int((exit_datetime - existing.entry_time).total_seconds())
            existing.save()
            
            logger.info(
                f"Исправлена запись для {employee.name} на {target_date}: "
                f"вход {entry_local.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"выход {exit_datetime.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"продолжительность {existing.work_duration_seconds // 3600}ч {(existing.work_duration_seconds % 3600) // 60}м"
            )
            return existing, False
        else:
            logger.info(f"Запись для {employee.name} на {target_date} уже существует и корректна")
            return existing, False
    
    # Если записи нет, создаем новую
    # Если время не указано, определяем автоматически
    if entry_time is None or exit_time is None or entry_date_offset is None or exit_date_offset is None:
        default_entry, default_exit, default_entry_offset, default_exit_offset = get_default_times_for_employee(employee)
        if entry_time is None:
            entry_time = default_entry
        if exit_time is None:
            exit_time = default_exit
        if entry_date_offset is None:
            entry_date_offset = default_entry_offset
        if exit_date_offset is None:
            exit_date_offset = default_exit_offset
    
    # Дата входа
    entry_date = target_date + timedelta(days=entry_date_offset)
    entry_datetime = timezone.make_aware(datetime.combine(entry_date, entry_time))
    
    # Дата выхода
    exit_date = target_date + timedelta(days=exit_date_offset)
    exit_datetime = timezone.make_aware(datetime.combine(exit_date, exit_time))
    
    # Создаем новую запись
    duration_seconds = int((exit_datetime - entry_datetime).total_seconds())
    
    entry_exit = EntryExit.objects.create(
        hikvision_id=employee.hikvision_id,
        entry_time=entry_datetime,
        exit_time=exit_datetime,
        work_duration_seconds=duration_seconds,
        device_name_entry='Автоматически создано',
        device_name_exit='Автоматически создано'
    )
    
    logger.info(
        f"Создана запись для {employee.name} на {target_date}: "
        f"вход {entry_datetime.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"выход {exit_datetime.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"продолжительность {duration_seconds // 3600}ч {(duration_seconds % 3600) // 60}м"
    )
    return entry_exit, True


def check_all_employees(start_date: date, end_date: date) -> List[Dict]:
    """
    Проверяет графики всех сотрудников за указанный период.
    
    Returns:
        Список словарей с результатами проверки для каждого сотрудника
    """
    logger.info(f"Начинаем проверку всех сотрудников за период {start_date} - {end_date}")
    
    employees = Employee.objects.all().select_related('department').prefetch_related('work_schedules')
    results = []
    
    for employee in employees:
        try:
            result = check_employee_schedule(employee, start_date, end_date)
            if result['days_incomplete'] > 0 or result['days_empty'] > 0:
                results.append(result)
                logger.info(
                    f"{employee.name}: полных дней: {result['days_complete']}, "
                    f"неполных: {result['days_incomplete']}, пустых: {result['days_empty']}"
                )
        except Exception as e:
            logger.error(f"Ошибка при проверке сотрудника {employee.name}: {e}")
    
    return results


def fix_all_invalid_durations(start_date: date, end_date: date) -> Dict:
    """
    Исправляет все записи с неправильной продолжительностью для круглосуточных графиков.
    
    Args:
        start_date: Начальная дата для проверки
        end_date: Конечная дата для проверки
        
    Returns:
        Словарь со статистикой исправлений
    """
    logger.info(f"Исправление всех записей с неправильной продолжительностью за период {start_date} - {end_date}")
    
    fixed_count = 0
    checked_count = 0
    employees_processed = set()
    
    # Получаем всех сотрудников с круглосуточными графиками
    employees_with_round_clock = Employee.objects.filter(
        work_schedules__schedule_type='round_the_clock'
    ).distinct().select_related('department').prefetch_related('work_schedules')
    
    print(f"\nПроверка {employees_with_round_clock.count()} сотрудников с круглосуточными графиками...")
    
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
    
    for employee in employees_with_round_clock:
        try:
            # Получаем все записи за период
            entries = EntryExit.objects.filter(
                hikvision_id=employee.hikvision_id,
                entry_time__gte=start_datetime,
                entry_time__lt=end_datetime,
                exit_time__isnull=False
            ).order_by('entry_time')
            
            for entry_exit in entries:
                checked_count += 1
                entry_local = timezone.localtime(entry_exit.entry_time)
                exit_local = timezone.localtime(entry_exit.exit_time)
                entry_date = entry_local.date()
                exit_date = exit_local.date()
                entry_time_local = entry_local.time()
                
                # Для круглосуточных графиков проверяем все записи
                # Приоритет: записи с входом в окне 07:00-10:00, но исправляем и другие
                
                duration_seconds = int((exit_local - entry_local).total_seconds())
                duration_hours = duration_seconds / 3600
                
                # Проверяем, нужно ли исправить запись:
                # 1. Продолжительность меньше 20 часов - неправильно для круглосуточного графика
                # 2. Выход в тот же день, что и вход, и продолжительность < 20 часов - неправильно
                needs_fix = False
                
                if duration_hours < 20:
                    needs_fix = True
                elif exit_date == entry_date:
                    # Выход в тот же день для круглосуточного графика - неправильно
                    # (кроме случаев, когда продолжительность > 20 часов - это может быть нормально)
                    if duration_hours < 20:
                        needs_fix = True
                
                if not needs_fix:
                    continue
                
                # Ищем реальный выход на следующий день в базе данных
                next_day = entry_date + timedelta(days=1)
                next_day_start = timezone.make_aware(datetime.combine(next_day, datetime.min.time()))
                next_day_end = timezone.make_aware(datetime.combine(next_day + timedelta(days=1), datetime.min.time()))
                
                # Ищем записи с выходом на следующий день
                # Вариант 1: Ищем другие записи EntryExit с exit_time на следующий день
                next_day_exits = EntryExit.objects.filter(
                    hikvision_id=employee.hikvision_id,
                    exit_time__gte=next_day_start,
                    exit_time__lt=next_day_end
                ).order_by('exit_time')
                
                # Вариант 2: Ищем записи с входом на следующий день (это может быть выход предыдущей смены)
                # Для круглосуточных графиков вход на следующий день часто означает выход предыдущей смены
                next_day_entries = EntryExit.objects.filter(
                    hikvision_id=employee.hikvision_id,
                    entry_time__gte=next_day_start,
                    entry_time__lt=next_day_end
                ).order_by('entry_time')
                
                # Вариант 3: Ищем события CameraEvent выхода на следующий день (если EntryExit еще не созданы)
                from camera_events.models import CameraEvent
                next_day_camera_exits = CameraEvent.objects.filter(
                    hikvision_id=employee.hikvision_id,
                    event_time__gte=next_day_start,
                    event_time__lt=next_day_end
                ).order_by('event_time')
                
                # Определяем, какие события являются выходами (по IP или device_name)
                camera_exit_events = []
                for cam_event in next_day_camera_exits:
                    is_exit_event = False
                    # Проверяем IP адрес
                    if cam_event.raw_data and isinstance(cam_event.raw_data, dict):
                        outer_event = cam_event.raw_data.get("AccessControllerEvent", {})
                        if isinstance(outer_event, dict):
                            camera_ip = (
                                outer_event.get("ipAddress") or
                                outer_event.get("remoteHostAddr") or
                                outer_event.get("ip") or
                                None
                            )
                            if camera_ip:
                                camera_ip_str = str(camera_ip)
                                # ВЫХОД: IP содержит 143
                                if "192.168.1.143" in camera_ip_str or camera_ip_str.endswith(".143") or camera_ip_str == "143":
                                    is_exit_event = True
                    
                    # Проверяем device_name
                    if not is_exit_event:
                        device_name_lower = (cam_event.device_name or "").lower()
                        is_exit_event = any(word in device_name_lower for word in ['выход', 'exit', 'выходная', 'выход 1', 'выход1', '143'])
                    
                    if is_exit_event:
                        camera_exit_events.append(cam_event)
                
                # Используем реальный выход, если найден
                found_real_exit = False
                new_exit_datetime = None
                
                # Приоритет 1: Выход на следующий день из других записей EntryExit
                if next_day_exits.exists():
                    # Берем самый ранний выход на следующий день
                    real_exit = next_day_exits.first()
                    exit_local = timezone.localtime(real_exit.exit_time)
                    # Проверяем, что это разумное время (не слишком рано и не слишком поздно)
                    exit_time_local = exit_local.time()
                    if time(6, 0) <= exit_time_local <= time(12, 0):
                        new_exit_datetime = real_exit.exit_time
                        found_real_exit = True
                        logger.info(
                            f"Найден реальный выход (EntryExit) на следующий день для {employee.name} на {entry_date}: "
                            f"{exit_local.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                
                # Приоритет 2: События CameraEvent выхода на следующий день
                if not found_real_exit and camera_exit_events:
                    # Берем самое раннее событие выхода на следующий день
                    real_exit_event = camera_exit_events[0]
                    exit_local = timezone.localtime(real_exit_event.event_time)
                    exit_time_local = exit_local.time()
                    if time(6, 0) <= exit_time_local <= time(12, 0):
                        new_exit_datetime = real_exit_event.event_time
                        found_real_exit = True
                        logger.info(
                            f"Найден реальный выход (CameraEvent) на следующий день для {employee.name} на {entry_date}: "
                            f"{exit_local.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                
                # Приоритет 3: Вход на следующий день (для круглосуточных графиков вход часто означает конец предыдущей смены)
                if not found_real_exit and next_day_entries.exists():
                    # Берем самый ранний вход на следующий день
                    real_entry = next_day_entries.first()
                    entry_local = timezone.localtime(real_entry.entry_time)
                    entry_time_local = entry_local.time()
                    # Для круглосуточных графиков вход на следующий день в окне 07:00-10:00 может быть выходом предыдущей смены
                    if time(7, 0) <= entry_time_local <= time(10, 0):
                        # Используем время входа как время выхода предыдущей смены
                        new_exit_datetime = real_entry.entry_time
                        found_real_exit = True
                        logger.info(
                            f"Использован вход на следующий день как выход для {employee.name} на {entry_date}: "
                            f"{entry_local.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                
                # Если не нашли реальный выход, используем примерное время
                if not found_real_exit:
                    new_exit_date = entry_date + timedelta(days=1)
                    exit_time_to_use = entry_time_local
                    
                    # Если время входа очень раннее (до 7:00), используем 8:00 для выхода
                    if entry_time_local < time(7, 0):
                        exit_time_to_use = time(8, 0)
                    # Если время входа после 10:00, используем то же время для выхода
                    elif entry_time_local > time(10, 0):
                        exit_time_to_use = entry_time_local
                    
                    new_exit_datetime = timezone.make_aware(datetime.combine(new_exit_date, exit_time_to_use))
                    logger.info(
                        f"Использовано примерное время выхода для {employee.name} на {entry_date}: "
                        f"{timezone.localtime(new_exit_datetime).strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                
                new_duration_seconds = int((new_exit_datetime - entry_exit.entry_time).total_seconds())
                
                entry_exit.exit_time = new_exit_datetime
                entry_exit.work_duration_seconds = new_duration_seconds
                entry_exit.save()
                
                fixed_count += 1
                employees_processed.add(employee.name)
                
                new_duration_hours = new_duration_seconds // 3600
                new_duration_mins = (new_duration_seconds % 3600) // 60
                
                logger.info(
                    f"Исправлена запись для {employee.name} на {entry_date}: "
                    f"было {duration_hours:.1f}ч, стало {new_duration_hours}ч {new_duration_mins}м"
                )
                
                if fixed_count % 10 == 0:
                    print(f"  Исправлено записей: {fixed_count}...")
        
        except Exception as e:
            logger.error(f"Ошибка при обработке сотрудника {employee.name}: {e}")
    
    print(f"\nИтоги исправления:")
    print(f"  Проверено записей: {checked_count}")
    print(f"  Исправлено записей: {fixed_count}")
    print(f"  Затронуто сотрудников: {len(employees_processed)}")
    
    if employees_processed:
        print(f"\n  Сотрудники с исправленными записями:")
        for name in sorted(employees_processed)[:20]:
            print(f"    - {name}")
        if len(employees_processed) > 20:
            print(f"    ... и еще {len(employees_processed) - 20} сотрудников")
    
    logger.info(
        f"Итоги исправления: проверено {checked_count}, исправлено {fixed_count}, "
        f"затронуто сотрудников {len(employees_processed)}"
    )
    
    return {
        'checked': checked_count,
        'fixed': fixed_count,
        'employees_affected': len(employees_processed)
    }


def create_missing_records(year: int = 2025, month: int = 12):
    """
    Создает недостающие записи для указанных сотрудников.
    """
    logger.info(f"Создание недостающих записей за {month}/{year}")
    
    created_count = 0
    updated_count = 0
    not_found_count = 0
    error_count = 0
    not_found_employees = []
    
    print(f"\nОбработка {len(EMPLOYEE_SCHEDULE_DATA)} сотрудников...")
    
    for name_part, data in EMPLOYEE_SCHEDULE_DATA.items():
        employee = find_employee_by_name(name_part, data['department_hint'])
        
        if not employee:
            logger.warning(f"Сотрудник '{name_part}' не найден")
            not_found_count += 1
            not_found_employees.append(name_part)
            continue
        
        print(f"  {employee.name} (ID: {employee.hikvision_id}) - даты: {data['dates']}")
        
        for day in data['dates']:
            try:
                target_date = date(year, month, day)
            except ValueError as e:
                logger.error(f"Неверная дата: {day}/{month}/{year}: {e}")
                error_count += 1
                continue
            
            try:
                # Время будет определено автоматически на основе графика сотрудника
                entry_exit, created = create_entry_exit_for_date(
                    employee=employee,
                    target_date=target_date
                )
                
                if created:
                    created_count += 1
                    entry_local = timezone.localtime(entry_exit.entry_time)
                    exit_local = timezone.localtime(entry_exit.exit_time)
                    duration_hours = entry_exit.work_duration_seconds // 3600
                    duration_mins = (entry_exit.work_duration_seconds % 3600) // 60
                    print(f"    ✓ Создана запись на {target_date}: {duration_hours}ч {duration_mins}м")
                else:
                    updated_count += 1
                    entry_local = timezone.localtime(entry_exit.entry_time)
                    exit_local = timezone.localtime(entry_exit.exit_time)
                    duration_hours = entry_exit.work_duration_seconds // 3600 if entry_exit.work_duration_seconds else 0
                    duration_mins = ((entry_exit.work_duration_seconds % 3600) // 60) if entry_exit.work_duration_seconds else 0
                    print(f"    → Исправлена запись на {target_date}: {duration_hours}ч {duration_mins}м")
                    
            except Exception as e:
                logger.error(f"Ошибка при создании записи для {employee.name} на {target_date}: {e}")
                error_count += 1
    
    print(f"\nИтоги создания записей:")
    print(f"  Создано новых: {created_count}")
    print(f"  Обновлено: {updated_count}")
    print(f"  Ошибок: {error_count}")
    print(f"  Не найдено сотрудников: {not_found_count}")
    
    if not_found_employees:
        print(f"\n  Не найденные сотрудники: {', '.join(not_found_employees)}")
    
    logger.info(
        f"Итоги создания записей: создано новых: {created_count}, "
        f"обновлено: {updated_count}, ошибок: {error_count}, не найдено сотрудников: {not_found_count}"
    )
    
    return {
        'created': created_count,
        'updated': updated_count,
        'errors': error_count,
        'not_found': not_found_count,
        'not_found_employees': not_found_employees
    }


def main():
    """
    Главная функция скрипта.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Проверка и исправление графиков работы сотрудников')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Только проверить графики, не создавать записи'
    )
    parser.add_argument(
        '--create-only',
        action='store_true',
        help='Только создать недостающие записи, не проверять всех'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2025-12-01',
        help='Начальная дата для проверки (формат: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default='2025-12-31',
        help='Конечная дата для проверки (формат: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Экспортировать результаты проверки в файл (путь к файлу)'
    )
    parser.add_argument(
        '--fix-all-durations',
        action='store_true',
        help='Исправить все записи с неправильной продолжительностью для всех сотрудников'
    )
    
    args = parser.parse_args()
    
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    except ValueError:
        logger.error("Неверный формат даты. Используйте YYYY-MM-DD")
        sys.exit(1)
    
    print("=" * 80)
    print("ПРОВЕРКА И ИСПРАВЛЕНИЕ ГРАФИКОВ РАБОТЫ СОТРУДНИКОВ")
    print("=" * 80)
    print(f"Период: {start_date} - {end_date}")
    print()
    
    # Проверка всех сотрудников
    if not args.create_only:
        print("1. ПРОВЕРКА ВСЕХ СОТРУДНИКОВ")
        print("-" * 80)
        results = check_all_employees(start_date, end_date)
        
        if results:
            print(f"\nНайдено сотрудников с проблемами: {len(results)}")
            print("\nДетальная информация:")
            for result in results[:20]:  # Показываем первые 20
                emp = result['employee']
                print(f"\n  {emp.name} ({emp.hikvision_id}):")
                print(f"    Полных дней: {result['days_complete']}")
                print(f"    Неполных дней: {result['days_incomplete']}")
                print(f"    Пустых дней: {result['days_empty']}")
                if result['incomplete_dates']:
                    print(f"    Неполные даты: {', '.join(str(d) for d in result['incomplete_dates'][:5])}")
                if result['empty_dates']:
                    print(f"    Пустые даты: {', '.join(str(d) for d in result['empty_dates'][:5])}")
            
            if len(results) > 20:
                print(f"\n  ... и еще {len(results) - 20} сотрудников")
            
            # Экспорт результатов в файл, если указан
            if args.export:
                try:
                    with open(args.export, 'w', encoding='utf-8') as f:
                        f.write("ОТЧЕТ О ПРОВЕРКЕ ГРАФИКОВ РАБОТЫ СОТРУДНИКОВ\n")
                        f.write("=" * 80 + "\n")
                        f.write(f"Период: {start_date} - {end_date}\n")
                        f.write(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Найдено сотрудников с проблемами: {len(results)}\n\n")
                        
                        for result in results:
                            emp = result['employee']
                            dept = emp.department.name if emp.department else (emp.department_old or 'Не указано')
                            f.write(f"\n{emp.name} (ID: {emp.hikvision_id})\n")
                            f.write(f"  Подразделение: {dept}\n")
                            f.write(f"  Полных дней: {result['days_complete']}\n")
                            f.write(f"  Неполных дней: {result['days_incomplete']}\n")
                            f.write(f"  Пустых дней: {result['days_empty']}\n")
                            if result['incomplete_dates']:
                                f.write(f"  Неполные даты: {', '.join(str(d) for d in result['incomplete_dates'])}\n")
                            if result['empty_dates']:
                                f.write(f"  Пустые даты: {', '.join(str(d) for d in result['empty_dates'])}\n")
                        
                    print(f"\n✓ Результаты экспортированы в файл: {args.export}")
                except Exception as e:
                    logger.error(f"Ошибка при экспорте результатов: {e}")
        else:
            print("\n✓ Все сотрудники имеют полные графики")
    
    # Исправление всех записей с неправильной продолжительностью
    # Запускается автоматически, если не указан --check-only
    if not args.check_only or args.fix_all_durations:
        print("\n" + "=" * 80)
        print("2. ИСПРАВЛЕНИЕ ВСЕХ ЗАПИСЕЙ С НЕПРАВИЛЬНОЙ ПРОДОЛЖИТЕЛЬНОСТЬЮ")
        print("-" * 80)
        fix_stats = fix_all_invalid_durations(start_date, end_date)
        print(f"\nПроверено записей: {fix_stats['checked']}")
        print(f"Исправлено записей: {fix_stats['fixed']}")
        print(f"Затронуто сотрудников: {fix_stats['employees_affected']}")
    
    # Создание недостающих записей
    if not args.check_only:
        print("\n" + "=" * 80)
        print("3. СОЗДАНИЕ НЕДОСТАЮЩИХ ЗАПИСЕЙ")
        print("-" * 80)
        stats = create_missing_records(year=start_date.year, month=start_date.month)
        print(f"\nСоздано новых записей: {stats['created']}")
        print(f"Обновлено записей: {stats['updated']}")
        print(f"Не найдено сотрудников: {stats['not_found']}")
    
    print("\n" + "=" * 80)
    print("ГОТОВО")
    print("=" * 80)


if __name__ == '__main__':
    try:
        # Проверяем подключение к базе данных
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Подключение к базе данных успешно")
        print()
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        print("\n⚠️ ВНИМАНИЕ: Не удалось подключиться к базе данных!")
        print("Убедитесь, что:")
        print("  1. База данных доступна")
        print("  2. Настройки подключения в settings.py корректны")
        print("  3. База данных находится на доступном сервере")
        sys.exit(1)
    
    try:
        main()
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        sys.exit(1)

