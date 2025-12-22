# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def copy_department_to_old(apps, schema_editor):
    """Копирует данные из department в department_old перед изменением типа поля."""
    Employee = apps.get_model('camera_events', 'Employee')
    for employee in Employee.objects.all():
        if employee.department:
            employee.department_old = employee.department
            employee.save(update_fields=['department_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('camera_events', '0004_employee'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Название подразделения')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='camera_events.department', verbose_name='Родительское подразделение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления записи')),
            ],
            options={
                'verbose_name': 'Подразделение',
                'verbose_name_plural': 'Подразделения',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['name'], name='camera_even_name_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['parent'], name='camera_even_parent_idx'),
        ),
        migrations.AddField(
            model_name='employee',
            name='department_old',
            field=models.CharField(blank=True, help_text='Устаревшее поле, используйте department', max_length=255, null=True, verbose_name='Подразделение (старое поле)'),
        ),
        migrations.RunPython(copy_department_to_old, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name='employee',
            name='camera_even_departm_bc606e_idx',
        ),
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='camera_events.department', verbose_name='Подразделение'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['department'], name='camera_even_departm_new_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['department_old'], name='camera_even_departm_old_idx'),
        ),
    ]

