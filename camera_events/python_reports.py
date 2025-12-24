"""
Python версия генерации отчетов о посещаемости.
Использует Django ORM вместо SQL запросов.
"""
from django.utils import timezone
from datetime import datetime, timedelta, time, date
from typing import Optional, List, Dict, Tuple
import logging
from collections import defaultdict

from .models import EntryExit, Employee, WorkSchedule, Department
from .utils import clean_id, get_excluded_hikvision_ids
from .schedule_matcher import ScheduleMatcher

logger = logging.getLogger(__name__)


def is_round_the_clock_morning_entry(dt: datetime) -> bool:
    """
    Проверяет, попадает ли время входа в утреннее окно 07:00–11:00
    для круглосуточного графика.
    """
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    dt_local = timezone.localtime(dt)
    t = dt_local.time()
    return time(7, 0) <= t <= time(11, 0)


def is_work_day_for_schedule(schedule: WorkSchedule, check_date: date) -> bool:
    """
    Проверяет, является ли дата рабочим днем по графику.
    """
    if schedule.schedule_type == 'round_the_clock':
        # Для круглосуточных графиков проверяем days_of_week
        if schedule.days_of_week:
            weekday = check_date.weekday()  # 0=понедельник, 6=воскресенье
            return weekday in schedule.days_of_week
        else:
            # Если days_of_week не указано, все дни рабочие
            return True
    elif schedule.schedule_type == 'regular':
        # Для обычных графиков проверяем days_of_week
        if schedule.days_of_week:
            weekday = check_date.weekday()
            return weekday in schedule.days_of_week
        else:
            return True
    elif schedule.schedule_type == 'floating':
        return True
    
    return False


def generate_comprehensive_attendance_report_python(
    hikvision_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    device_name: Optional[str] = None,
    excluded_hikvision_ids: Optional[List[str]] = None
) -> Tuple[List[Dict], date, date]:
    """
    Генерирует отчет о посещаемости используя Python и Django ORM.
    
    Args:
        hikvision_id: ID сотрудника от Hikvision (опционально)
        start_date: Начальная дата (формат: YYYY-MM-DD)
        end_date: Конечная дата (формат: YYYY-MM-DD)
        device_name: Фильтр по названию устройства
        excluded_hikvision_ids: Список ID для исключения
        
    Returns:
        Кортеж (список словарей с данными, start_date_obj, end_date_obj)
    """
    # Парсим даты
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            if ' ' in start_date or 'T' in start_date:
                start_date_clean = start_date.replace('T', ' ')
                start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M:%S")
            else:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime)
            
            start_date_obj = timezone.localtime(start_datetime).date()
        except ValueError:
            pass
    
    if end_date:
        try:
            if ' ' in end_date or 'T' in end_date:
                end_date_clean = end_date.replace('T', ' ')
                end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M:%S")
            else:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                # Добавляем время конца дня
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            if timezone.is_naive(end_datetime):
                end_datetime = timezone.make_aware(end_datetime)
            
            end_date_obj = timezone.localtime(end_datetime).date()
        except ValueError:
            pass
    
    if not start_date_obj:
        start_date_obj = timezone.now().date() - timedelta(days=30)
    
    if not end_date_obj:
        end_date_obj = timezone.now().date()
    
    # Получаем исключаемые ID
    if excluded_hikvision_ids is None:
        excluded_hikvision_ids = get_excluded_hikvision_ids()
    
    # Получаем записи EntryExit (без select_related, так как нет прямого ForeignKey на Employee)
    queryset = EntryExit.objects.filter(
        entry_time__isnull=False,
        exit_time__isnull=False
    )
    
    # Фильтр по hikvision_id
    if hikvision_id:
        clean_id_str = clean_id(hikvision_id)
        queryset = queryset.filter(
            hikvision_id__in=[clean_id_str, hikvision_id]
        )
    
    # Фильтр по датам
    start_datetime_aware = timezone.make_aware(datetime.combine(start_date_obj, datetime.min.time()))
    end_datetime_aware = timezone.make_aware(datetime.combine(end_date_obj, datetime.max.time()))
    queryset = queryset.filter(entry_time__gte=start_datetime_aware, entry_time__lte=end_datetime_aware)
    
    # Фильтр по device_name
    if device_name:
        queryset = queryset.filter(
            device_name_entry__icontains=device_name
        ) | queryset.filter(
            device_name_exit__icontains=device_name
        )
    
    # Исключаем определенных сотрудников
    if excluded_hikvision_ids:
        queryset = queryset.exclude(hikvision_id__in=excluded_hikvision_ids)
    
    # Получаем все записи
    entry_exits = list(queryset.order_by('entry_time'))
    
    # Предзагружаем всех сотрудников и их графики для оптимизации
    hikvision_ids = set(ee.hikvision_id for ee in entry_exits if ee.hikvision_id)
    employees_dict = {}
    schedules_dict = {}
    
    if hikvision_ids:
        employees = Employee.objects.filter(
            hikvision_id__in=hikvision_ids
        ).select_related('department').prefetch_related('work_schedules')
        
        for emp in employees:
            clean_emp_id = clean_id(emp.hikvision_id)
            employees_dict[clean_emp_id] = emp
            employees_dict[emp.hikvision_id] = emp  # Также сохраняем с оригинальным ID
            schedule = emp.work_schedules.first()
            if schedule:
                schedules_dict[clean_emp_id] = schedule
                schedules_dict[emp.hikvision_id] = schedule
    
    # Группируем по сотрудникам и периодам
    # Структура: (hikvision_id, period_date) -> {entries: [], exits: [], ...}
    results_by_employee_period = defaultdict(lambda: {
        'employee_name': None,
        'department_name': None,
        'schedule_type': None,
        'schedule_start_time': None,
        'schedule_end_time': None,
        'allowed_late_minutes': None,
        'allowed_early_leave_minutes': None,
        'days_of_week': None,
        'entries': [],  # Входы, которые относятся к этому периоду (period_date = period_date)
        'exits': [],    # Выходы, которые относятся к этому периоду (exit_period_date = period_date)
        'period_date': None
    })
    
    # Обрабатываем каждую запись
    for ee in entry_exits:
        try:
            if not ee.hikvision_id:
                continue
            
            # Получаем сотрудника из кэша
            clean_emp_id = clean_id(ee.hikvision_id)
            employee = employees_dict.get(clean_emp_id) or employees_dict.get(ee.hikvision_id)
            if not employee:
                continue
            
            # Получаем график работы из кэша
            schedule = schedules_dict.get(clean_emp_id) or schedules_dict.get(ee.hikvision_id)
            if not schedule:
                continue
            
            # Получаем название подразделения
            department_name = ''
            if employee.department:
                try:
                    if employee.department.parent:
                        department_name = f"{employee.department.parent.name} > {employee.department.name}"
                    else:
                        department_name = employee.department.name
                except:
                    department_name = employee.department.name if employee.department.name else ''
            elif employee.department_old:
                department_name = employee.department_old.replace('/', ' > ')
            
            # Конвертируем времена в локальный часовой пояс
            if timezone.is_naive(ee.entry_time):
                entry_time = timezone.make_aware(ee.entry_time)
            else:
                entry_time = ee.entry_time
            entry_local = timezone.localtime(entry_time)
            
            if timezone.is_naive(ee.exit_time):
                exit_time = timezone.make_aware(ee.exit_time)
            else:
                exit_time = ee.exit_time
            exit_local = timezone.localtime(exit_time)
            
            # Определяем период для входа/выхода
            if schedule.schedule_type == 'round_the_clock':
                # Новая логика для круглосуточных графиков:
                # - Берем только утренние входы в окне 07:00–11:00
                # - Период (дата графика) = календарная дата этого входа
                # - Выход относится к тому же периоду, даже если он на следующий день
                if not is_round_the_clock_morning_entry(entry_time):
                    # Вход вне окна 07:00–11:00 в графике не учитываем
                    continue
                period_date = entry_local.date()
                
                key = (ee.hikvision_id, period_date)
                
                if results_by_employee_period[key]['employee_name'] is None:
                    results_by_employee_period[key]['employee_name'] = employee.name
                    results_by_employee_period[key]['department_name'] = department_name
                    results_by_employee_period[key]['schedule_type'] = schedule.schedule_type
                    results_by_employee_period[key]['schedule_start_time'] = schedule.start_time
                    results_by_employee_period[key]['schedule_end_time'] = schedule.end_time
                    results_by_employee_period[key]['allowed_late_minutes'] = schedule.allowed_late_minutes
                    results_by_employee_period[key]['allowed_early_leave_minutes'] = schedule.allowed_early_leave_minutes
                    results_by_employee_period[key]['days_of_week'] = schedule.days_of_week
                    results_by_employee_period[key]['period_date'] = period_date
                
                # Для круглосуточного графика вход и выход всегда относим к одному и тому же периоду
                results_by_employee_period[key]['entries'].append(entry_local)
                results_by_employee_period[key]['exits'].append(exit_local)
            else:
                period_date = entry_local.date()
                exit_period_date = exit_local.date()
                
                # Ключ для группировки входов (по периоду входа)
                entry_key = (ee.hikvision_id, period_date)
                
                # Сохраняем информацию о сотруднике и графике
                if results_by_employee_period[entry_key]['employee_name'] is None:
                    results_by_employee_period[entry_key]['employee_name'] = employee.name
                    results_by_employee_period[entry_key]['department_name'] = department_name
                    results_by_employee_period[entry_key]['schedule_type'] = schedule.schedule_type
                    results_by_employee_period[entry_key]['schedule_start_time'] = schedule.start_time
                    results_by_employee_period[entry_key]['schedule_end_time'] = schedule.end_time
                    results_by_employee_period[entry_key]['allowed_late_minutes'] = schedule.allowed_late_minutes
                    results_by_employee_period[entry_key]['allowed_early_leave_minutes'] = schedule.allowed_early_leave_minutes
                    results_by_employee_period[entry_key]['days_of_week'] = schedule.days_of_week
                    results_by_employee_period[entry_key]['period_date'] = period_date
                
                # Добавляем вход к периоду входа
                if results_by_employee_period[entry_key]['employee_name'] is None:
                    results_by_employee_period[entry_key]['employee_name'] = employee.name
                    results_by_employee_period[entry_key]['department_name'] = department_name
                    results_by_employee_period[entry_key]['schedule_type'] = schedule.schedule_type
                    results_by_employee_period[entry_key]['schedule_start_time'] = schedule.start_time
                    results_by_employee_period[entry_key]['schedule_end_time'] = schedule.end_time
                    results_by_employee_period[entry_key]['allowed_late_minutes'] = schedule.allowed_late_minutes
                    results_by_employee_period[entry_key]['allowed_early_leave_minutes'] = schedule.allowed_early_leave_minutes
                    results_by_employee_period[entry_key]['days_of_week'] = schedule.days_of_week
                    results_by_employee_period[entry_key]['period_date'] = period_date
                results_by_employee_period[entry_key]['entries'].append(entry_local)
                
                # Добавляем выход к периоду выхода (exit_period_date)
                exit_key = (ee.hikvision_id, exit_period_date)
                if results_by_employee_period[exit_key]['employee_name'] is None:
                    results_by_employee_period[exit_key]['employee_name'] = employee.name
                    results_by_employee_period[exit_key]['department_name'] = department_name
                    results_by_employee_period[exit_key]['schedule_type'] = schedule.schedule_type
                    results_by_employee_period[exit_key]['schedule_start_time'] = schedule.start_time
                    results_by_employee_period[exit_key]['schedule_end_time'] = schedule.end_time
                    results_by_employee_period[exit_key]['allowed_late_minutes'] = schedule.allowed_late_minutes
                    results_by_employee_period[exit_key]['allowed_early_leave_minutes'] = schedule.allowed_early_leave_minutes
                    results_by_employee_period[exit_key]['days_of_week'] = schedule.days_of_week
                    results_by_employee_period[exit_key]['period_date'] = exit_period_date
                results_by_employee_period[exit_key]['exits'].append(exit_local)
            
        except Exception as e:
            logger.warning(f"Ошибка при обработке записи EntryExit (id={ee.id}): {e}")
            continue
    
    # Формируем результаты
    results = []
    
    for (hikvision_id, period_date), data in results_by_employee_period.items():
        try:
            # Проверяем, является ли день рабочим
            employee = Employee.objects.filter(hikvision_id=hikvision_id).first()
            if employee:
                schedule = employee.work_schedules.first()
                if schedule and not is_work_day_for_schedule(schedule, period_date):
                    continue
            
            # Находим первый вход и последний выход
            if not data['entries'] or not data['exits']:
                continue
            
            # Находим первый вход и последний выход для этого периода
            if data['schedule_type'] == 'round_the_clock' and data['entries']:
                # Для круглосуточных графиков:
                # если есть входы в окне 07:00–11:00, берем самый ранний из них,
                # иначе берем самый ранний вход за день
                morning_entries = [
                    e for e in data['entries']
                    if time(7, 0) <= e.time() <= time(11, 0)
                ]
                if morning_entries:
                    first_entry = min(morning_entries)
                else:
                    first_entry = min(data['entries'])
            else:
                first_entry = min(data['entries']) if data['entries'] else None
            last_exit = max(data['exits']) if data['exits'] else None
            
            if first_entry is None or last_exit is None:
                continue
            
            # Вычисляем продолжительность
            if last_exit > first_entry:
                duration_seconds = int((last_exit - first_entry).total_seconds())
                # Ограничиваем максимум 72 часами для круглосуточных графиков
                if data['schedule_type'] == 'round_the_clock':
                    duration_seconds = min(duration_seconds, 72 * 3600)
                else:
                    duration_seconds = min(duration_seconds, 16 * 3600)
            else:
                duration_seconds = 0
            
            # Вычисляем опоздание (только для обычных графиков)
            late_minutes = 0
            if data['schedule_type'] != 'round_the_clock' and data['schedule_start_time']:
                schedule_start = datetime.combine(period_date, data['schedule_start_time'])
                schedule_start = timezone.make_aware(schedule_start)
                schedule_start_local = timezone.localtime(schedule_start)
                
                if first_entry > schedule_start_local:
                    late_seconds = (first_entry - schedule_start_local).total_seconds()
                    late_minutes = int(late_seconds / 60) - (data['allowed_late_minutes'] or 0)
                    late_minutes = max(0, late_minutes)
            
            # Вычисляем ранний уход (только для обычных графиков)
            early_leave_minutes = 0
            if data['schedule_type'] != 'round_the_clock' and data['schedule_end_time']:
                schedule_end = datetime.combine(period_date, data['schedule_end_time'])
                if data['schedule_end_time'] < data['schedule_start_time']:
                    schedule_end += timedelta(days=1)
                schedule_end = timezone.make_aware(schedule_end)
                schedule_end_local = timezone.localtime(schedule_end)
                
                if last_exit < schedule_end_local:
                    early_seconds = (schedule_end_local - last_exit).total_seconds()
                    early_leave_minutes = int(early_seconds / 60) - (data['allowed_early_leave_minutes'] or 0)
                    early_leave_minutes = max(0, early_leave_minutes)
            
            # День недели (PostgreSQL DOW формат: 0=воскресенье, 1=понедельник, ..., 6=суббота)
            # Python weekday(): 0=понедельник, 6=воскресенье
            # Конвертация: postgresql_dow = (python_weekday + 1) % 7
            python_weekday = period_date.weekday()
            day_of_week = (python_weekday + 1) % 7
            
            results.append({
                'hikvision_id': hikvision_id,
                'employee_name': data['employee_name'],
                'department_name': data['department_name'],
                'report_date': period_date,
                'day_of_week': day_of_week,
                'schedule_type': data['schedule_type'],
                'schedule_start_time': data['schedule_start_time'],
                'schedule_end_time': data['schedule_end_time'],
                'allowed_late_minutes': data['allowed_late_minutes'],
                'allowed_early_leave_minutes': data['allowed_early_leave_minutes'],
                'first_entry': first_entry,
                'last_exit': last_exit,
                'total_duration_seconds': duration_seconds,
                'late_minutes': late_minutes,
                'early_leave_minutes': early_leave_minutes,
            })
            
        except Exception as e:
            logger.warning(f"Ошибка при формировании результата для {hikvision_id}, {period_date}: {e}")
            continue
    
    # Сортируем результаты
    results.sort(key=lambda x: (x['employee_name'], x['report_date']))
    
    return results, start_date_obj, end_date_obj

