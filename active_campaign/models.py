from django.db import models

class Campaign(models.Model):
    active_campaign_id = models.TextField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)   
    status = models.TextField(null=True, blank=True)   
    uniqueopens = models.IntegerField(default=0)
    opens = models.IntegerField(default=0)
    active_campaign_created = models.DateTimeField(null=True, blank=True)
    active_campaign_updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    json_data = models.JSONField(default=dict)

class CampaignWebhook(models.Model):
    json_data = models.JSONField(default=dict)