"""
УСТАРЕВШИЙ МОДУЛЬ - НЕ ИСПОЛЬЗУЕТСЯ

Вся логика обработки графиков перенесена в schedule_matcher.py.
Этот файл оставлен для обратной совместимости, но больше не содержит рабочей логики.
"""
import logging
from django.utils import timezone
from .models import CameraEvent

logger = logging.getLogger(__name__)


class AttendanceProcessor:
    """
    УСТАРЕВШИЙ КЛАСС - НЕ ИСПОЛЬЗУЕТСЯ
    
    Вся логика обработки графиков перенесена в schedule_matcher.ScheduleMatcher.
    Этот класс оставлен для обратной совместимости.
    """
    
    @staticmethod
    def process_camera_event(camera_event: CameraEvent):
        """
        УСТАРЕВШИЙ МЕТОД - НЕ ВЫПОЛНЯЕТ НИКАКИХ ДЕЙСТВИЙ
        
        Вся логика обработки графиков перенесена в schedule_matcher.py.
        Этот метод оставлен для обратной совместимости, но больше не выполняет никаких действий.
        
        Args:
            camera_event: The CameraEvent instance to process
        """
        # Метод оставлен пустым для обратной совместимости
        # Вся логика обработки графиков теперь в schedule_matcher.py
        pass

