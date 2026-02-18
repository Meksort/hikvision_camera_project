"""
Модели для хранения событий от камер Hikvision.
"""
import re
from django.db import models


class Department(models.Model):
    """
    Модель для хранения подразделений с поддержкой иерархии.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Название подразделения",
        db_index=True,
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительское подразделение",
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["parent"]),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Возвращает полный путь подразделения через ' > '."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " > ".join(path)


class CameraEvent(models.Model):
    """
    Модель для хранения событий от камер Hikvision.
    """
    # Данные события
    hikvision_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="ID от Hikvision",
        db_index=True,
    )
    device_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Название устройства/камеры",
    )
    event_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время события",
        db_index=True,
    )
    
    # Изображение
    picture_data = models.TextField(
        null=True,
        blank=True,
        verbose_name="Фото в формате Base64",
    )
    
    # Сырые данные
    raw_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Сырые данные события",
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "Событие камеры"
        verbose_name_plural = "События камер"
        ordering = ["-event_time", "-created_at"]
        indexes = [
            models.Index(fields=["hikvision_id", "event_time"]),
            models.Index(fields=["device_name", "event_time"]),
        ]
    
    def __str__(self):
        return f"CameraEvent {self.id} - {self.hikvision_id} - {self.event_time}"


class Employee(models.Model):
    """
    Модель для хранения информации о сотрудниках и их подразделениях.
    """
    hikvision_id = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="ID от Hikvision",
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Имя сотрудника",
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name="Подразделение",
    )
    # Сохраняем старое поле для обратной совместимости (deprecated)
    department_old = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Подразделение (старое поле)",
        help_text="Устаревшее поле, используйте department",
    )
    card_no = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Номер карты",
    )
    position = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Должность",
        help_text="Должность сотрудника",
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["hikvision_id"]
        indexes = [
            models.Index(fields=["hikvision_id"]),
            models.Index(fields=["department"]),
            models.Index(fields=["department_old"]),
        ]
    
    def clean_id(self, id_str):
        """Удаляет ведущие нули из ID."""
        if not id_str:
            return id_str
        s = str(id_str).strip()
        if s.replace('0', '') == '':
            return "0"
        return s.lstrip('0') or "0"
    
    def save(self, *args, **kwargs):
        """Убирает ведущие нули из hikvision_id и нормализует имя перед сохранением."""
        if self.hikvision_id:
            self.hikvision_id = self.clean_id(self.hikvision_id)
        
        # Нормализуем имя: убираем переносы строк и лишние пробелы
        if self.name:
            self.name = self.name.replace('\n', ' ').replace('\r', ' ').strip()
            self.name = re.sub(r'\s+', ' ', self.name)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        dept_name = self.department.name if self.department else (self.department_old or 'Без подразделения')
        return f"{self.name} ({self.hikvision_id}) - {dept_name}"


class EntryExit(models.Model):
    """
    Модель для хранения записей входов и выходов.
    """
    hikvision_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="ID от Hikvision",
        db_index=True,
    )
    entry_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время входа",
        db_index=True,
    )
    exit_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время выхода",
        db_index=True,
    )
    device_name_entry = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Устройство входа",
    )
    device_name_exit = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Устройство выхода",
    )
    work_duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Продолжительность работы (секунды)",
    )
    
    # Флаги для отслеживания учета статистики
    late_counted = models.BooleanField(
        default=False,
        verbose_name="Опоздание учтено",
        help_text="Флаг, указывающий, было ли опоздание учтено в статистике",
        db_index=True,
    )
    early_leave_counted = models.BooleanField(
        default=False,
        verbose_name="Ранний уход учтен",
        help_text="Флаг, указывающий, был ли ранний уход учтен в статистике",
        db_index=True,
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "Запись входа/выхода"
        verbose_name_plural = "Записи входов/выходов"
        ordering = ["-entry_time"]
        indexes = [
            models.Index(fields=["hikvision_id", "entry_time"]),
            models.Index(fields=["entry_time"]),
            models.Index(fields=["exit_time"]),
        ]
    
    def __str__(self):
        return f"EntryExit {self.id} - {self.hikvision_id} - {self.entry_time}"
    
    @property
    def work_duration_formatted(self):
        """Возвращает продолжительность работы в формате 'Xч Ym'."""
        if self.work_duration_seconds:
            hours = self.work_duration_seconds // 3600
            minutes = (self.work_duration_seconds % 3600) // 60
            return f"{hours}ч {minutes}м"
        return "Не завершено"


class WorkSchedule(models.Model):
    """
    Модель для хранения графиков работы сотрудников.
    Поддерживает обычные, плавающие и круглосуточные графики.
    """
    SCHEDULE_TYPE_CHOICES = [
        ('regular', 'Обычный график'),
        ('floating', 'Плавающий график'),
        ('round_the_clock', 'Круглосуточный'),
    ]
    
    DAY_OF_WEEK_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='work_schedules',
        verbose_name="Сотрудник",
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        default='regular',
        verbose_name="Тип графика",
        db_index=True,
    )
    
    # Для обычного графика: дни недели и время
    days_of_week = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Дни недели",
        help_text="Список дней недели (0=Понедельник, 6=Воскресенье)",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Время начала работы",
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Время окончания работы",
    )
    
    # Для плавающего графика: чередование смен (JSON)
    # Формат: [{"day": 0, "start": "08:00", "end": "17:00"}, {"day": 1, "start": "20:00", "end": "05:00"}]
    floating_shifts = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Плавающие смены",
        help_text="Список смен для плавающего графика",
    )
    
    # Описание графика (для удобства)
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Описание графика",
        help_text="Текстовое описание графика (например: 'Пн-Пт 08:00-17:00' или 'Чередование день/ночь')",
    )
    
    # Допустимые отклонения от графика (в минутах)
    allowed_late_minutes = models.IntegerField(
        default=0,
        verbose_name="Допустимое опоздание (минуты)",
        help_text="На сколько минут можно опоздать (например: 15)",
    )
    allowed_early_leave_minutes = models.IntegerField(
        default=0,
        verbose_name="Допустимый ранний уход (минуты)",
        help_text="На сколько минут можно уйти раньше (например: 15)",
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "График работы"
        verbose_name_plural = "Графики работы"
        ordering = ["employee", "schedule_type"]
        indexes = [
            models.Index(fields=["employee", "schedule_type"]),
            models.Index(fields=["schedule_type"]),
        ]
    
    def __str__(self):
        if self.schedule_type == 'round_the_clock':
            return f"{self.employee.name} - Круглосуточный"
        elif self.schedule_type == 'floating':
            return f"{self.employee.name} - Плавающий график"
        elif self.start_time and self.end_time:
            days_str = ", ".join([self.DAY_OF_WEEK_CHOICES[d][1] for d in self.days_of_week])
            return f"{self.employee.name} - {days_str} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        return f"{self.employee.name} - {self.get_schedule_type_display()}"
    
    def get_schedule_display(self):
        """Возвращает читаемое описание графика."""
        if self.schedule_type == 'round_the_clock':
            return "Круглосуточно"
        elif self.schedule_type == 'floating':
            if self.description:
                return self.description
            return "Плавающий график"
        elif self.start_time and self.end_time:
            # Возвращаем только время без дней
            return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        return self.description or "Не указано"


class EmployeeAttendanceStats(models.Model):
    """
    Модель для хранения статистики посещаемости сотрудников.
    Считает опоздания и ранние уходы.
    """
    employee = models.OneToOneField(
        'Employee',
        on_delete=models.CASCADE,
        related_name='attendance_stats',
        verbose_name="Сотрудник",
        db_index=True,
    )
    late_count = models.IntegerField(
        default=0,
        verbose_name="Количество опозданий",
        help_text="Общее количество опозданий сотрудника",
    )
    early_leave_count = models.IntegerField(
        default=0,
        verbose_name="Количество ранних уходов",
        help_text="Общее количество ранних уходов и недоработок",
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи",
    )
    
    class Meta:
        verbose_name = "Статистика посещаемости"
        verbose_name_plural = "Статистика посещаемости"
        ordering = ["-late_count", "-early_leave_count"]
        indexes = [
            models.Index(fields=["employee"]),
        ]
    
    def increment_late(self):
        """Увеличивает счетчик опозданий на 1."""
        self.late_count += 1
        self.save(update_fields=['late_count', 'updated_at'])
    
    def increment_early_leave(self):
        """Увеличивает счетчик ранних уходов на 1."""
        self.early_leave_count += 1
        self.save(update_fields=['early_leave_count', 'updated_at'])
    
    def __str__(self):
        return f"{self.employee.name} - Опозданий: {self.late_count}, Ранних уходов: {self.early_leave_count}"