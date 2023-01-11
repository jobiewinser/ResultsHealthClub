from django.urls import path
import active_campaign.views as activecampaignviews
urlpatterns = [
    path('active-campaign-webhooks/<str:guid>/', activecampaignviews.Webhooks.as_view(), name='active-campaign-webhooks' ),
    path('set-campaign-site/<int:campaign_pk>/', activecampaignviews.set_campaign_site, name='set-campaign-site'),
    path('set-whatsapp-template-sending-status/', activecampaignviews.set_whatsapp_template_sending_status, name='set-whatsapp-template-sending-status'),
    
    path('set-active-campaign-lead-status/', activecampaignviews.set_active_campaign_leads_status, name='set-active-campaign-lead-status'),
    path('import-active-campaign-leads/', activecampaignviews.import_active_campaign_leads, name='import-active-campaign-leads'),
    
]