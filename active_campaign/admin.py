from django.contrib import admin

from active_campaign.models import ActiveCampaign

class ActiveCampaignAdmin(admin.ModelAdmin):
    list_display = ['pk', 'active_campaign_id', 'name', 'guid', 'webhook_created', 'webhook_id']
    search_fields = ['pk', 'active_campaign_id', 'name', 'guid', 'webhook_created', 'webhook_id']
admin.site.register(ActiveCampaign, ActiveCampaignAdmin)