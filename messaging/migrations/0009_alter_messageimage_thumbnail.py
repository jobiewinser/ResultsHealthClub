# Generated by Django 3.2.15 on 2022-10-29 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0008_auto_20221028_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageimage',
            name='thumbnail',
            field=models.TextField(blank=True, null=True),
        ),
    ]