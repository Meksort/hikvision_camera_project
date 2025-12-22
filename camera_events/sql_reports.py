"""
Оптимизированные SQL запросы для генерации отчетов.
Использует raw SQL для максимальной производительности.
"""
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta, time, date
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def generate_attendance_report_sql(
    hikvision_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    device_name: Optional[str] = None,
    excluded_hikvision_ids: Optional[List[str]] = None
) -> List[Dict]:
    """
    Генерирует отчет о посещаемости используя оптимизированные SQL запросы.
    
    Args:
        hikvision_id: ID сотрудника от Hikvision (опционально)
        start_date: Начальная дата (формат: YYYY-MM-DD)
        end_date: Конечная дата (формат: YYYY-MM-DD)
        device_name: Фильтр по названию устройства
        excluded_hikvision_ids: Список ID для исключения
        
    Returns:
        Список словарей с данными для отчета
    """
    # Парсим даты
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            if ' ' in start_date or 'T' in start_date:
                start_date_clean = start_date.replace('T', ' ')
                try:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M")
            else:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime)
        except ValueError:
            pass
    
    if end_date:
        try:
            if ' ' in end_date or 'T' in end_date:
                end_date_clean = end_date.replace('T', ' ')
                try:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M")
            else:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            if timezone.is_naive(end_datetime):
                from datetime import timezone as dt_timezone
                almaty_offset = dt_timezone(timedelta(hours=5))
                end_datetime = end_datetime.replace(tzinfo=almaty_offset)
                end_datetime = end_datetime.astimezone(dt_timezone.utc)
            
            # Расширяем на день для ночных смен
            end_datetime = end_datetime + timedelta(days=1)
        except ValueError:
            pass
    
    # Строим SQL запрос
    with connection.cursor() as cursor:
        # Базовый запрос с JOIN'ами для получения всех нужных данных
        query = """
        SELECT 
            e.id as employee_id,
            e.hikvision_id,
            e.name as employee_name,
            COALESCE(d.name, e.department_old, '') as department_name,
            DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty') as report_date,
            EXTRACT(DOW FROM ee.entry_time AT TIME ZONE 'Asia/Almaty') as day_of_week,
            ws.schedule_type,
            ws.start_time as schedule_start_time,
            ws.end_time as schedule_end_time,
            -- Конвертируем время из UTC в местное время (Asia/Almaty, UTC+5)
            MIN(ee.entry_time AT TIME ZONE 'Asia/Almaty') as first_entry,
            MAX(ee.exit_time AT TIME ZONE 'Asia/Almaty') as last_exit,
            COUNT(DISTINCT DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty')) as days_count,
            -- Рассчитываем продолжительность как разницу между первым входом и последним выходом за день
            -- Используем исходные UTC времена для правильного расчета разницы
            EXTRACT(EPOCH FROM (
                MAX(ee.exit_time AT TIME ZONE 'Asia/Almaty')::timestamp - 
                MIN(ee.entry_time AT TIME ZONE 'Asia/Almaty')::timestamp
            )) as total_duration_seconds
        FROM camera_events_entryexit ee
        INNER JOIN camera_events_employee e ON ee.hikvision_id = e.hikvision_id
        LEFT JOIN camera_events_department d ON e.department_id = d.id
        LEFT JOIN camera_events_workschedule ws ON ws.employee_id = e.id
        WHERE ee.entry_time IS NOT NULL
            AND ee.exit_time IS NOT NULL
        """
        
        params = []
        
        # Фильтр по hikvision_id
        if hikvision_id:
            # Очищаем ID от ведущих нулей
            clean_id_str = hikvision_id.lstrip('0') or '0'
            query += " AND (ee.hikvision_id = %s OR ee.hikvision_id = %s)"
            params.extend([clean_id_str, hikvision_id])
        
        # Фильтр по датам
        if start_datetime:
            query += " AND ee.entry_time >= %s"
            params.append(start_datetime)
        
        if end_datetime:
            query += " AND ee.entry_time <= %s"
            params.append(end_datetime)
        
        # Фильтр по device_name
        if device_name:
            query += " AND (ee.device_name_entry ILIKE %s OR ee.device_name_exit ILIKE %s)"
            params.extend([f'%{device_name}%', f'%{device_name}%'])
        
        # Исключаем определенных сотрудников
        if excluded_hikvision_ids:
            placeholders = ','.join(['%s'] * len(excluded_hikvision_ids))
            query += f" AND ee.hikvision_id NOT IN ({placeholders})"
            params.extend(excluded_hikvision_ids)
        
        # Группировка
        query += """
        GROUP BY 
            e.id, e.hikvision_id, e.name, d.name, e.department_old,
            DATE(ee.entry_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Almaty'),
            EXTRACT(DOW FROM ee.entry_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Almaty'),
            ws.schedule_type, ws.start_time, ws.end_time
        ORDER BY e.name, report_date
        """
        
        logger.info(f"Executing SQL query with {len(params)} parameters")
        cursor.execute(query, params)
        
        # Получаем результаты
        columns = [col[0] for col in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        return results


def generate_round_the_clock_report_sql(
    hikvision_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    schedule_start_time: time = time(9, 0)
) -> List[Dict]:
    """
    Оптимизированный SQL запрос для круглосуточных графиков.
    Использует оконные функции PostgreSQL для группировки по периодам графика.
    
    Args:
        hikvision_id: ID сотрудника от Hikvision
        start_date: Начальная дата
        end_date: Конечная дата
        schedule_start_time: Время начала периода графика (по умолчанию 09:00)
        
    Returns:
        Список словарей с данными для отчета
    """
    # Парсим даты
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            if ' ' in start_date or 'T' in start_date:
                start_date_clean = start_date.replace('T', ' ')
                try:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M")
            else:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime)
        except ValueError:
            pass
    
    if end_date:
        try:
            if ' ' in end_date or 'T' in end_date:
                end_date_clean = end_date.replace('T', ' ')
                try:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M")
            else:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            if timezone.is_naive(end_datetime):
                from datetime import timezone as dt_timezone
                almaty_offset = dt_timezone(timedelta(hours=5))
                end_datetime = end_datetime.replace(tzinfo=almaty_offset)
                end_datetime = end_datetime.astimezone(dt_timezone.utc)
            
            end_datetime = end_datetime + timedelta(days=1)
        except ValueError:
            pass
    
    # Время начала периода в секундах от начала дня
    schedule_start_seconds = schedule_start_time.hour * 3600 + schedule_start_time.minute * 60
    
    with connection.cursor() as cursor:
        # Используем CTE для определения периода графика для каждой записи
        query = f"""
        WITH entry_exits_with_period AS (
            SELECT 
                ee.id,
                ee.hikvision_id,
                ee.entry_time,
                ee.exit_time,
                e.name as employee_name,
                COALESCE(d.name, e.department_old, '') as department_name,
                -- Определяем дату периода графика
                CASE 
                    WHEN EXTRACT(HOUR FROM ee.entry_time AT TIME ZONE 'Asia/Almaty') * 3600 + 
                         EXTRACT(MINUTE FROM ee.entry_time AT TIME ZONE 'Asia/Almaty') * 60 < {schedule_start_seconds}
                    THEN DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty') - INTERVAL '1 day'
                    ELSE DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty')
                END::date as period_date,
                -- Время входа в локальном часовом поясе (конвертируем из UTC в Asia/Almaty)
                ee.entry_time AT TIME ZONE 'Asia/Almaty' as entry_local,
                -- Время выхода в локальном часовом поясе (конвертируем из UTC в Asia/Almaty)
                ee.exit_time AT TIME ZONE 'Asia/Almaty' as exit_local
            FROM camera_events_entryexit ee
            INNER JOIN camera_events_employee e ON ee.hikvision_id = e.hikvision_id
            LEFT JOIN camera_events_department d ON e.department_id = d.id
            WHERE ee.entry_time IS NOT NULL
                AND ee.exit_time IS NOT NULL
        """
        
        params = []
        
        # Фильтр по hikvision_id
        if hikvision_id:
            clean_id_str = hikvision_id.lstrip('0') or '0'
            query += " AND (ee.hikvision_id = %s OR ee.hikvision_id = %s)"
            params.extend([clean_id_str, hikvision_id])
        
        # Фильтр по датам
        if start_datetime:
            query += " AND ee.entry_time >= %s"
            params.append(start_datetime)
        
        if end_datetime:
            query += " AND ee.entry_time <= %s"
            params.append(end_datetime)
        
        # Основной запрос с агрегацией по периодам
        query += """
        )
        SELECT 
            hikvision_id,
            employee_name,
            department_name,
            period_date as report_date,
            EXTRACT(DOW FROM period_date) as day_of_week,
            MIN(entry_local) as first_entry,
            MAX(exit_local) as last_exit,
            -- Рассчитываем продолжительность как разницу между первым входом и последним выходом
            -- Для круглосуточных графиков обрезаем по границам периода (24 часа максимум)
            LEAST(
                EXTRACT(EPOCH FROM (MAX(exit_local)::timestamp - MIN(entry_local)::timestamp)),
                EXTRACT(EPOCH FROM INTERVAL '24 hours')
            ) as total_duration_seconds
        FROM entry_exits_with_period
        GROUP BY hikvision_id, employee_name, department_name, period_date
        ORDER BY employee_name, period_date
        """
        
        logger.info(f"Executing round-the-clock SQL query with {len(params)} parameters")
        cursor.execute(query, params)
        
        # Получаем результаты
        columns = [col[0] for col in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        return results


def generate_comprehensive_attendance_report_sql(
    hikvision_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    device_name: Optional[str] = None,
    excluded_hikvision_ids: Optional[List[str]] = None
) -> Tuple[List[Dict], date, date]:
    """
    Комплексный SQL запрос для генерации полного отчета о посещаемости.
    Включает обработку всех типов графиков, опозданий, ранних уходов.
    
    Args:
        hikvision_id: ID сотрудника от Hikvision (опционально)
        start_date: Начальная дата (формат: YYYY-MM-DD)
        end_date: Конечная дата (формат: YYYY-MM-DD)
        device_name: Фильтр по названию устройства
        excluded_hikvision_ids: Список ID для исключения
        
    Returns:
        Кортеж: (список словарей с данными для отчета, start_date_obj, end_date_obj)
    """
    # Парсим даты
    start_datetime = None
    end_datetime = None
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            if ' ' in start_date or 'T' in start_date:
                start_date_clean = start_date.replace('T', ' ')
                try:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    start_datetime = datetime.strptime(start_date_clean, "%Y-%m-%d %H:%M")
            else:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            
            start_date_obj = start_datetime.date()
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime)
        except ValueError:
            pass
    
    if end_date:
        try:
            if ' ' in end_date or 'T' in end_date:
                end_date_clean = end_date.replace('T', ' ')
                try:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    end_datetime = datetime.strptime(end_date_clean, "%Y-%m-%d %H:%M")
            else:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            end_date_obj = end_datetime.date()
            if timezone.is_naive(end_datetime):
                from datetime import timezone as dt_timezone
                almaty_offset = dt_timezone(timedelta(hours=5))
                end_datetime = end_datetime.replace(tzinfo=almaty_offset)
                end_datetime = end_datetime.astimezone(dt_timezone.utc)
            
            end_datetime = end_datetime + timedelta(days=1)
        except ValueError:
            pass
    
    # Если даты не указаны, используем текущий месяц
    if not start_date_obj:
        today = timezone.now().date()
        start_date_obj = datetime(today.year, today.month, 1).date()
    if not end_date_obj:
        end_date_obj = timezone.now().date()
    
    with connection.cursor() as cursor:
        # Сложный запрос с обработкой всех типов графиков
        query = """
        WITH 
        -- Определяем период графика для каждой записи
        entry_exits_with_period AS (
            SELECT 
                ee.id,
                ee.hikvision_id,
                ee.entry_time,
                ee.exit_time,
                e.name as employee_name,
                COALESCE(
                    CASE 
                        WHEN d.parent_id IS NOT NULL THEN 
                            (SELECT name FROM camera_events_department WHERE id = d.parent_id) || ' > ' || d.name
                        ELSE d.name
                    END,
                    e.department_old,
                    ''
                ) as department_name,
                ws.schedule_type,
                ws.start_time as schedule_start_time,
                ws.end_time as schedule_end_time,
                ws.allowed_late_minutes,
                ws.allowed_early_leave_minutes,
                -- Определяем дату периода графика
                -- ВАЖНО: Для круглосуточных графиков всегда используем дату ВХОДА (начало смены)
                -- Это гарантирует, что смена, начавшаяся 4 декабря и закончившаяся 5 декабря,
                -- будет засчитана только за 4 декабря
                CASE 
                    WHEN ws.schedule_type = 'round_the_clock' THEN
                        -- Для круглосуточных графиков: всегда используем дату входа
                        -- Если вход до времени начала смены (например, до 09:00), 
                        -- то это смена предыдущего дня
                        CASE 
                            WHEN EXTRACT(HOUR FROM ee.entry_time AT TIME ZONE 'Asia/Almaty') * 3600 + 
                                 EXTRACT(MINUTE FROM ee.entry_time AT TIME ZONE 'Asia/Almaty') * 60 < 
                                 (COALESCE(EXTRACT(HOUR FROM ws.start_time)::int, 9) * 3600 + 
                                  COALESCE(EXTRACT(MINUTE FROM ws.start_time)::int, 0) * 60)
                            THEN DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty') - INTERVAL '1 day'
                            ELSE DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty')
                        END
                    ELSE DATE(ee.entry_time AT TIME ZONE 'Asia/Almaty')
                END::date as period_date,
                -- Время входа и выхода в локальном часовом поясе (конвертируем из UTC в Asia/Almaty)
                ee.entry_time AT TIME ZONE 'Asia/Almaty' as entry_local,
                ee.exit_time AT TIME ZONE 'Asia/Almaty' as exit_local,
                -- Вычисляем продолжительность для каждой записи (в секундах)
                -- Правильно обрабатываем случаи, когда выход на следующий день
                EXTRACT(EPOCH FROM (
                    (ee.exit_time AT TIME ZONE 'Asia/Almaty')::timestamp - 
                    (ee.entry_time AT TIME ZONE 'Asia/Almaty')::timestamp
                )) as individual_duration_seconds
            FROM camera_events_entryexit ee
            INNER JOIN camera_events_employee e ON ee.hikvision_id = e.hikvision_id
            LEFT JOIN camera_events_department d ON e.department_id = d.id
            LEFT JOIN camera_events_workschedule ws ON ws.employee_id = e.id
            WHERE ee.entry_time IS NOT NULL
                AND ee.exit_time IS NOT NULL
        """
        
        params = []
        
        # Фильтр по hikvision_id
        if hikvision_id:
            clean_id_str = hikvision_id.lstrip('0') or '0'
            query += " AND (ee.hikvision_id = %s OR ee.hikvision_id = %s)"
            params.extend([clean_id_str, hikvision_id])
        
        # Фильтр по датам
        if start_datetime:
            query += " AND ee.entry_time >= %s"
            params.append(start_datetime)
        
        if end_datetime:
            query += " AND ee.entry_time <= %s"
            params.append(end_datetime)
        
        # Фильтр по device_name
        if device_name:
            query += " AND (ee.device_name_entry ILIKE %s OR ee.device_name_exit ILIKE %s)"
            params.extend([f'%{device_name}%', f'%{device_name}%'])
        
        # Исключаем определенных сотрудников
        if excluded_hikvision_ids:
            placeholders = ','.join(['%s'] * len(excluded_hikvision_ids))
            query += f" AND ee.hikvision_id NOT IN ({placeholders})"
            params.extend(excluded_hikvision_ids)
        
        # Основной запрос с агрегацией
        query += """
        ),
        -- Предварительно вычисляем среднее время входов для круглосуточных графиков
        round_the_clock_avg_entry AS (
            SELECT 
                hikvision_id,
                period_date,
                -- Среднее время входов между 7:00 и 12:00
                CASE 
                    WHEN COUNT(CASE 
                        WHEN EXTRACT(HOUR FROM entry_local) >= 7 
                        AND EXTRACT(HOUR FROM entry_local) < 12 
                        THEN 1 END) > 0
                    THEN 
                        -- Вычисляем среднее время входов между 7:00 и 12:00
                        (DATE(period_date) + 
                         AVG(CASE 
                             WHEN EXTRACT(HOUR FROM entry_local) >= 7 
                             AND EXTRACT(HOUR FROM entry_local) < 12 
                             THEN EXTRACT(EPOCH FROM (entry_local::time - '00:00:00'::time))
                             ELSE NULL
                         END) * INTERVAL '1 second'
                        )::timestamp
                    ELSE 
                        -- Если нет входов в промежутке 7:00-12:00, используем среднее время (9:30)
                        (DATE(period_date) + '09:30:00'::time)::timestamp
                END as avg_entry_time
            FROM entry_exits_with_period
            WHERE schedule_type = 'round_the_clock'
            GROUP BY hikvision_id, period_date
        ),
        -- Агрегируем данные по сотруднику и дате
        -- ВАЖНО: Для круглосуточных графиков period_date определяется по дате ВХОДА
        -- Это гарантирует, что смена, начавшаяся 4 декабря и закончившаяся 5 декабря,
        -- будет засчитана ТОЛЬКО за 4 декабря (дату начала смены)
        aggregated_data AS (
            SELECT 
                eep.hikvision_id,
                eep.employee_name,
                eep.department_name,
                eep.period_date as report_date,
                EXTRACT(DOW FROM eep.period_date) as day_of_week,
                eep.schedule_type,
                eep.schedule_start_time,
                eep.schedule_end_time,
                eep.allowed_late_minutes,
                eep.allowed_early_leave_minutes,
                -- Для круглосуточных графиков используем среднее время входов между 7:00 и 12:00
                -- Для остальных графиков используем MIN
                CASE 
                    WHEN eep.schedule_type = 'round_the_clock' THEN
                        COALESCE(rtc.avg_entry_time, (DATE(eep.period_date) + '09:30:00'::time)::timestamp)
                    ELSE 
                        MIN(eep.entry_local)
                END as first_entry,
                MAX(eep.exit_local) as last_exit,
                -- Рассчитываем продолжительность работы
                -- НОВАЯ ФОРМУЛА: Для круглосуточных графиков используем ТОЛЬКО ФАКТИЧЕСКОЕ время из базы данных
                -- ВАЖНО: 
                -- 1. Считаем ТОЛЬКО если есть фактические записи entry/exit в базе данных
                -- 2. Используем РЕАЛЬНОЕ время между входом и выходом (без ограничений)
                -- 3. Если вход 4 декабря 9:00, выход 5 декабря 9:00 - считаем 24 часа
                -- 4. Если вход 4 декабря 9:00, выход 5 декабря 7:00 - считаем 22 часа (фактическое время)
                -- 5. Если нет записей в базе - НЕ считаем (0 часов)
                CASE 
                    WHEN eep.schedule_type = 'round_the_clock' THEN
                        -- Для круглосуточных графиков: используем ТОЛЬКО фактические записи из базы данных
                        -- Суммируем все индивидуальные периоды работы
                        -- period_date определяется по дате ВХОДА, поэтому смена засчитывается за день начала
                        CASE 
                            WHEN COUNT(eep.entry_local) > 0 AND COUNT(eep.exit_local) > 0 THEN
                                -- Есть фактические записи в базе - используем РЕАЛЬНОЕ время работы
                                -- Суммируем все индивидуальные периоды (entry-exit для каждой записи)
                                -- НЕ ограничиваем 24 часами - используем фактическое время из базы
                                COALESCE(SUM(eep.individual_duration_seconds), 0)
                            ELSE
                                -- Нет фактических записей в базе - НЕ считаем (0 часов)
                                0
                        END
                    ELSE
                        -- Для обычных графиков используем фактическое время работы
                        -- Ограничиваем максимум 16 часами
                        LEAST(
                            EXTRACT(EPOCH FROM (MAX(eep.exit_local)::timestamp - MIN(eep.entry_local)::timestamp)),
                            EXTRACT(EPOCH FROM INTERVAL '16 hours')
                        )
                END as total_duration_seconds,
                -- Рассчитываем опоздание (в минутах)
                CASE 
                    WHEN eep.schedule_start_time IS NOT NULL AND eep.schedule_type != 'round_the_clock' THEN
                        GREATEST(
                            0,
                            (EXTRACT(EPOCH FROM (
                                MIN(eep.entry_local)::timestamp - 
                                (eep.period_date::date + eep.schedule_start_time::time)::timestamp
                            )) / 60.0)::numeric
                            - COALESCE(eep.allowed_late_minutes, 0)
                        )
                    ELSE 0
                END as late_minutes,
                -- Рассчитываем ранний уход (в минутах)
                CASE 
                    WHEN eep.schedule_end_time IS NOT NULL AND eep.schedule_type != 'round_the_clock' THEN
                        -- Определяем дату окончания смены (может быть следующий день для ночных смен)
                        CASE 
                            WHEN eep.schedule_end_time < eep.schedule_start_time THEN
                                -- Ночная смена - выход на следующий день
                                GREATEST(
                                    0,
                                    (EXTRACT(EPOCH FROM (
                                        (eep.period_date::date + INTERVAL '1 day' + eep.schedule_end_time::time)::timestamp - 
                                        MAX(eep.exit_local)::timestamp
                                    )) / 60.0)::numeric
                                    - COALESCE(eep.allowed_early_leave_minutes, 0)
                                )
                            ELSE
                                -- Обычная смена - выход в тот же день
                                GREATEST(
                                    0,
                                    (EXTRACT(EPOCH FROM (
                                        (eep.period_date::date + eep.schedule_end_time::time)::timestamp - 
                                        MAX(eep.exit_local)::timestamp
                                    )) / 60.0)::numeric
                                    - COALESCE(eep.allowed_early_leave_minutes, 0)
                                )
                        END
                    ELSE 0
                END as early_leave_minutes
            FROM entry_exits_with_period eep
            LEFT JOIN round_the_clock_avg_entry rtc 
                ON eep.hikvision_id = rtc.hikvision_id 
                AND eep.period_date = rtc.period_date
                AND eep.schedule_type = 'round_the_clock'
            GROUP BY 
                eep.hikvision_id, eep.employee_name, eep.department_name, eep.period_date,
                eep.schedule_type, eep.schedule_start_time, eep.schedule_end_time,
                eep.allowed_late_minutes, eep.allowed_early_leave_minutes,
                rtc.avg_entry_time
        )
        SELECT 
            hikvision_id,
            employee_name,
            department_name,
            report_date,
            day_of_week,
            schedule_type,
            schedule_start_time,
            schedule_end_time,
            allowed_late_minutes,
            allowed_early_leave_minutes,
            first_entry,
            last_exit,
            total_duration_seconds,
            late_minutes,
            early_leave_minutes
        FROM aggregated_data
        ORDER BY employee_name, report_date
        """
        
        logger.info(f"Executing comprehensive SQL query with {len(params)} parameters")
        cursor.execute(query, params)
        
        # Получаем результаты
        columns = [col[0] for col in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        return results, start_date_obj, end_date_obj

