"""
ViewSet для получения сотрудников с наибольшим количеством опозданий.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import Employee, EmployeeAttendanceStats
from ..utils import get_excluded_hikvision_ids


class TopLateEmployeesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения сотрудников с наибольшим количеством опозданий.
    """
    queryset = Employee.objects.none()
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        """
        Возвращает список сотрудников, отсортированных по количеству опозданий.
        
        Параметры:
        - limit - количество сотрудников для возврата (по умолчанию 10)
        """
        limit = int(request.query_params.get('limit', 10))
        
        # Получаем исключаемые ID
        excluded_hikvision_ids = get_excluded_hikvision_ids()
        
        # Получаем сотрудников с их статистикой опозданий
        employees_with_stats = Employee.objects.exclude(
            hikvision_id__in=excluded_hikvision_ids
        ).filter(
            hikvision_id__isnull=False
        ).select_related('department', 'attendance_stats').prefetch_related('work_schedules')
        
        employees_data = []
        
        for employee in employees_with_stats:
            # Получаем статистику опозданий
            late_count = 0
            early_leave_count = 0
            
            try:
                stats = employee.attendance_stats
                late_count = stats.late_count if stats else 0
                early_leave_count = stats.early_leave_count if stats else 0
            except EmployeeAttendanceStats.DoesNotExist:
                pass
            
            # Пропускаем сотрудников без опозданий
            if late_count == 0:
                continue
            
            # Получаем название отдела
            department_name = ""
            if employee.department:
                full_path = employee.department.get_full_path()
                if full_path.startswith("АУП > "):
                    department_name = full_path[6:]
                elif full_path.startswith("АУП"):
                    department_name = full_path[3:].lstrip("/ > ")
                else:
                    department_name = full_path
            elif employee.department_old:
                dept_old = employee.department_old
                if dept_old.startswith("АУП/"):
                    department_name = dept_old[4:].replace("/", " > ")
                elif dept_old.startswith("АУП"):
                    department_name = dept_old[3:].lstrip("/").replace("/", " > ")
                else:
                    department_name = dept_old.replace("/", " > ")
            
            # Аватар
            avatar = f"https://ui-avatars.com/api/?name={employee.name}&background=random"
            
            employees_data.append({
                "id": employee.id,
                "name": employee.name,
                "avatar": avatar,
                "department": department_name,
                "position": employee.position or "",
                "lateCount": late_count,
                "earlyLeaveCount": early_leave_count,
            })
        
        # Сортируем по количеству опозданий (по убыванию)
        employees_data.sort(key=lambda x: x["lateCount"], reverse=True)
        
        # Ограничиваем количество
        employees_data = employees_data[:limit]
        
        return Response({
            "employees": employees_data
        })


