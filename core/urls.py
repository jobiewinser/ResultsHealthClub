from django.urls import path
import core.views as coreviews
import core.htmx as corehtmx
urlpatterns = [
    # Public Facing
    # path('products/campaign-leads-product-page', coreviews.CampaignLeadsProductPageView.as_view(), name='campaign-leads-product-page' ),
    # path('login-htmx', coreviews.custom_login_post, name='login-htmx' ),

    path('', coreviews.HomeView.as_view(), name='customer-home'),
    # path('customer-login/', coreviews.CustomerLoginView.as_view(), name='customer-login'),
    path('login-demo/', coreviews.LoginDemoView.as_view(), name='login-demo'),
    
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
    # path('free-tasters/overview/', coreviews.FreeTasterOverviewView.as_view(), name='free-taster-overview' ),
    path('free-tasters/redirect/<str:guid>/', coreviews.free_taster_redirect, name='free-taster' ),
    path('generate-free-taster-link/', corehtmx.generate_free_taster_link, name='generate-free-taster-link' ),
    path('create-calendly-webhook-subscription/', corehtmx.create_calendly_webhook_subscription, name='create-calendly-webhook-subscription' ),
    path('delete-calendly-webhook-subscription/', corehtmx.delete_calendly_webhook_subscription, name='delete-calendly-webhook-subscription' ),

    path('add-site/', corehtmx.add_site, name='add-site' ),
    path('add-stripe-payment-method-new-site-handler/', coreviews.add_stripe_payment_method_new_site_handler, name='add-stripe-payment-method-new-site-handler'),  
    path('detach-stripe-payment-method-new-site-handler/', coreviews.detach_stripe_payment_method_new_site_handler, name='detach-stripe-payment-method-new-site-handler'),  
    path('complete-stripe-subscription-new-site-handler/', coreviews.complete_stripe_subscription_new_site_handler, name='complete-stripe-subscription-new-site-handler'),  
    
    path('delete-free-taster-link/', corehtmx.delete_free_taster_link, name='delete-free-taster-link' ),  
    # path('configuration/', coreviews.ConfigurationView.as_view(), name='configuration'),  

    path('profile-configuration-needed/', coreviews.ProfileConfigurationNeededView.as_view(), name='profile-configuration-needed'),  
    path('configuration/company-permissions/', coreviews.CompanyPermissionsView.as_view(), name='company-permissions'),  
    path('configuration/site-permissions/', coreviews.SitePermissionsView.as_view(), name='site-permissions'),  
    path('configuration/change-sites-allowed/', coreviews.change_site_allowed, name='change-sites-allowed'),  
    path('configuration/deactivate-profile/', coreviews.deactivate_profile, name='deactivate-profile'),  
    path('configuration/reactivate-profile/', coreviews.reactivate_profile, name='reactivate-profile'),  
    path('submit-feedback-form/', coreviews.submit_feedback_form, name='submit-feedback-form'),  
    path('feedback-forms/', coreviews.FeedbackListView.as_view(), name='feedback-forms'),  
    path('feedback-forms/', coreviews.FeedbackListView.as_view(), name='feedback-forms'),  

    path('switch-subscription-begin/', coreviews.SwitchSubscriptionBeginView.as_view(), name='switch-subscription-begin'),  
    path('choose-attached-profiles/', coreviews.choose_attached_profiles, name='choose-attached-profiles'),  
    # path('stripe-subscription-success/', coreviews.StripeSubscriptionSuccessView.as_view(), name='stripe-subscription-success'),  
    # path('configuration/payments-and-billing/', coreviews.PaymentsAndBillingView.as_view(), name='payments-and-billing'),  
    path('stripe-subscription-canceled/', coreviews.StripeSubscriptionCanceledView.as_view(), name='stripe-subscription-cancelled'),  
    path('add-stripe-payment-method-handler/', coreviews.add_stripe_payment_method_handler, name='add-stripe-payment-method-handler'),  
    path('detach-stripe-payment-method-handler/', coreviews.detach_stripe_payment_method_handler, name='detach-stripe-payment-method-handler'),  
    path('complete-stripe-subscription-handler/', coreviews.complete_stripe_subscription_handler, name='complete-stripe-subscription-handler'),  
    path('renew-stripe-subscription/', coreviews.renew_stripe_subscription, name='renew-stripe-subscription'),  
    path('change-default-payment-method/', coreviews.change_default_payment_method, name='change-default-payment-method'),  
    path('accounts/register/', coreviews.RegisterNewCompanyView.as_view(), name='register'), 

    path('activate/<str:register_uuid>/<str:email>/', coreviews.activate, name='activate'),

]
