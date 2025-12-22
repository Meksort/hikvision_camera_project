"""
Модуль для сопоставления записей входов/выходов с графиками работы сотрудников.
"""
import logging
from datetime import datetime, timedelta, time
from django.utils import timezone
from .models import WorkSchedule, Employee, EntryExit

logger = logging.getLogger(__name__)


class ScheduleMatcher:
    """
    Класс для сопоставления записей входов/выходов с графиками работы.
    """
    
    @staticmethod
    def get_employee_schedule(employee: Employee, date) -> WorkSchedule:
        """
        Получает график работы сотрудника на указанную дату.
        
        Args:
            employee: Сотрудник
            date: Дата (date объект)
            
        Returns:
            WorkSchedule объект или None, если график не найден
        """
        try:
            # Получаем первый активный график сотрудника
            schedule = WorkSchedule.objects.filter(employee=employee).first()
            return schedule
        except Exception as e:
            logger.error(f"Ошибка при получении графика для сотрудника {employee.id}: {e}")
            return None
    
    @staticmethod
    def get_scheduled_time_for_date(schedule: WorkSchedule, date) -> tuple:
        """
        Получает запланированное время начала и окончания работы для указанной даты.
        
        Args:
            schedule: График работы
            date: Дата (date объект)
            
        Returns:
            Кортеж (scheduled_start, scheduled_end) где оба - datetime объекты,
            или None, если время не может быть определено
        """
        if not schedule:
            return None
        
        try:
            weekday = date.weekday()  # 0 = Понедельник, 6 = Воскресенье
            
            if schedule.schedule_type == 'round_the_clock':
                # Круглосуточный график - 24 часа
                start_dt = timezone.make_aware(datetime.combine(date, time(0, 0)))
                end_dt = start_dt + timedelta(days=1)
                return (start_dt, end_dt)
            
            elif schedule.schedule_type == 'floating':
                # Плавающий график - используем floating_shifts
                if schedule.floating_shifts and isinstance(schedule.floating_shifts, list):
                    # Ищем смену для текущего дня недели
                    for shift in schedule.floating_shifts:
                        if isinstance(shift, dict) and shift.get('day') == weekday:
                            start_str = shift.get('start', '08:00')
                            end_str = shift.get('end', '17:00')
                            
                            # Парсим время
                            start_hour, start_minute = map(int, start_str.split(':'))
                            end_hour, end_minute = map(int, end_str.split(':'))
                            
                            start_dt = timezone.make_aware(datetime.combine(date, time(start_hour, start_minute)))
                            end_dt = timezone.make_aware(datetime.combine(date, time(end_hour, end_minute)))
                            
                            # Если время окончания меньше времени начала, значит смена через полночь
                            if end_hour < start_hour or (end_hour == start_hour and end_minute < start_minute):
                                end_dt += timedelta(days=1)
                            
                            return (start_dt, end_dt)
                
                # Если смена не найдена, возвращаем None
                return None
            
            elif schedule.schedule_type == 'regular':
                # Обычный график - проверяем, есть ли этот день недели в расписании
                if schedule.days_of_week and weekday in schedule.days_of_week:
                    if schedule.start_time and schedule.end_time:
                        start_dt = timezone.make_aware(datetime.combine(date, schedule.start_time))
                        end_dt = timezone.make_aware(datetime.combine(date, schedule.end_time))
                        
                        # Если время окончания меньше времени начала, значит смена через полночь
                        if schedule.end_time < schedule.start_time:
                            end_dt += timedelta(days=1)
                        
                        return (start_dt, end_dt)
                
                # Если день не в расписании, возвращаем None
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении запланированного времени для графика {schedule.id} на дату {date}: {e}")
            return None
    
    @staticmethod
    def match_entry_exit_to_schedule(entry_exit: EntryExit, schedule: WorkSchedule) -> dict:
        """
        Сопоставляет запись входа/выхода с графиком работы и определяет опоздания/ранние уходы.
        
        Args:
            entry_exit: Запись входа/выхода
            schedule: График работы
            
        Returns:
            Словарь с результатами сопоставления:
            {
                'is_late': bool,
                'is_early_leave': bool,
                'late_minutes': int,
                'early_leave_minutes': int,
                'is_extra_shift': bool,
                'scheduled_start': datetime или None,
                'scheduled_end': datetime или None
            }
        """
        result = {
            'is_late': False,
            'is_early_leave': False,
            'late_minutes': 0,
            'early_leave_minutes': 0,
            'is_extra_shift': False,
            'scheduled_start': None,
            'scheduled_end': None
        }
        
        if not entry_exit or not entry_exit.entry_time or not schedule:
            result['is_extra_shift'] = True
            return result
        
        try:
            entry_date = entry_exit.entry_time.date()
            scheduled_times = ScheduleMatcher.get_scheduled_time_for_date(schedule, entry_date)
            
            if not scheduled_times:
                # График не определен для этого дня - это дополнительная смена
                result['is_extra_shift'] = True
                return result
            
            scheduled_start, scheduled_end = scheduled_times
            result['scheduled_start'] = scheduled_start
            result['scheduled_end'] = scheduled_end
            
            entry_time = entry_exit.entry_time
            
            # Проверяем опоздание
            if entry_time > scheduled_start:
                delay = entry_time - scheduled_start
                late_minutes = int(delay.total_seconds() / 60)
                
                # Учитываем допустимое опоздание
                allowed_late = schedule.allowed_late_minutes or 0
                if late_minutes > allowed_late:
                    result['is_late'] = True
                    result['late_minutes'] = late_minutes - allowed_late
            
            # Проверяем ранний уход (если есть время выхода)
            if entry_exit.exit_time and scheduled_end:
                exit_time = entry_exit.exit_time
                
                # Если смена через полночь, нужно правильно определить, к какой смене относится выход
                if scheduled_end > scheduled_start + timedelta(hours=12):
                    # Смена через полночь - выход должен быть на следующий день
                    if exit_time < scheduled_start:
                        # Выход до начала смены - это выход предыдущей смены
                        # Используем scheduled_end предыдущего дня
                        prev_date = entry_date - timedelta(days=1)
                        prev_scheduled_times = ScheduleMatcher.get_scheduled_time_for_date(schedule, prev_date)
                        if prev_scheduled_times:
                            _, prev_scheduled_end = prev_scheduled_times
                            scheduled_end = prev_scheduled_end
                
                if exit_time < scheduled_end:
                    delay = scheduled_end - exit_time
                    early_minutes = int(delay.total_seconds() / 60)
                    
                    # Учитываем допустимый ранний уход
                    allowed_early = schedule.allowed_early_leave_minutes or 0
                    if early_minutes > allowed_early:
                        result['is_early_leave'] = True
                        result['early_leave_minutes'] = early_minutes - allowed_early
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при сопоставлении записи {entry_exit.id} с графиком {schedule.id}: {e}")
            result['is_extra_shift'] = True
            return result
