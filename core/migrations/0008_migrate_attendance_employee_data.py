from django.db import migrations, models


def convert_attendance_employee_fk_to_name(apps, schema_editor):
    Attendance = apps.get_model('core', 'Attendance')
    Employee = apps.get_model('core', 'Employee')
    for att in Attendance.objects.all():
        if att.employee_id:
            try:
                emp = Employee.objects.get(pk=att.employee_id)
                att.employee = emp.full_name
            except Employee.DoesNotExist:
                att.employee = None
        else:
            att.employee = None
        att.save(update_fields=['employee'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_migrate_supervisor_data'),
    ]

    operations = [
        migrations.RunPython(convert_attendance_employee_fk_to_name, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='attendance',
            name='employee',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
