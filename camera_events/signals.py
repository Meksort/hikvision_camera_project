"""
Django signals for processing camera events with new clean scheduling system.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CameraEvent
from .event_processor import process_single_camera_event

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CameraEvent)
def camera_event_saved(sender, instance, created, **kwargs):
    """
    Signal handler that processes camera events instantly when they arrive.
    Creates or updates EntryExit records immediately for real-time updates.
    """
    if created:
        try:
            # Обрабатываем событие мгновенно для автоматического обновления данных
            process_single_camera_event(instance)
        except Exception as e:
            logger.error(f"Error processing camera event {instance.id}: {e}", exc_info=True)
