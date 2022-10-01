import uuid
from django.db import models
from active_campaign.api import ActiveCampaign
from django.dispatch import receiver
from django.conf import settings

from core.models import Site
class ActiveCampaignList(models.Model):
    active_campaign_id = models.TextField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)   
    # active_campaign_created = models.DateTimeField(null=True, blank=True)
    # active_campaign_updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)
    webhook_created = models.BooleanField(default=False)
    webhook_id = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    manual = models.BooleanField(default=False)
    company = models.ManyToManyField("core.Company")
        
    def create_webhook(self):
        if self.name and self.guid and not self.webhook_id and not settings.DEBUG and not 'manually' in self.name.lower():
            response = ActiveCampaign().create_webhook(str(self.name), str(self.guid), str(self.active_campaign_id))
            if response.status_code in [200, 201]:
                self.webhook_created = True
                self.webhook_id = response.json().get('webhook').get('id')
                self.save()
    def get_active_leads_qs(self):
        return self.campaignlead_set.filter(complete=False)
@receiver(models.signals.post_save, sender=ActiveCampaignList)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        instance.guid = str(uuid.uuid4())[:16]
        instance.save()
        instance.create_webhook()

class CampaignWebhook(models.Model):
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)
    company = models.ManyToManyField("core.Company")


