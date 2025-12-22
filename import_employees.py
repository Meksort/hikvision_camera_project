#!/usr/bin/env python
"""
Скрипт для импорта сотрудников из Excel файла.
Использование: python import_employees.py <путь_к_excel_файлу>
"""
import os
import sys
import django

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from camera_events.import_employees import import_employees_from_excel


def main():
    if len(sys.argv) < 2:
        print("Использование: python import_employees.py <путь_к_excel_файлу>")
        print("\nПример:")
        print("  python import_employees.py employee_import_template.xlsx")
        print("\nФормат Excel файла:")
        print("  - Employee ID: обязательное поле")
        print("  - Имя: обязательное поле")
        print("  - Подразделение: опционально (поддерживается иерархия через ' > ')")
        print("  - Должность: опционально")
        print("  - Тип графика: 'Обычный график', 'Плавающий график', 'Круглосуточный'")
        print("  - График: описание или время в формате 'HH:MM-HH:MM'")
        print("  - Допустимое опоздание: количество минут (число)")
        print("  - Допустимый ранний уход: количество минут (число)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл не найден: {file_path}")
        sys.exit(1)
    
    try:
        print(f"Начинаем импорт из файла: {file_path}")
        results = import_employees_from_excel(file_path, update_existing=True)
        
        print(f"\n{'='*50}")
        print(f"Результаты импорта:")
        print(f"{'='*50}")
        print(f"Успешно обработано: {results['success']}")
        print(f"  - Создано новых: {results['created']}")
        print(f"  - Обновлено: {results['updated']}")
        
        if results['errors']:
            print(f"\nОшибки ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  ⚠ {error}")
        else:
            print("\n✓ Ошибок не обнаружено!")
        
        print(f"{'='*50}\n")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка при импорте: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()











