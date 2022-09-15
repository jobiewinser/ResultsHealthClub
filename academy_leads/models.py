import datetime
import os
from django.db import models
from django.contrib.auth.models import User

from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage

from django.dispatch import receiver
# Create your models here.


COMMUNICATION_CHOICES = (
                    ('a', 'Phone'),
                    ('b', 'Whatsapp'),
                    ('c', 'Email'),
                    ('d', 'Text')
                )
communication_choices_dict = {}
for tuple in COMMUNICATION_CHOICES:
    communication_choices_dict[tuple[0]] = tuple[1]
BOOKING_CHOICES = (
                    ('a', 'In Person'),
                    ('b', 'Phone'),
                )
booking_choices_dict = {}
for tuple in BOOKING_CHOICES:
    booking_choices_dict[tuple[0]] = tuple[1]

# class AdCampaign(models.Model):
#     name = models.TextField(null=True, blank=True)

class AcademyLead(models.Model):
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    country_code = models.TextField(null=True, blank=True)
    campaign = models.ForeignKey("active_campaign.Campaign", on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    arrived = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)

    def next_whatsapp_communication(self):
        last_whatsapp_communication = self.communication_set.filter(type='b')
    def send_whatsapp_message(self, template, user=None):
        whatsapp = Whatsapp()
        response = whatsapp.send_message(f"{self.country_code}{self.phone}", f"{template.rendered(self)}")
        print("send_whatsapp_message response", response)
        reponse_messages = response.get('messages',[])
        if reponse_messages:
            for response_message in reponse_messages:
                communication = Communication.objects.get_or_create(    
                    datetime = datetime.datetime.now(),
                    lead = self,
                    type = 'b',
                    automatic = True,
                    staff_user = user
                )[0]
                print("response_message MESSAGE", str(response_message))
                WhatsAppMessage.objects.get_or_create(
                    wamid=response_message.get('id'),
                    message=message,
                    communication=communication,
                    phone_from=os.getenv("WHATSAPP_PRIMARY_BUSINESS_PHONE_NUMBER"),
                    phone_to=f"{self.country_code}{self.phone}"
                    )
        else:
            communication = Communication.objects.get_or_create(    
                datetime = datetime.datetime.now(),
                lead = self,
                type = 'b',
                automatic = True,
                staff_user = user,
                successful = False,
                error_json = response
            )[0]

@receiver(models.signals.post_save, sender=AcademyLead)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        instance.send_whatsapp_message(WhatsappTemplate.objects.get(pk=1), user=None)
        
class Communication(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(choices=COMMUNICATION_CHOICES, max_length=2, null=False, blank=False)
    successful = models.BooleanField(default=None, null=True, blank=True)
    automatic = models.BooleanField(default=False)
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    error_json = models.JSONField(default=dict)
    class Meta:
        ordering = ['-datetime']

class Booking(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE)
    type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        ordering = ['-created']

class Note(models.Model):
    text = models.TextField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE, null=True, blank=True)
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    #This referes to the date it was created unless it's attached to a communication/booking, then it's set to the related datetime
    datetime = models.DateTimeField(null=True, blank=True) 


class CustomWhatsappTemplateQuerySet(models.QuerySet):
    def delete(self):
        pass
class WhatsappTemplateManager(models.Manager):
    def get_queryset(self):
        return CustomWhatsappTemplateQuerySet(self.model, using=self._db)

class WhatsappTemplate(models.Model):
    name = models.TextField(null=False, blank=False)
    text = models.TextField(null=False, blank=False)
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    edited = models.DateTimeField(null=True, blank=True) 
    created = models.DateTimeField(auto_now_add=True)

    objects = WhatsappTemplateManager()
    def delete(self):
        self.save()

    def rendered_demo(self):
        return self.text.replace('{first_name}', 'Jobie').replace('{last_name}', 'Winser')

    def rendered(self, lead):
        return self.text.replace('{first_name}', lead.first_name).replace('{last_name}', lead.last_name)
try:
    template, created = WhatsappTemplate.objects.get_or_create(pk=1)
    template.name = "Immediate Lead Followup"
    template.save()

    template, created = WhatsappTemplate.objects.get_or_create(pk=2)
    template.name = "Second Lead Followup"
    template.save()

    template, created = WhatsappTemplate.objects.get_or_create(pk=3)
    template.name = "Third Lead Followup"
    template.save()
except:
    pass