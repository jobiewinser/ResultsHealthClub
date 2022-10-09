from django.contrib import admin

from active_campaign.models import ActiveCampaignList

# class ActiveCampaignListAdmin(admin.ModelAdmin):
#     list_display = ['pk', 'active_campaign_id', 'name', 'guid', 'webhook_created', 'webhook_id']
#     search_fields = ['pk', 'active_campaign_id', 'name', 'guid', 'webhook_created', 'webhook_id']
# admin.site.register(ActiveCampaignList, ActiveCampaignListAdmin)