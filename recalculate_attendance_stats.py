"""
Скрипт для пересчета статистики посещаемости с 1 декабря.
Обновляет счетчики опозданий и ранних уходов для всех сотрудников.
"""
import os
import sys

# Настройка кодировки для Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import django
from datetime import datetime, timedelta, time

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from django.utils import timezone
from django.db import transaction, connection
from django.db.utils import OperationalError, DatabaseError
from camera_events.models import EntryExit, Employee, EmployeeAttendanceStats
from camera_events.views import clean_id
import logging

logger = logging.getLogger(__name__)

def should_exclude_employee(employee):
    """
    Проверяет, нужно ли исключить сотрудника из статистики.
    Исключаются: массажисты, водители, парильщики, маникюр, педикюр, косметологи, тренера, инструкторы.
    """
    if not employee:
        return False
    
    # Ключевые слова для исключения (в названиях подразделений или именах)
    exclude_keywords = [
        'массаж', 'массажист',
        'водитель', 'водители',
        'париль', 'парильщик',
        'маникюр',
        'педикюр',
        'косметолог', 'косметология',
        'тренер', 'тренера', 'тренеры',
        'инструктор', 'инструкторы', 'инструктора'
    ]
    
    # Проверяем подразделение сотрудника
    if employee.department:
        try:
            dept_path = employee.department.get_full_path().lower()
            for keyword in exclude_keywords:
                if keyword in dept_path:
                    return True
        except (RecursionError, AttributeError, Exception) as e:
            logger.warning(f"Ошибка при получении пути подразделения для сотрудника (id={employee.id}): {e}")
    
    # Проверяем старое поле подразделения
    if employee.department_old:
        dept_old_lower = employee.department_old.lower()
        for keyword in exclude_keywords:
            if keyword in dept_old_lower:
                return True
    
    # Проверяем имя сотрудника (на случай, если категория указана в имени)
    employee_name_lower = employee.name.lower()
    for keyword in exclude_keywords:
        if keyword in employee_name_lower:
            return True
    
    return False

def recalculate_attendance_stats(start_date=None):
    """
    Пересчитывает статистику посещаемости для всех сотрудников с указанной даты.
    
    Args:
        start_date: Дата начала пересчета (по умолчанию 1 декабря текущего года)
    """
    start_time = timezone.now()
    
    try:
        if start_date is None:
            today = timezone.now().date()
            start_date = datetime(today.year, 12, 1).date()
        
        # Конвертируем в datetime с временем начала дня
        start_datetime = datetime.combine(start_date, datetime.min.time())
        start_datetime = timezone.make_aware(start_datetime)
        
        # Получаем количество записей для прогресса
        try:
            total_records = EntryExit.objects.filter(
                entry_time__gte=start_datetime
            ).count()
            logger.info(f"Найдено записей EntryExit для обработки: {total_records}")
        except Exception as e:
            logger.error(f"Ошибка при подсчете записей EntryExit: {e}", exc_info=True)
            return
        
        # Получаем QuerySet для итерации (не загружаем все в память сразу)
        try:
            entry_exits_qs = EntryExit.objects.filter(
                entry_time__gte=start_datetime
            ).order_by('entry_time').only('id', 'hikvision_id', 'entry_time', 'exit_time', 'late_counted', 'early_leave_counted')
        except Exception as e:
            logger.error(f"Ошибка при получении QuerySet EntryExit: {e}", exc_info=True)
            return
        
        # Сбрасываем все флаги учета, чтобы пересчитать заново
        try:
            EntryExit.objects.filter(
                entry_time__gte=start_datetime
            ).update(late_counted=False, early_leave_counted=False)
        except Exception as e:
            logger.error(f"Ошибка при сбросе флагов учета: {e}", exc_info=True)
            return
        
        # Обнуляем статистику для всех сотрудников
        try:
            EmployeeAttendanceStats.objects.all().update(late_count=0, early_leave_count=0)
        except Exception as e:
            logger.error(f"Ошибка при обнулении статистики: {e}", exc_info=True)
            return
    
        # Группируем записи по сотрудникам
        entries_by_employee = {}
        processed_records = 0
        batch_size = 1000
        
        try:
            # Используем batch processing вместо iterator, чтобы избежать проблем с закрытием курсора
            offset = 0
            while True:
                batch = list(entry_exits_qs[offset:offset + batch_size])
                if not batch:
                    break
                
                for entry_exit in batch:
                    try:
                        if not entry_exit.hikvision_id:
                            processed_records += 1
                            continue
                        
                        clean_emp_id = clean_id(entry_exit.hikvision_id)
                        if clean_emp_id not in entries_by_employee:
                            entries_by_employee[clean_emp_id] = []
                        entries_by_employee[clean_emp_id].append(entry_exit)
                        processed_records += 1
                        
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке записи EntryExit (id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                        processed_records += 1
                        continue
                
                # Выводим прогресс
                if processed_records % batch_size == 0 or processed_records == total_records:
                    logger.info(f"Прогресс загрузки: {processed_records}/{total_records} ({processed_records*100//total_records if total_records > 0 else 0}%)")
                
                offset += batch_size
                    
            logger.info(f"Загрузка завершена: обработано {processed_records} записей, сгруппировано по {len(entries_by_employee)} сотрудникам")
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Ошибка БД при группировке записей по сотрудникам: {e}", exc_info=True)
            return
        except Exception as e:
            logger.error(f"Ошибка при группировке записей по сотрудникам: {e}", exc_info=True)
            return
        
        # Обрабатываем каждого сотрудника
        total_late_count = 0
        total_early_count = 0
        processed_employees = 0
        employees_without_schedule = 0
        employees_not_found = 0
        
        total_employees = len(entries_by_employee)
        
        employee_index = 0
        for employee_id, entries in entries_by_employee.items():
            employee_index += 1
            # Выводим прогресс каждые 200 сотрудников или для последнего
            if employee_index % 200 == 0 or employee_index == total_employees:
                logger.info(f"Прогресс: {employee_index}/{total_employees} ({employee_index*100//total_employees}%)")
            try:
                try:
                    employee = Employee.objects.filter(hikvision_id=employee_id).select_related('department').first()
                except (OperationalError, DatabaseError) as e:
                    logger.warning(f"Ошибка БД при поиске сотрудника (hikvision_id={employee_id}): {e}")
                    employees_not_found += 1
                    continue
                except Exception as e:
                    logger.warning(f"Ошибка при поиске сотрудника (hikvision_id={employee_id}): {e}")
                    employees_not_found += 1
                    continue
                
                if not employee:
                    employees_not_found += 1
                    continue
                
                # Проверяем, нужно ли исключить сотрудника из статистики
                try:
                    if should_exclude_employee(employee):
                        continue
                except Exception as e:
                    logger.warning(f"Ошибка при проверке исключения сотрудника (id={employee.id}): {e}")
                    continue
                
                try:
                    schedule = employee.work_schedules.first()
                except (OperationalError, DatabaseError) as e:
                    logger.warning(f"Ошибка БД при получении графика работы для сотрудника (id={employee.id}): {e}")
                    employees_without_schedule += 1
                    continue
                except Exception as e:
                    logger.warning(f"Ошибка при получении графика работы для сотрудника (id={employee.id}): {e}")
                    employees_without_schedule += 1
                    continue
                
                if not schedule:
                    employees_without_schedule += 1
                    continue
                
                processed_employees += 1
                
                try:
                    stats, created = EmployeeAttendanceStats.objects.get_or_create(employee=employee)
                except (OperationalError, DatabaseError) as e:
                    logger.warning(f"Ошибка БД при создании/получении статистики для сотрудника (id={employee.id}): {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Ошибка при создании/получении статистики для сотрудника (id={employee.id}): {e}")
                    continue
        
                # Сортируем записи по времени входа
                try:
                    entries_sorted = sorted(entries, key=lambda x: x.entry_time if x.entry_time else datetime.min)
                except Exception as e:
                    logger.warning(f"Ошибка при сортировке записей для сотрудника (id={employee.id}): {e}")
                    continue
                
                # Группируем записи по датам для определения первого входа за день
                entries_by_date = {}
                try:
                    for entry_exit in entries_sorted:
                        try:
                            if not entry_exit.entry_time:
                                continue
                            
                            # Конвертируем время входа
                            if timezone.is_naive(entry_exit.entry_time):
                                entry_time = timezone.make_aware(entry_exit.entry_time)
                            else:
                                entry_time = entry_exit.entry_time
                            entry_time_local = timezone.localtime(entry_time)
                            
                            # Определяем дату записи
                            date_obj = entry_time_local.date()
                            
                            if date_obj not in entries_by_date:
                                entries_by_date[date_obj] = []
                            entries_by_date[date_obj].append(entry_exit)
                        except Exception as e:
                            logger.warning(f"Ошибка при обработке записи EntryExit (id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Ошибка при группировке записей по датам для сотрудника (id={employee.id}): {e}")
                    continue
                
                # Обрабатываем каждую запись
                for date_obj, date_entries in entries_by_date.items():
                    try:
                        # Определяем, является ли это рабочим днем
                        is_work_day = False
                        
                        try:
                            if schedule.schedule_type == 'round_the_clock':
                                # Круглосуточный график - все дни рабочие
                                is_work_day = True
                            elif schedule.schedule_type == 'regular':
                                # Обычный график - проверяем день недели
                                day_of_week = date_obj.weekday()  # 0 = понедельник, 6 = воскресенье
                                if schedule.days_of_week and day_of_week in schedule.days_of_week:
                                    is_work_day = True
                                elif not schedule.days_of_week:
                                    # Если дни не указаны, считаем все дни рабочими
                                    is_work_day = True
                            elif schedule.schedule_type == 'floating':
                                # Плавающий график - считаем все дни рабочими
                                is_work_day = True
                        except Exception as e:
                            logger.warning(f"Ошибка при определении рабочего дня для сотрудника (id={employee.id}, date={date_obj}): {e}")
                            continue
                        
                        if not is_work_day:
                            continue
            
                        # Определяем время начала и окончания смены для этой даты
                        try:
                            if schedule.schedule_type == 'round_the_clock':
                                # Для круглосуточного графика используем start_time как начало периода
                                if schedule.start_time:
                                    schedule_start_time = schedule.start_time
                                else:
                                    schedule_start_time = time(9, 0)  # 09:00 по умолчанию
                                
                                schedule_start = datetime.combine(date_obj, schedule_start_time)
                                schedule_end = datetime.combine(date_obj, schedule_start_time) + timedelta(days=1)
                                
                                schedule_start = timezone.make_aware(schedule_start)
                                schedule_end = timezone.make_aware(schedule_end)
                                schedule_start_local = timezone.localtime(schedule_start)
                                schedule_end_local = timezone.localtime(schedule_end)
                            else:
                                # Для обычного графика
                                if schedule.start_time and schedule.end_time:
                                    schedule_start = datetime.combine(date_obj, schedule.start_time)
                                    schedule_end = datetime.combine(date_obj, schedule.end_time)
                                    
                                    # Если время окончания меньше времени начала, значит смена переходит через полночь
                                    if schedule.end_time < schedule.start_time:
                                        schedule_end = schedule_end + timedelta(days=1)
                                    
                                    schedule_start = timezone.make_aware(schedule_start)
                                    schedule_end = timezone.make_aware(schedule_end)
                                    schedule_start_local = timezone.localtime(schedule_start)
                                    schedule_end_local = timezone.localtime(schedule_end)
                                else:
                                    continue
                        except Exception as e:
                            logger.warning(f"Ошибка при определении времени смены для сотрудника (id={employee.id}, date={date_obj}): {e}")
                            continue
            
                        # Сортируем записи за день по времени входа
                        try:
                            date_entries_sorted = sorted(date_entries, key=lambda x: x.entry_time if x.entry_time else datetime.min)
                        except Exception as e:
                            logger.warning(f"Ошибка при сортировке записей за день для сотрудника (id={employee.id}, date={date_obj}): {e}")
                            continue
                        
                        # Находим последний уход за день (для проверки раннего ухода)
                        last_exit_entry = None
                        last_exit_time_local = None
                        try:
                            for entry_exit in date_entries_sorted:
                                try:
                                    if entry_exit.exit_time:
                                        if timezone.is_naive(entry_exit.exit_time):
                                            exit_time = timezone.make_aware(entry_exit.exit_time)
                                        else:
                                            exit_time = entry_exit.exit_time
                                        exit_time_local = timezone.localtime(exit_time)
                                        
                                        if last_exit_time_local is None or exit_time_local > last_exit_time_local:
                                            last_exit_time_local = exit_time_local
                                            last_exit_entry = entry_exit
                                except Exception as e:
                                    logger.warning(f"Ошибка при обработке времени выхода (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                    continue
                        except Exception as e:
                            logger.warning(f"Ошибка при поиске последнего ухода для сотрудника (id={employee.id}, date={date_obj}): {e}")
                            continue
                        
                        # Флаги для отслеживания, было ли уже учтено опоздание и ранний уход за этот день
                        late_counted_for_day = False
                        early_leave_counted_for_day = False
                        
                        for entry_index, entry_exit in enumerate(date_entries_sorted):
                            try:
                                if not entry_exit.entry_time:
                                    continue
                                
                                # Конвертируем время входа
                                try:
                                    if timezone.is_naive(entry_exit.entry_time):
                                        entry_time = timezone.make_aware(entry_exit.entry_time)
                                    else:
                                        entry_time = entry_exit.entry_time
                                    entry_time_local = timezone.localtime(entry_time)
                                except Exception as e:
                                    logger.warning(f"Ошибка при конвертации времени входа (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                    continue
                                
                                # Конвертируем время выхода
                                exit_time_local = None
                                try:
                                    if entry_exit.exit_time:
                                        if timezone.is_naive(entry_exit.exit_time):
                                            exit_time = timezone.make_aware(entry_exit.exit_time)
                                        else:
                                            exit_time = entry_exit.exit_time
                                        exit_time_local = timezone.localtime(exit_time)
                                except Exception as e:
                                    logger.warning(f"Ошибка при конвертации времени выхода (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                
                                is_first_entry_of_day = (entry_index == 0)
                                
                                # Проверяем опоздание только для первого входа за день
                                if is_first_entry_of_day and not late_counted_for_day and entry_time_local > schedule_start_local:
                                    try:
                                        late_seconds = (entry_time_local - schedule_start_local).total_seconds()
                                        late_minutes = int(late_seconds / 60)
                                        
                                        if late_minutes > schedule.allowed_late_minutes:
                                            actual_late_minutes = late_minutes - schedule.allowed_late_minutes
                                            if actual_late_minutes > 0:
                                                try:
                                                    with transaction.atomic():
                                                        stats.increment_late()
                                                        total_late_count += 1
                                                        entry_exit.late_counted = True
                                                        entry_exit.save(update_fields=['late_counted'])
                                                        late_counted_for_day = True
                                                except (OperationalError, DatabaseError) as e:
                                                    logger.warning(f"Ошибка БД при сохранении опоздания (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                                    continue
                                    except Exception as e:
                                        logger.warning(f"Ошибка при обработке опоздания (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                        continue
            
                                # Проверяем ранний уход только для последнего ухода за день (не для круглосуточного графика)
                                if schedule.schedule_type != 'round_the_clock' and not early_leave_counted_for_day:
                                    try:
                                        if entry_exit == last_exit_entry and last_exit_time_local:
                                            if last_exit_time_local < schedule_end_local:
                                                early_seconds = (schedule_end_local - last_exit_time_local).total_seconds()
                                                early_minutes = int(early_seconds / 60)
                                                
                                                if early_minutes > schedule.allowed_early_leave_minutes:
                                                    actual_early_minutes = early_minutes - schedule.allowed_early_leave_minutes
                                                    if actual_early_minutes > 0:
                                                        try:
                                                            with transaction.atomic():
                                                                stats.increment_early_leave()
                                                                total_early_count += 1
                                                                entry_exit.early_leave_counted = True
                                                                entry_exit.save(update_fields=['early_leave_counted'])
                                                                early_leave_counted_for_day = True
                                                        except (OperationalError, DatabaseError) as e:
                                                            logger.warning(f"Ошибка БД при сохранении раннего ухода (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                                            continue
                                        elif not last_exit_entry:
                                            current_time = timezone.now()
                                            current_time_local = timezone.localtime(current_time)
                                            entry_date = entry_time_local.date()
                                            is_today = entry_date == current_time_local.date()
                                            should_count_as_incomplete = False
                                            
                                            if not is_today:
                                                should_count_as_incomplete = True
                                            elif current_time_local >= schedule_end_local + timedelta(hours=1):
                                                should_count_as_incomplete = True
                                            
                                            if should_count_as_incomplete and entry_index == 0 and not early_leave_counted_for_day:
                                                try:
                                                    with transaction.atomic():
                                                        stats.increment_early_leave()
                                                        total_early_count += 1
                                                        entry_exit.early_leave_counted = True
                                                        entry_exit.save(update_fields=['early_leave_counted'])
                                                        early_leave_counted_for_day = True
                                                except (OperationalError, DatabaseError) as e:
                                                    logger.warning(f"Ошибка БД при сохранении недоработки (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                                    continue
                                    except Exception as e:
                                        logger.warning(f"Ошибка при обработке раннего ухода (EntryExit id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                        continue
                            except Exception as e:
                                logger.warning(f"Ошибка при обработке записи EntryExit (id={entry_exit.id if hasattr(entry_exit, 'id') else 'unknown'}): {e}")
                                continue
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке даты {date_obj} для сотрудника (id={employee.id}): {e}")
                        continue
            except Exception as e:
                logger.error(f"Ошибка при обработке сотрудника (hikvision_id={employee_id}): {e}", exc_info=True)
                continue
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time.strftime('%H:%M:%S')}] Статистика: {duration:.1f}с, сотрудников={processed_employees}, опозданий={total_late_count}, уходов={total_early_count}")
    except Exception as e:
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time.strftime('%H:%M:%S')}] Ошибка при обновлении статистики (время до ошибки: {duration:.1f}с): {e}", exc_info=True)


if __name__ == '__main__':
    recalculate_attendance_stats()
