# Generated by Django 3.2.15 on 2023-04-17 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0013_auto_20221119_2337'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsapptemplate',
            name='lead_only',
            field=models.BooleanField(default=False),
        ),
    ]
