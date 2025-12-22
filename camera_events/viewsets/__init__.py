"""
ViewSet'ы для приложения camera_events.

Пока что только DepartmentViewSet вынесен в отдельный файл.
Остальные ViewSet'ы находятся в views.py и будут вынесены позже.
"""
from .department import DepartmentViewSet

__all__ = [
    'DepartmentViewSet',
]

