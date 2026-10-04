from django.db import migrations, models


def convert_position_fk_to_title(apps, schema_editor):
    Employee = apps.get_model('core', 'Employee')
    Position = apps.get_model('core', 'Position')
    for emp in Employee.objects.all():
        if emp.position_id:
            try:
                pos = Position.objects.get(pk=emp.position_id)
                emp.position = pos.title
            except Position.DoesNotExist:
                emp.position = None
        else:
            emp.position = None
        emp.save(update_fields=['position'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_employee_role'),
    ]

    operations = [
        migrations.RunPython(convert_position_fk_to_title, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='position',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
