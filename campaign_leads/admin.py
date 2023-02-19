from django.contrib import admin

from campaign_leads.models import Campaignlead, Booking, Call

# Register your models here.

class CampaignleadAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','archived',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
    search_fields = ['first_name','last_name','email','whatsapp_number',
    'campaign','created','arrived','archived',
    'active_campaign_contact_id','active_campaign_form_id',
    'possible_duplicate','last_dragged']
admin.site.register(Campaignlead, CampaignleadAdmin)

class BookingAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'lead', 'user', 'calendly_event_uri', 'archived', 'created']
admin.site.register(Booking, BookingAdmin)

class CallAdmin(admin.ModelAdmin):
    list_display = ['created', 'datetime', 'lead', 'user', 'archived']
    search_fields = ['created', 'datetime', 'archived']    
admin.site.register(Call, CallAdmin)