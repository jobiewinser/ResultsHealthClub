# Generated by Django 3.2.15 on 2022-12-08 15:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_siteprofilepermissions_edit_user_permissions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siteprofilepermissions',
            old_name='toggle_toggle_active_campaign',
            new_name='toggle_active_campaign',
        ),
    ]