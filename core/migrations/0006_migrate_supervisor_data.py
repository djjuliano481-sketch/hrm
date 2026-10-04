from django.db import migrations, models


def convert_supervisor_fk_to_name(apps, schema_editor):
    Employee = apps.get_model('core', 'Employee')
    for emp in Employee.objects.all():
        if emp.immediate_supervisor_id:
            try:
                sup = Employee.objects.get(pk=emp.immediate_supervisor_id)
                emp.immediate_supervisor = sup.full_name
            except Employee.DoesNotExist:
                emp.immediate_supervisor = None
        else:
            emp.immediate_supervisor = None
        emp.save(update_fields=['immediate_supervisor'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_migrate_position_data'),
    ]

    operations = [
        migrations.RunPython(convert_supervisor_fk_to_name, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='immediate_supervisor',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
