"""jobiewebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
import campaign_leads.views as campaignleadsviews
import campaign_leads.htmx as campaignleadshtmx
urlpatterns = [
    path('home/', campaignleadsviews.CampaignLeadsHomeView.as_view(), name='campaign-leads-home'),
    


    path('booking-and-calender/', campaignleadsviews.CampaignBookingsOverviewView.as_view(), name='campaign-booking-overview'),
    path('leads-and-calls/', campaignleadsviews.CampaignleadsOverviewView.as_view(), name='campaign-leads-overview'),    




    path('configuration/whatsapp-templates/', campaignleadsviews.WhatsappTemplatesView.as_view(), name='whatsapp-templates'),
    path('configuration/lead-configuration/', campaignleadsviews.LeadConfigurationView.as_view(), name='lead-configuration'),
    

    
    path('mark-done/', campaignleadshtmx.mark_done, name='mark-done' ),
    
    path('new-leads-column/', campaignleadshtmx.new_leads_column, name='new-leads-column' ),
    path('new-call/', campaignleadshtmx.new_call, name='new-call' ),
    path('new-call/<int:lead_pk>/<int:call_count>/<int:max_call_count>/', campaignleadshtmx.new_call, name='new-call' ),
    path('delete-lead/', campaignleadshtmx.delete_lead, name='delete-lead' ),
    
    path('get-leads-column-meta-data/', campaignleadshtmx.get_leads_column_meta_data, name='get-leads-column-meta-data' ),
    path('create-campaign-lead/', campaignleadshtmx.create_campaign_lead, name='create-campaign-lead' ),
    path('log-communication/', campaignleadshtmx.log_communication, name='log-communication' ),
    path('add-booking/', campaignleadshtmx.add_booking, name='add-booking' ),
    path('mark-arrived/', campaignleadshtmx.mark_arrived, name='mark-arrived' ),
    path('mark-sold/', campaignleadshtmx.mark_sold, name='mark-sold' ),
    # path('test-whatsapp-message/', campaignleadshtmx.test_whatsapp_message, name='test-whatsapp-message' ),
    path('template-editor/', campaignleadshtmx.template_editor, name='template-editor' ),
    path('template-save/', campaignleadshtmx.template_save, name='template-save' ),
    
    path('campaign-lead-get-modal-content/', campaignleadshtmx.get_modal_content, name='campaign-lead-get-modal-content' ),
    path('campaign-lead-get-modal-content/<str:param1>/', campaignleadshtmx.get_modal_content, name='campaign-lead-get-modal-content' ),
    path('campaign-lead-get-modal-content/<str:param1>/<str:param2>/', campaignleadshtmx.get_modal_content, name='campaign-lead-get-modal-content' ),
    
]
