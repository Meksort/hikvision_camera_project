"""
Обработка событий от камер Hikvision.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from .models import CameraEvent, EntryExit
from .utils import clean_id

logger = logging.getLogger(__name__)


def process_single_camera_event(camera_event):
    """
    Обрабатывает одно событие от камеры и мгновенно создает/обновляет EntryExit запись.
    Вызывается автоматически при получении нового события через сигнал.
    
    Args:
        camera_event: Экземпляр CameraEvent для обработки
    """
    try:
        if not camera_event.hikvision_id or not camera_event.event_time:
            return
        
        # Очищаем ID от ведущих нулей
        clean_employee_id = clean_id(camera_event.hikvision_id)
        
        # Определяем тип события (вход/выход) по IP адресу или device_name
        is_entry = False
        is_exit = False
        
        camera_ip = None
        try:
            if camera_event.raw_data and isinstance(camera_event.raw_data, dict):
                outer_event = camera_event.raw_data.get("AccessControllerEvent", {})
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
                        camera_event.raw_data.get("ipAddress") or
                        camera_event.raw_data.get("remoteHostAddr") or
                        camera_event.raw_data.get("ip") or
                        None
                    )
        except Exception as e:
            logger.warning(f"Ошибка при извлечении IP из события {camera_event.id}: {e}")
        
        # Определяем тип события
        # ПРИОРИТЕТ: Сначала проверяем IP адрес (самый надежный способ)
        if camera_ip:
            camera_ip_str = str(camera_ip)
            # ВЫХОД: IP содержит 143 или 192.168.1.143
            if "192.168.1.143" in camera_ip_str or camera_ip_str.endswith(".143") or camera_ip_str == "143":
                is_exit = True
            # ВХОД: IP содержит 124 или 192.168.1.124
            elif "192.168.1.124" in camera_ip_str or camera_ip_str.endswith(".124") or camera_ip_str == "124":
                is_entry = True
        
        # Если IP не определен, проверяем device_name
        if not is_entry and not is_exit:
            device_name_lower = (camera_event.device_name or "").lower()
            # ВХОД: проверяем ключевые слова
            is_entry = any(word in device_name_lower for word in ['вход', 'entry', 'входная', 'вход 1', 'вход1', '124'])
            # ВЫХОД: проверяем ключевые слова
            is_exit = any(word in device_name_lower for word in ['выход', 'exit', 'выходная', 'выход 1', 'выход1', '143'])
        
        if not (is_entry or is_exit):
            return
        
        event_date = camera_event.event_time.date()
        event_time = camera_event.event_time
        
        if is_entry:
            # Событие входа - создаем или обновляем запись EntryExit
            # Ищем существующую запись без выхода за этот день
            existing = EntryExit.objects.filter(
                hikvision_id=clean_employee_id,
                entry_time__date=event_date,
                exit_time__isnull=True
            ).order_by('-entry_time').first()
            
            if existing:
                # Обновляем существующую запись, если новый вход позже
                if event_time > existing.entry_time:
                    existing.entry_time = event_time
                    existing.device_name_entry = camera_event.device_name
                    existing.save()
                    logger.info(f"Обновлена запись EntryExit для сотрудника {clean_employee_id} на {event_date}")
            else:
                # Создаем новую запись входа
                EntryExit.objects.create(
                    hikvision_id=clean_employee_id,
                    entry_time=event_time,
                    exit_time=None,
                    device_name_entry=camera_event.device_name,
                    device_name_exit=None,
                    work_duration_seconds=None,
                )
                logger.info(f"Создана запись EntryExit (вход) для сотрудника {clean_employee_id} на {event_date}")
        
        elif is_exit:
            # Событие выхода - обновляем существующую запись EntryExit
            # Ищем запись входа без выхода за этот день или предыдущий день (для ночных смен)
            yesterday = event_date - timedelta(days=1)
            
            # Сначала ищем за сегодня
            existing = EntryExit.objects.filter(
                hikvision_id=clean_employee_id,
                entry_time__date=event_date,
                exit_time__isnull=True
            ).order_by('-entry_time').first()
            
            # Если не нашли за сегодня, ищем за вчера (для ночных смен)
            if not existing:
                existing = EntryExit.objects.filter(
                    hikvision_id=clean_employee_id,
                    entry_time__date=yesterday,
                    exit_time__isnull=True
                ).order_by('-entry_time').first()
            
            if existing:
                # УЛУЧШЕННАЯ ЛОГИКА: Если есть вход (IP 124) и выход (IP 143), обязательно создаем полную запись
                # Проверяем, что выход не раньше входа
                if event_time > existing.entry_time:
                    duration = event_time - existing.entry_time
                    hours_diff = duration.total_seconds() / 3600
                    # УВЕЛИЧЕН диапазон: от 30 минут до 24 часов (для учета длинных смен и ночных смен)
                    # Это гарантирует, что если есть вход (IP 124) и выход (IP 143), они будут сопоставлены
                    if 0.5 <= hours_diff <= 24:
                        existing.exit_time = event_time
                        existing.device_name_exit = camera_event.device_name
                        existing.work_duration_seconds = int(duration.total_seconds())
                        existing.save()
                        logger.info(f"Обновлена запись EntryExit (выход) для сотрудника {clean_employee_id} на {existing.entry_time.date()}, продолжительность: {hours_diff:.2f} часов")
                    else:
                        logger.warning(f"Выход для сотрудника {clean_employee_id} отклонен: продолжительность {hours_diff:.2f} часов вне допустимого диапазона (0.5-24 часа)")
            else:
                # Если нет записи входа, создаем запись только с выходом (неполная запись)
                EntryExit.objects.create(
                    hikvision_id=clean_employee_id,
                    entry_time=None,
                    exit_time=event_time,
                    device_name_entry=None,
                    device_name_exit=camera_event.device_name,
                    work_duration_seconds=None,
                )
                logger.info(f"Создана запись EntryExit (только выход) для сотрудника {clean_employee_id} на {event_date}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке события камеры {camera_event.id}: {e}", exc_info=True)










