"""
ViewSet для отделов.
"""
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from ..models import Department
from ..serializers import DepartmentSerializer
from ..utils import EXCLUDED_DEPARTMENTS


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения структуры отделов и сотрудников.
    """
    queryset = Department.objects.filter(parent=None).order_by("name")
    permission_classes = [AllowAny]
    serializer_class = DepartmentSerializer
    
    def get_queryset(self):
        """Возвращает только корневые отделы (без родителя), исключая указанные подразделения."""
        queryset = Department.objects.filter(parent=None).order_by("name")
        # Исключаем подразделения по имени (используем глобальную константу)
        queryset = queryset.exclude(name__in=EXCLUDED_DEPARTMENTS)
        return queryset











