from django.db import models
from django.forms import BooleanField

# Create your models here.
class TwilioRawWebhook(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    REQUEST_TYPE_CHOICES = (
                        ('a', 'POST'),
                        ('b', 'GET'),
                    )
    TWILIO_WEBHOOK_TYPE_CHOICES = (
                        ('a', 'Message'),
                        ('b', 'Status'),
                    )
    json_data = models.JSONField(null=True, blank=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)
    twilio_webhook_type = models.CharField(choices=TWILIO_WEBHOOK_TYPE_CHOICES, default='a', max_length=1)
class TwilioMessage(models.Model):    
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    INBOUND_OUTBOUND_CHOICES = (
                        ('a', 'Inbound'),
                        ('b', 'Outbound'),
                    )
    TYPE_CHOICES = (
                        ('whatsapp', 'WhatsApp'),
                        ('sms', 'SMS'),
                    )
    raw_webhook = models.ForeignKey("twilio.TwilioRawWebhook", null=True, blank=True, on_delete=models.SET_NULL)
    inbound = models.CharField(choices=INBOUND_OUTBOUND_CHOICES, default='a', max_length=1)
    Type = models.CharField(choices=TYPE_CHOICES, default='whatsapp', max_length=15)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)

    Body = models.TextField(null=True, blank=True)
    ProfileName = models.TextField(null=True, blank=True)
    From = models.CharField(max_length=15, null=True, blank=True)
    To = models.CharField(max_length=15, null=True, blank=True)
    SmsSid = models.CharField(max_length=50, null=True, blank=True)
    MessageSid = models.CharField(max_length=50, null=True, blank=True)
    SmsMessageSid = models.CharField(max_length=50, null=True, blank=True)
    AccountSid = models.CharField(max_length=50, null=True, blank=True)
    ApiVersion = models.CharField(max_length=50, null=True, blank=True)
    WaId = models.CharField(max_length=50, null=True, blank=True)
    NumMedia = models.CharField(max_length=3, null=True, blank=True)
    NumSegments = models.CharField(max_length=3, null=True, blank=True)
    ReferralNumMedia = models.CharField(max_length=3, null=True, blank=True)    
    SmsStatus = models.CharField(max_length=20, null=True, blank=True)
