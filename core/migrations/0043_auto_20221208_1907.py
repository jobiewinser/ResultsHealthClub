# Generated by Django 3.2.15 on 2022-12-08 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_auto_20221208_1813'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyprofilepermissions',
            name='permissions_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='siteprofilepermissions',
            name='permissions_count',
            field=models.IntegerField(default=0),
        ),
    ]