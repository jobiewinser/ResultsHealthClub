# Generated by Django 3.2.15 on 2022-12-06 03:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_siteusersonline'),
        ('campaign_leads', '0017_campaignlead_product_cost'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaigncategory',
            name='company',
        ),
        migrations.AddField(
            model_name='campaigncategory',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.site'),
        ),
    ]
