"""jobiewebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more inlistation please see:
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
import active_campaign.views as activecampaignviews
urlpatterns = [
    path('active-campaign-webhooks/<str:guid>/', activecampaignviews.Webhooks.as_view(), name='active-campaign-webhooks' ),
    path('set-campaign-site/<int:campaign_pk>/', activecampaignviews.set_campaign_site, name='set-campaign-site'),
    path('set-whatsapp-template-sending-status/', activecampaignviews.set_whatsapp_template_sending_status, name='set-whatsapp-template-sending-status'),
    path('set-active-campaign-lead-status/', activecampaignviews.set_active_campaign_leads_status, name='set-active-campaign-lead-status'),
    
]