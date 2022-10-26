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
import core.views as coreviews
import core.htmx as corehtmx
urlpatterns = [
    # Public Facing
    path('products/campaign-leads-product-page', coreviews.CampaignLeadsProductPageView.as_view(), name='campaign-leads-product-page' ),
    path('login-htmx', coreviews.custom_login_post, name='login-htmx' ),

    path('', coreviews.CustomerHomeView.as_view(), name='customer-home'),
    path('company-configuration/', coreviews.CompanyConfigurationView.as_view(), name='company-configuration'),
    path('site-configuration/', coreviews.SiteConfigurationView.as_view(), name='site-configuration'),


    path('configuration/change-profile-role/', coreviews.change_profile_role, name='change-profile-role'),
    path('configuration/change-profile-site/', coreviews.change_profile_site, name='change-profile-site'),

    # path('switch-user/', corehtmx.switch_user, name='switch-user' ),
    path('get-modal-content/', corehtmx.get_modal_content, name='get-modal-content' ),
    path('get-modal-content/<str:param1>/', corehtmx.get_modal_content, name='get-modal-content' ),
    path('get-modal-content/<str:param1>/<str:param2>/', corehtmx.get_modal_content, name='get-modal-content' ),
    path('modify-user/', corehtmx.ModifyUser.as_view(), name='modify-user' ),
    path('free-tasters/overview/', coreviews.FreeTasterOverviewView.as_view(), name='free-taster-overview' ),
    path('free-tasters/redirect/<str:guid>/', coreviews.free_taster_redirect, name='free-taster' ),
    path('generate-free-taster-link/', corehtmx.generate_free_taster_link, name='generate-free-taster-link' ),
    path('create-calendly-webhook-subscription/', corehtmx.create_calendly_webhook_subscription, name='create-calendly-webhook-subscription' ),
    path('delete-calendly-webhook-subscription/', corehtmx.delete_calendly_webhook_subscription, name='delete-calendly-webhook-subscription' ),
    
    path('delete-free-taster-link/', corehtmx.delete_free_taster_link, name='delete-free-taster-link' ),  
    path('configuration/', coreviews.ConfigurationView.as_view(), name='configuration'),  
]
