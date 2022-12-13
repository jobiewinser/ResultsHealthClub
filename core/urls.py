from django.urls import path
import core.views as coreviews
import core.htmx as corehtmx
urlpatterns = [
    # Public Facing
    # path('products/campaign-leads-product-page', coreviews.CampaignLeadsProductPageView.as_view(), name='campaign-leads-product-page' ),
    # path('login-htmx', coreviews.custom_login_post, name='login-htmx' ),

    path('', coreviews.HomeView.as_view(), name='customer-home'),
    path('customer-login/', coreviews.CustomerLoginView.as_view(), name='customer-login'),
    
    path('change-log/', coreviews.ChangeLogView.as_view(), name='change-log'),


    path('configuration/company-configuration/', coreviews.CompanyConfigurationView.as_view(), name='company-configuration'),
    path('configuration/site-configuration/', coreviews.SiteConfigurationView.as_view(), name='site-configuration'),


    path('configuration/change-profile-role/', coreviews.change_profile_role, name='change-profile-role'),
    path('configuration/change-profile-site/', coreviews.change_profile_site, name='change-profile-site'),
    # path('configuration/change-profile-sites-allowed/', coreviews.change_profile_sites_allowed, name='change-profile-sites-allowed'),

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

    path('add-site/', corehtmx.add_site, name='add-site' ),
    
    path('delete-free-taster-link/', corehtmx.delete_free_taster_link, name='delete-free-taster-link' ),  
    # path('configuration/', coreviews.ConfigurationView.as_view(), name='configuration'),  

    path('profile-incorrectly-configured/', coreviews.ProfileIncorrectlyConfiguredView.as_view(), name='profile-incorrectly-configured'),  
    path('configuration/company-permissions/', coreviews.CompanyPermissionsView.as_view(), name='company-permissions'),  
    path('configuration/site-permissions/', coreviews.SitePermissionsView.as_view(), name='site-permissions'),  
    path('configuration/change-sites-allowed/', coreviews.change_site_allowed, name='change-sites-allowed'),  

    
]
