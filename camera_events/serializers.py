"""
Сериализаторы для событий камер.
"""
from rest_framework import serializers
from .models import CameraEvent, EntryExit, Department, Employee, WorkSchedule


class CameraEventSerializer(serializers.ModelSerializer):
    """Сериализатор для событий камер."""
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    card_no = serializers.SerializerMethodField()
    event_type = serializers.SerializerMethodField()
    
    class Meta:
        model = CameraEvent
        fields = [
            "id",
            "hikvision_id",
            "employee_id",
            "employee_name",
            "card_no",
            "event_type",
            "device_name",
            "event_time",
            "picture_data",
            "raw_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "employee_id", "employee_name", "card_no", "event_type"]
    
    def _get_access_event(self, obj):
        """Извлекает вложенный AccessControllerEvent из raw_data."""
        if obj and obj.raw_data and isinstance(obj.raw_data, dict):
            outer_event = obj.raw_data.get("AccessControllerEvent", {})
            # Проверяем вложенную структуру
            if isinstance(outer_event, dict) and "AccessControllerEvent" in outer_event:
                return outer_event["AccessControllerEvent"]
            elif isinstance(outer_event, dict):
                return outer_event
        return {}
    
    def get_employee_id(self, obj):
        """Извлекает Employee ID из raw_data."""
        access_event = self._get_access_event(obj)
        return (
            access_event.get("employeeId") or
            access_event.get("employeeID") or
            access_event.get("employeeNo") or
            access_event.get("employeeNoString") or
            obj.hikvision_id or
            None
        )
    
    def get_employee_name(self, obj):
        """Извлекает имя сотрудника из raw_data."""
        access_event = self._get_access_event(obj)
        return (
            access_event.get("employeeName") or
            access_event.get("name") or
            access_event.get("employeeNameString") or
            None
        )
    
    def get_card_no(self, obj):
        """Извлекает номер карты из raw_data."""
        access_event = self._get_access_event(obj)
        return (
            access_event.get("cardNo") or
            access_event.get("cardNumber") or
            access_event.get("card") or
            None
        )
    
    def get_event_type(self, obj):
        """Извлекает тип события из raw_data."""
        access_event = self._get_access_event(obj)
        # Проверяем subEventType для определения типа
        sub_event_type = access_event.get("subEventType")
        if sub_event_type == 75:
            return "Authenticated via Face"
        
        return (
            access_event.get("eventType") or
            access_event.get("eventTypes") or
            access_event.get("eventDescription") or
            access_event.get("event") or
            None
        )


class EntryExitSerializer(serializers.ModelSerializer):
    """Сериализатор для записей входов и выходов."""
    work_duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = EntryExit
        fields = [
            "id",
            "hikvision_id",
            "entry_time",
            "exit_time",
            "device_name_entry",
            "device_name_exit",
            "work_duration_seconds",
            "work_duration_formatted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "work_duration_formatted"]


class EmployeeSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для сотрудников в структуре отделов."""
    position = serializers.SerializerMethodField()
    schedule_type = serializers.SerializerMethodField()
    schedule_description = serializers.SerializerMethodField()
    allowed_late_minutes = serializers.SerializerMethodField()
    allowed_early_leave_minutes = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'hikvision_id', 'name', 'position', 'schedule_type', 'schedule_description', 
                 'allowed_late_minutes', 'allowed_early_leave_minutes', 'department_name']
    
    def get_position(self, obj):
        """Возвращает должность сотрудника."""
        return obj.position if obj else None
    
    def get_department_name(self, obj):
        """Возвращает название подразделения сотрудника."""
        if obj:
            if obj.department:
                full_path = obj.department.get_full_path()
                # Убираем "АУП" или "АУП > " из начала пути
                if full_path.startswith("АУП > "):
                    result = full_path[6:]  # Убираем "АУП > "
                elif full_path.startswith("АУП"):
                    result = full_path[3:].lstrip(" > ")  # Убираем "АУП" и возможные разделители
                else:
                    result = full_path
                # Убираем ведущие разделители на случай, если они остались
                return result.lstrip("/ > ")
            elif obj.department_old:
                dept_old = obj.department_old
                # Убираем "АУП/" из начала для старого поля и заменяем "/" на " > "
                if dept_old.startswith("АУП/"):
                    result = dept_old[4:]  # Убираем "АУП/"
                elif dept_old.startswith("АУП"):
                    result = dept_old[3:].lstrip("/")  # Убираем "АУП" и возможные разделители
                else:
                    result = dept_old
                # Заменяем "/" на " > " и убираем ведущие разделители
                result = result.replace("/", " > ")
                return result.lstrip("/ > ")
        return None
    
    def get_schedule_type(self, obj):
        """Возвращает тип графика работы."""
        if obj:
            schedule = obj.work_schedules.first()
            if schedule:
                return schedule.get_schedule_type_display()
        return None
    
    def get_schedule_description(self, obj):
        """Возвращает описание графика работы."""
        if obj:
            schedule = obj.work_schedules.first()
            if schedule:
                return schedule.get_schedule_display()
        return None
    
    def get_allowed_late_minutes(self, obj):
        """Возвращает допустимое опоздание в минутах."""
        if obj:
            schedule = obj.work_schedules.first()
            if schedule:
                return schedule.allowed_late_minutes
        return None
    
    def get_allowed_early_leave_minutes(self, obj):
        """Возвращает допустимый ранний уход в минутах."""
        if obj:
            schedule = obj.work_schedules.first()
            if schedule:
                return schedule.allowed_early_leave_minutes
        return None


class DepartmentSerializer(serializers.ModelSerializer):
    """Сериализатор для подразделений."""
    full_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    employees = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "parent",
            "parent_name",
            "full_path",
            "employees",
            "children",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_path", "parent_name", "employees", "children"]
    
    def get_full_path(self, obj):
        """Возвращает полный путь подразделения."""
        return obj.get_full_path() if obj else None
    
    def get_parent_name(self, obj):
        """Возвращает название родительского подразделения."""
        return obj.parent.name if obj and obj.parent else None
    
    def get_employees(self, obj):
        """Возвращает список сотрудников отдела."""
        employees = obj.employees.all().prefetch_related('work_schedules').order_by('name')
        return EmployeeSimpleSerializer(employees, many=True).data
    
    def get_children(self, obj):
        """Возвращает дочерние отделы (рекурсивно)."""
        children = obj.children.all().order_by('name')
        return DepartmentSerializer(children, many=True).data
