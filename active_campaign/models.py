import uuid
from django.db import models
from active_campaign.api import ActiveCampaign
from django.dispatch import receiver
from django.conf import settings
from campaign_leads.models import Campaign

from core.models import Site
class ActiveCampaignWebhook(models.Model):
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)

class ActiveCampaignList(Campaign):
    pass
    active_campaign_id = models.TextField(null=True, blank=True)
    def create_webhook(self):
        if self.name and self.guid and not self.webhook_id and not settings.DEBUG and not 'manually' in self.name.lower():
            response = ActiveCampaign(self.company.active_campaign_api_key, self.company.active_campaign_url).create_webhook(str(self.name), str(self.guid), str(self.active_campaign_id))
            if response.status_code in [200, 201]:
                self.webhook_created = True
                self.webhook_id = response.json().get('webhook').get('id')
                self.save()

@receiver(models.signals.post_save, sender=ActiveCampaignList)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        instance.guid = str(uuid.uuid4())[:16]
        instance.save()
        instance.create_webhook()



