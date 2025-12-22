"""
Создание отделов из старого поля department_old сотрудников.
"""
import os
import sys
import django

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from camera_events.models import Employee, Department
from collections import Counter

def main():
    print("=" * 80)
    print("СОЗДАНИЕ ОТДЕЛОВ ИЗ department_old")
    print("=" * 80)
    print()
    
    # Получаем все уникальные отделы из department_old
    employees = Employee.objects.exclude(department_old__isnull=True).exclude(department_old='')
    departments_old = [emp.department_old for emp in employees if emp.department_old]
    unique_departments = set(departments_old)
    
    print(f"Найдено уникальных отделов: {len(unique_departments)}")
    print()
    
    # Создаем отделы
    created_count = 0
    existing_count = 0
    dept_mapping = {}
    
    for dept_name in sorted(unique_departments):
        # Проверяем, существует ли уже такой отдел
        dept, created = Department.objects.get_or_create(name=dept_name)
        dept_mapping[dept_name] = dept
        
        if created:
            created_count += 1
            print(f"✓ Создан отдел: {dept_name}")
        else:
            existing_count += 1
            print(f"→ Отдел уже существует: {dept_name}")
    
    print()
    print(f"Создано новых отделов: {created_count}")
    print(f"Уже существовало отделов: {existing_count}")
    print()
    
    # Привязываем сотрудников к отделам
    print("Привязка сотрудников к отделам...")
    updated_count = 0
    
    for emp in employees:
        if emp.department_old and emp.department_old in dept_mapping:
            dept = dept_mapping[emp.department_old]
            if emp.department != dept:
                emp.department = dept
                emp.save(update_fields=['department'])
                updated_count += 1
    
    print(f"✓ Привязано сотрудников к отделам: {updated_count}")
    print()
    
    # Статистика
    print("=" * 80)
    print("СТАТИСТИКА:")
    print("-" * 80)
    print(f"Всего отделов в базе: {Department.objects.count()}")
    print(f"Сотрудников с отделами: {Employee.objects.exclude(department=None).count()}")
    print(f"Сотрудников без отделов: {Employee.objects.filter(department=None).count()}")
    print()
    
    # Показываем топ-10 отделов по количеству сотрудников
    print("ТОП-10 ОТДЕЛОВ ПО КОЛИЧЕСТВУ СОТРУДНИКОВ:")
    print("-" * 80)
    dept_stats = []
    for dept in Department.objects.all():
        emp_count = dept.employees.count()
        dept_stats.append((dept.name, emp_count))
    
    dept_stats.sort(key=lambda x: x[1], reverse=True)
    for dept_name, emp_count in dept_stats[:10]:
        print(f"  {dept_name}: {emp_count} сотрудников")
    
    print()
    print("=" * 80)
    print("ГОТОВО!")
    print("=" * 80)

if __name__ == '__main__':
    main()




