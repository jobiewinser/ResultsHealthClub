import uuid
from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User


GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )


# Extending User Model Using a One-To-One Link
class WhatsAppMessage(models.Model):
    wamid = models.TextField(null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    phone_to = models.TextField(null=True, blank=True) 
    phone_from = models.TextField(null=True, blank=True) 