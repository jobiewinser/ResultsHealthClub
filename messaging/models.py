from django.db import models
from django.contrib.auth.models import User
from polymorphic.models import PolymorphicModel

# Create your models here.

class Message(PolymorphicModel):
    lead = models.ForeignKey("campaign_leads.Campaignlead", null=True, blank=True, on_delete=models.SET_NULL)
    inbound = models.BooleanField(default=True)
    read = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    customer_number = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    template = models.ForeignKey("whatsapp.WhatsappTemplate", on_delete=models.SET_NULL, null=True, blank=True)
    # company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['-datetime']

class MessageImage(PolymorphicModel):  
    image = models.ImageField(upload_to="secure/message_images", null=True, blank=True)    
    thumbnail = models.TextField(null=True, blank=True)
