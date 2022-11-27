from django.contrib import admin

from campaign_leads.models import Campaignlead, Campaign

# Register your models here.

class CampaignleadAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','sold','archived',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
    search_fields = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','sold','archived',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
admin.site.register(Campaignlead, CampaignleadAdmin)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name','created','product_cost','guid',
    'webhook_created','webhook_id','site','company','first_send_template',
    'second_send_template','third_send_template',
    'whatsapp_business_account']
admin.site.register(Campaign, CampaignAdmin)


    