from datetime import timedelta, datetime
import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse

from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage, WhatsappTemplate
from django.db.models import Sum
from django.conf import settings
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
# Create your models here.

BOOKING_CHOICES = (
                    ('a', 'In Person'),
                    ('b', 'Phone'),
                )
booking_choices_dict = {}
for tuple in BOOKING_CHOICES:
    booking_choices_dict[tuple[0]] = tuple[1]

# class AdCampaign(models.Model):
#     name = models.TextField(null=True, blank=True)

class Campaign(PolymorphicModel):
    name = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_cost = models.FloatField(default=100)
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)
    webhook_created = models.BooleanField(default=False)
    webhook_id = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    def get_active_leads_qs(self):
        return self.campaignlead_set.filter(complete=False)
    def is_manual(self):
        return False
@receiver(models.signals.post_save, sender=Campaign)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        instance.guid = str(uuid.uuid4())[:16]
        instance.save()

class ManualCampaign(Campaign):
    pass
    @property
    def is_manual(self):
        return True


class Campaignlead(models.Model):
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    whatsapp_number = models.TextField(null=True, blank=True)
    # country_code = models.TextField(null=True, blank=True)
    campaign = models.ForeignKey("campaign_leads.Campaign", on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    arrived = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    active_campaign_contact_id = models.TextField(null=True, blank=True)
    active_campaign_form_id = models.TextField(null=True, blank=True)
    possible_duplicate = models.BooleanField(default=False)
    
    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    @property
    def last_whatsapp(self):
        whatsapps = self.call_set.all()
        if whatsapps:
            return whatsapps.first()
        return None
    
    @property
    def time_until_next_whatsapp(self):
        last_whatsapp = self.last_whatsapp
        print(last_whatsapp)
        if last_whatsapp:
            return last_whatsapp.datetime.replace(hour=9).replace(minute=30).replace(second=0) + timedelta(days=1)
        return "Never"  

    def send_template_whatsapp_message(self, send_order, communication_method = 'a'):
        if communication_method == 'whatsapp':
            template = WhatsappTemplate.objects.get(send_order = send_order, site=self.campaign.site)
            message = f"{template.rendered(self)}" 
            return self.campaign.site.send_whatsapp_message(customer_number=self.whatsapp_number, lead=self, message=message, template_used=template)
        return HttpResponse("No Communication method specified", status=500)

@receiver(models.signals.post_save, sender=Campaignlead)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created and not instance.complete:
        instance.send_template_whatsapp_message(1, communication_method='a')
        pass
        
class Call(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    error_json = models.JSONField(default=dict)
    class Meta:
        ordering = ['-datetime']

class Booking(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE)
    type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        ordering = ['-datetime']

class Note(models.Model):
    text = models.TextField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE, null=True, blank=True)
    call = models.ForeignKey('campaign_leads.Call', on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    #This referes to the date it was created unless it's attached to a call/booking, then it's set to the related datetime
    datetime = models.DateTimeField(null=True, blank=True) 
    class Meta:
        ordering = ['-datetime']

# try:
#     template, created = WhatsappTemplate.objects.get_or_create(pk=1)
#     template.name = "Immediate Lead Followup"
#     template.save()

#     template, created = WhatsappTemplate.objects.get_or_create(pk=2)
#     template.name = "Second Lead Followup"
#     template.save()

#     template, created = WhatsappTemplate.objects.get_or_create(pk=3)
#     template.name = "Third Lead Followup"
#     template.save()
# except:
#     pass