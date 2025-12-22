#!/usr/bin/env python
"""
Скрипт для экспорта сотрудников из базы данных в Excel файл.
Использование: python export_employees.py <путь_к_excel_файлу> [подразделение_id]
"""
import os
import sys
import django

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from camera_events.import_employees import export_employees_to_excel
from camera_events.models import Department


def main():
    if len(sys.argv) < 2:
        print("Использование: python export_employees.py <путь_к_excel_файлу> [подразделение_id]")
        print("\nПримеры:")
        print("  python export_employees.py employees_export.xlsx")
        print("  python export_employees.py employees_export.xlsx 1  # экспорт только для подразделения с ID=1")
        print("\nФормат выходного Excel файла:")
        print("  - Employee ID: ID сотрудника")
        print("  - Имя: Имя сотрудника")
        print("  - Подразделение: Название подразделения (с иерархией через ' > ')")
        print("  - Должность: Должность сотрудника")
        print("  - Тип графика: Обычный график, Плавающий график, Круглосуточный")
        print("  - График: Описание графика или время работы")
        print("  - Допустимое опоздание: Количество минут")
        print("  - Допустимый ранний уход: Количество минут")
        print("\nПримечание: Экспортируются также сотрудники из событий камер,")
        print("которые еще не добавлены в таблицу Employee (без подразделения и графика)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    department_filter = None
    
    # Проверяем, указано ли подразделение для фильтрации
    if len(sys.argv) >= 3:
        try:
            department_id = int(sys.argv[2])
            try:
                department_filter = Department.objects.get(id=department_id)
                print(f"Экспорт будет выполнен только для подразделения: {department_filter.get_full_path()}")
            except Department.DoesNotExist:
                print(f"Ошибка: Подразделение с ID={department_id} не найдено")
                sys.exit(1)
        except ValueError:
            print(f"Ошибка: '{sys.argv[2]}' не является валидным ID подразделения")
            sys.exit(1)
    
    try:
        print(f"Начинаем экспорт в файл: {file_path}")
        results = export_employees_to_excel(file_path, department_filter=department_filter)
        
        print(f"\n{'='*50}")
        print(f"Результаты экспорта:")
        print(f"{'='*50}")
        print(f"Всего экспортировано сотрудников: {results['success']}")
        print(f"  - Из таблицы Employee: {results['from_employee_table']}")
        print(f"  - Из событий камер (новые): {results['from_camera_events']}")
        
        if results['errors']:
            print(f"\nОшибки ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  ⚠ {error}")
        else:
            print("\n✓ Экспорт выполнен успешно!")
            print(f"✓ Файл сохранен: {file_path}")
        
        print(f"{'='*50}\n")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка при экспорте: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

