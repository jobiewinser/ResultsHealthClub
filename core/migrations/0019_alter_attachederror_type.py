# Generated by Django 3.2.15 on 2022-11-13 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_site_whatsapp_app_secret_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachederror',
            name='type',
            field=models.CharField(choices=[('0101', 'You can only edit an active template once every 24 hours'), ('0102', 'The system can not send Whatsapp Templates without a template name'), ('0103', 'The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)'), ('1104', 'Message failed to send because more than 24 hours have passed since the customer last replied to this number. You can still send a template message at 24 hour intervals instead'), ('1105', 'Message failed to send because the Whatsapp account is not yet registered (contact Winser Systems)'), ('1201', "Whatsapp Template not found Whatsapp's system"), ('1202', "There is no Whatsapp Business linked to this Lead's assosciated Site"), ('1203', "There is no 1st Whatsapp Template linked to this Lead's Campaign"), ('1204', "There is no 2nd Whatsapp Template linked to this Lead's Campaign"), ('1205', "There is no 3rd Whatsapp Template linked to this Lead's Campaign")], default='c', max_length=5),
        ),
    ]