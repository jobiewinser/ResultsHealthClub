# Generated by Django 3.2.15 on 2022-12-02 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20221202_0001'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='site',
            name='whatsapp_app_secret_key',
        ),
        migrations.AddField(
            model_name='company',
            name='whatsapp_app_secret_key',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='active_campaign_leads_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='site',
            name='whatsapp_template_sending_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
