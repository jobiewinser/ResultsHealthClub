# Generated by Django 3.2.15 on 2022-11-19 13:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20221119_1303'),
        ('messaging', '0010_auto_20221106_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.contact'),
        ),
    ]