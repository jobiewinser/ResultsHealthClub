from django.db import models
from django.contrib.auth.models import User


GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )

class WhatsAppWebhook(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    REQUEST_TYPE_CHOICES = (
                        ('a', 'POST'),
                        ('b', 'GET'),
                    )
    json_data = models.JSONField(null=True, blank=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)

class WhatsAppMessage(models.Model):
    wamid = models.TextField(null=True, blank=True)   
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhook", null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey("campaign_leads.Campaignlead", null=True, blank=True, on_delete=models.SET_NULL)
    inbound = models.BooleanField(default=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    conversationid = models.TextField(null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    system_user_number = models.CharField(max_length=50, null=True, blank=True)
    customer_number = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    template = models.ForeignKey("campaign_leads.WhatsappTemplate", on_delete=models.SET_NULL, null=True, blank=True)
    # company = models.ManyToManyField("core.Company")
    class Meta:
        ordering = ['-datetime']
    
class WhatsAppMessageStatus(models.Model):
    whatsapp_message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhook", null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ['-datetime']