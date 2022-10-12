from django.db import models

# Create your models here.

class CalendlyWebhookRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    REQUEST_TYPE_CHOICES = (
                        ('a', 'POST'),
                        ('b', 'GET'),
                    )
    json_data = models.JSONField(null=True, blank=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)