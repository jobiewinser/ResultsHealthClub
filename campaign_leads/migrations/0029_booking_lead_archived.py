# Generated by Django 3.2.15 on 2023-03-23 16:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_leads', '0028_campaignlead_active_sale'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='lead_archived',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='booking_archived', to='campaign_leads.campaignlead'),
        ),
    ]
