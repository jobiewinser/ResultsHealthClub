from django.db import models


GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )

class WhatsAppMessage(models.Model):
    wamid = models.TextField(null=True, blank=True)   
    conversationid = models.TextField(null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    phone_to = models.TextField(null=True, blank=True) 
    phone_from = models.TextField(null=True, blank=True)
    communication = models.OneToOneField("academy_leads.Communication", on_delete=models.SET_NULL, null=True, blank=True) 
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta:
        ordering = ['-datetime']
    
class WhatsAppMessageStatus(models.Model):
    whats_app_message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta:
        ordering = ['-datetime']