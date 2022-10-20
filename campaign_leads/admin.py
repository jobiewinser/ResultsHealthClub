from django.contrib import admin

from campaign_leads.models import Campaignlead

# Register your models here.

class CampaignleadAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','sold','complete',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
    search_fields = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','sold','complete',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
admin.site.register(Campaignlead, CampaignleadAdmin)


    