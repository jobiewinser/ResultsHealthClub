# Generated by Django 3.2.15 on 2022-12-05 23:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_leads', '0016_auto_20221204_2012'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignlead',
            name='product_cost',
            field=models.FloatField(blank=True, null=True),
        ),
    ]