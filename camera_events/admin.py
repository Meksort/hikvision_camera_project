"""
Админка для событий камер.
"""
from django.contrib import admin
from .models import CameraEvent, EntryExit, Employee, Department, WorkSchedule


@admin.register(CameraEvent)
class CameraEventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_employee_id",
        "get_employee_name",
        "get_card_no",
        "get_event_type",
        "device_name",
        "event_time",
        "created_at",
    ]
    list_filter = ["device_name", "event_time", "created_at"]
    search_fields = ["hikvision_id", "device_name", "raw_data"]
    readonly_fields = ["created_at", "updated_at", "raw_data", "get_employee_id", "get_employee_name", "get_card_no", "get_event_type"]
    date_hierarchy = "event_time"
    
    def get_employee_id(self, obj):
        """Извлекает Employee ID из raw_data."""
        if obj and obj.raw_data and isinstance(obj.raw_data, dict):
            outer_event = obj.raw_data.get("AccessControllerEvent", {})
            # Проверяем вложенную структуру
            if isinstance(outer_event, dict) and "AccessControllerEvent" in outer_event:
                access_event = outer_event["AccessControllerEvent"]
            else:
                access_event = outer_event if isinstance(outer_event, dict) else {}
            
            return (
                access_event.get("employeeId") or
                access_event.get("employeeID") or
                access_event.get("employeeNo") or
                access_event.get("employeeNoString") or
                obj.hikvision_id or
                "--"
            )
        return obj.hikvision_id or "--"
    get_employee_id.short_description = "Employee ID"
    get_employee_id.admin_order_field = "hikvision_id"
    
    def get_employee_name(self, obj):
        """Извлекает имя сотрудника из raw_data."""
        if obj and obj.raw_data and isinstance(obj.raw_data, dict):
            outer_event = obj.raw_data.get("AccessControllerEvent", {})
            # Проверяем вложенную структуру
            if isinstance(outer_event, dict) and "AccessControllerEvent" in outer_event:
                access_event = outer_event["AccessControllerEvent"]
            else:
                access_event = outer_event if isinstance(outer_event, dict) else {}
            
            return (
                access_event.get("employeeName") or
                access_event.get("name") or
                access_event.get("employeeNameString") or
                "--"
            )
        return "--"
    get_employee_name.short_description = "Имя"
    
    def get_card_no(self, obj):
        """Извлекает номер карты из raw_data."""
        if obj and obj.raw_data and isinstance(obj.raw_data, dict):
            outer_event = obj.raw_data.get("AccessControllerEvent", {})
            # Проверяем вложенную структуру
            if isinstance(outer_event, dict) and "AccessControllerEvent" in outer_event:
                access_event = outer_event["AccessControllerEvent"]
            else:
                access_event = outer_event if isinstance(outer_event, dict) else {}
            
            return (
                access_event.get("cardNo") or
                access_event.get("cardNumber") or
                access_event.get("card") or
                "--"
            )
        return "--"
    get_card_no.short_description = "Card No."
    
    def get_event_type(self, obj):
        """Извлекает тип события из raw_data."""
        if obj and obj.raw_data and isinstance(obj.raw_data, dict):
            outer_event = obj.raw_data.get("AccessControllerEvent", {})
            # Проверяем вложенную структуру
            if isinstance(outer_event, dict) and "AccessControllerEvent" in outer_event:
                access_event = outer_event["AccessControllerEvent"]
            else:
                access_event = outer_event if isinstance(outer_event, dict) else {}
            
            # Проверяем subEventType для определения типа
            sub_event_type = access_event.get("subEventType")
            if sub_event_type == 75:
                return "Authenticated via Face"
            
            return (
                access_event.get("eventType") or
                access_event.get("eventTypes") or
                access_event.get("eventDescription") or
                access_event.get("event") or
                "--"
            )
        return "--"
    get_event_type.short_description = "Event Type"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "get_full_path", "get_employees_count", "created_at"]
    list_filter = ["parent", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at", "get_full_path", "get_employees_count"]
    
    def get_full_path(self, obj):
        """Показывает полный путь подразделения."""
        return obj.get_full_path()
    get_full_path.short_description = "Полный путь"
    
    def get_employees_count(self, obj):
        """Показывает количество сотрудников в подразделении."""
        return obj.employees.count()
    get_employees_count.short_description = "Количество сотрудников"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["hikvision_id", "name", "department", "card_no", "created_at"]
    list_filter = ["department", "created_at"]
    search_fields = ["hikvision_id", "name", "department__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EntryExit)
class EntryExitAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "hikvision_id",
        "entry_time",
        "exit_time",
        "get_work_duration",
        "device_name_entry",
        "device_name_exit",
    ]
    list_filter = ["entry_time", "exit_time", "created_at"]
    search_fields = ["hikvision_id"]
    readonly_fields = ["created_at", "updated_at", "get_work_duration"]
    
    def get_work_duration(self, obj):
        """Возвращает продолжительность работы в формате 'Xч Ym'."""
        if obj and obj.work_duration_seconds:
            hours = obj.work_duration_seconds // 3600
            minutes = (obj.work_duration_seconds % 3600) // 60
            return f"{hours}ч {minutes}м"
        return "Не завершено"
    get_work_duration.short_description = "Продолжительность работы"
    get_work_duration.admin_order_field = "work_duration_seconds"


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ["employee", "schedule_type", "get_schedule_display", "allowed_late_minutes", "allowed_early_leave_minutes", "created_at"]
    list_filter = ["schedule_type", "created_at"]
    search_fields = ["employee__name", "employee__hikvision_id", "description"]
    readonly_fields = ["created_at", "updated_at", "get_schedule_display"]
    
    def get_schedule_display(self, obj):
        """Показывает описание графика."""
        return obj.get_schedule_display()
    get_schedule_display.short_description = "График работы"

