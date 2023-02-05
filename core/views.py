#0.9 safe
import os
import sys
import traceback
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from calendly.api import Calendly
from core.core_decorators import check_core_profile_requirements_fulfilled
from core.models import ROLE_CHOICES, StripeCustomer, FreeTasterLink, FreeTasterLinkClick, Profile, Site, CompanyProfilePermissions, SiteProfilePermissions, Feedback, Subscription,SiteSubscriptionChange, Company
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from core.user_permission_functions import *
from whatsapp.api import Whatsapp
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.list import ListView
from stripe_integration.api import *
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from core.core_decorators import *
logger = logging.getLogger(__name__)

class LoginDemoView(View):
    template_name='core/customer_login.html'
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(groups__name='demo').order_by('last_login').first()
        [s.delete() for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == user.id]
        login(request, user, backend='core.backends.CustomBackend')
        user.last_login = datetime.now()
        user.save()
        return redirect("/")

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class HomeView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.profile:
                return redirect("/leads-and-calls/")
    


@method_decorator(login_required, name='dispatch')
# @method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class ChangeLogView(TemplateView):
    template_name='core/change_log.html'
    def get(self, request, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/change_log_htmx.html'
        return super().get(request, *args, **kwargs)
        
    
PROFILE_ERROR_OPTIONS = {
    '1':"No profile set up for your user account.",
    '2':"No company assigned to your profile (please contact: <a href='mailto:jobie@winser.uk'>jobie@winser.uk</a> or <a href='tel:+447872000364'>+44 7872 000364</a>).",
    '3':"You have not been granted permission to access any sites.",
    '4':"You have not been allocated a primary site.",
}
class ProfileConfigurationNeededView(TemplateView):
    template_name='core/profile_configuration_needed.html'
    def get(self, request, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/profile_configuration_needed_htmx.html'
        return super().get(request, *args, **kwargs)
        

    def get_context_data(self, **kwargs):
        context = super(ProfileConfigurationNeededView, self).get_context_data(**kwargs)       
        errors = []
        if not self.request.user.profile:
            errors.append(PROFILE_ERROR_OPTIONS['1'])
            errors.append(PROFILE_ERROR_OPTIONS['2'])
            errors.append(PROFILE_ERROR_OPTIONS['3'])
            errors.append(PROFILE_ERROR_OPTIONS['4'])
        else:
            if not self.request.user.profile.company:
                errors.append(PROFILE_ERROR_OPTIONS['2'])
            if not self.request.user.profile.active_sites_allowed:
                errors.append(PROFILE_ERROR_OPTIONS['3'])
            if not self.request.user.profile.site:
                errors.append(PROFILE_ERROR_OPTIONS['4'])
        context['errors'] = errors
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='post')
class CompanyPermissionsView(TemplateView):
    template_name='campaign_leads/htmx/edit_permissions.html'

    def get_context_data(self, **kwargs):
        context = super(CompanyPermissionsView, self).get_context_data(**kwargs)       
        company_permissions = CompanyProfilePermissions.objects.get(pk=self.request.GET.get('company_permissions_pk'))
        company_permissions.save()
        context['company_permissions'] = company_permissions
        context['profile'] = company_permissions.profile
        return context
    def post(self, request):
        company_permissions = CompanyProfilePermissions.objects.get(pk = request.POST.get('company_permissions_pk'))
        context = {'company_permissions':company_permissions}
        if get_profile_allowed_to_edit_other_profile_permissions(request.user.profile, company_permissions.company):
            if not company_permissions.profile.role == 'a':
                if request.user.profile.role == 'a' or (request.user.profile.role == 'b' and company_permissions.profile.role == 'c'):      
                    for key in [
                                'edit_user_permissions',
                                ] :
                        if key in request.POST:
                            setattr(company_permissions, key, (request.POST.get(key, 'off') == 'on'))
                    company_permissions.save()
                    return render(request, 'campaign_leads/htmx/company_permissions.html', context)
        context['error'] = "You do not have permission to do this"
        return render(request, 'campaign_leads/htmx/company_permissions.html', context)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='post')
class SitePermissionsView(TemplateView):
    template_name='campaign_leads/htmx/edit_permissions.html'

    def get_context_data(self, **kwargs):
        context = super(SitePermissionsView, self).get_context_data(**kwargs)    
        site_permissions = SiteProfilePermissions.objects.get(pk=self.request.GET.get('site_permissions_pk'))
        site_permissions.save()
        context['site_permissions'] = site_permissions
        context['profile'] = site_permissions.profile
        return context
    def post(self, request):
        site_permissions = SiteProfilePermissions.objects.get(pk = request.POST.get('site_permissions_pk'))
        context = {'site_permissions':site_permissions}
        if get_profile_allowed_to_edit_other_profile_permissions(request.user.profile, site_permissions.site.company):
            if request.user.profile.role == 'a' or (request.user.profile.role == 'b' and site_permissions.profile.role == 'c'):      
                for key in ['view_site_configuration',
                            'edit_site_configuration',
                            'edit_site_calendly_configuration',                            
                            'edit_whatsapp_settings',
                            'toggle_active_campaign',                            
                            'toggle_whatsapp_sending',                            
                            'change_subscription',                            
                            ] :
                    if key in request.POST:
                        setattr(site_permissions, key, (request.POST.get(key, 'off') == 'on'))
                site_permissions.save()
                return render(request, 'campaign_leads/htmx/site_permissions.html', context)
        context['error'] = "You do not have permission to do this"
        return render(request, 'campaign_leads/htmx/site_permissions.html', context)

def get_site_configuration_context(request):
    request.GET._mutable = True   
    context = {}
    site_pk = get_single_site_pk_from_request_or_default_profile_site(request)   
    request.GET['site_pk'] = site_pk   
    site = Site.objects.get(pk=site_pk)     

    # permissions
    context['permitted'] = False
    if get_profile_allowed_to_view_site_configuration(request.user.profile, site):
        context['permitted'] = True
    # endpermissions
    context['whatsapp_numbers'] = site.get_live_whatsapp_phone_numbers()          
    calendly = Calendly(site.calendly_token)
    site_webhook_active = False
    if site.calendly_organization:
        calendly_webhooks = calendly.list_webhook_subscriptions(organization = site.calendly_organization).get('collection')
        if calendly_webhooks:
            for webhook in calendly_webhooks:
                if webhook.get('state') == 'active' \
                and webhook.get('callback_url') == f"{os.getenv('SITE_URL')}/calendly-webhooks/{site.guid}/" \
                and webhook.get('organization') == f"{os.getenv('CALENDLY_URL')}/organizations/{site.calendly_organization}":
                    site_webhook_active = True
                    break
    context['site'] = site
    context['site_webhook_active'] = site_webhook_active
    if site.whatsapp_access_token:
        whatsapp = Whatsapp(site.whatsapp_access_token)
        context['whatsapp_business_details'] = whatsapp.get_business(site.company.whatsapp_app_business_id)
    else:
        context['whatsapp_business_details'] = {"error":True}
    return context
@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
@method_decorator(not_demo_or_superuser_check, name='post')
class SiteConfigurationView(TemplateView):
    template_name='core/site_configuration.html'

    def get(self, request, *args, **kwargs):   
        # site = Site.objects.get(pk=site_pk) 
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/site_configuration_htmx.html'
        return super(SiteConfigurationView, self).get(request, args, kwargs)

    def get_context_data(self):    
        context = super(SiteConfigurationView, self).get_context_data()
        context.update(get_site_configuration_context(self.request))
        context['get_stripe_subscriptions_and_update_models'] = context['site'].get_stripe_subscriptions_and_update_models()
        return context
    def post(self, request):
        # if settings.DEMO and not request.user.is_superuser:
        #     return HttpResponse(status=500)
        self.request.POST._mutable = True 
        site = Site.objects.get(pk=request.POST.get('site_pk'))   
        if not get_profile_allowed_to_view_site_configuration(request.user.profile, site):
            if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                return HttpResponse("You don't have the edit Calendly configuration permission", status=403)
            raise PermissionDenied()
        
        response_text = ""     
        if 'name' in request.POST:
            site.name = request.POST['name']
            response_text = f"{response_text} <span hx-swap-oob='innerHTML:.name_display_{site.pk}'>{site.name}</span>"            
            site.save()
            return HttpResponse(response_text, status=200)
            
        if 'calendly_organization' in request.POST or 'calendly_token' in request.POST:
            if 'calendly_organization' in request.POST:
                if request.POST['calendly_organization'] == '' or request.POST['calendly_organization'].replace('*', ''): #stops the **** input submitting!
                    site.calendly_organization = request.POST['calendly_organization']        
                    site.save()            
                
            if 'calendly_token' in request.POST:
                if request.POST['calendly_token'] == '' or request.POST['calendly_token'].replace('*', ''): #stops the **** input submitting!
                    site.calendly_token = request.POST['calendly_token']        
                    site.save()
            context = get_site_configuration_context(request)
            context.update({'advanced_settings_open':True})
            return render(request, 'core/htmx/site_configuration_htmx.html',context)
        return HttpResponse( status=200)
            

@method_decorator(login_required, name='dispatch')
# @method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class CompanyConfigurationView(TemplateView):
    template_name='core/company_configuration.html'

    def get(self, request, *args, **kwargs):
        if not request.user.profile.role == 'a':
            if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                return HttpResponse("Only an owner can edit the company configuration", status=403)
            raise PermissionDenied()
        return super().get(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
            
        self.request.GET._mutable = True       
        context = super(CompanyConfigurationView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/company_configuration_htmx.html'
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        context['company'] = self.request.user.profile.company
        for profile in context['company'].profile_set.all():
            CompanyProfilePermissions.objects.get_or_create(profile=profile, company=profile.company)  
        
        context['role_choices'] = ROLE_CHOICES
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        return context
@login_required
@not_demo_or_superuser_check
def change_profile_role(request):
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if (not request.user == profile.user and get_profile_allowed_to_edit_other_profile(request.user.profile, profile)):
        role = request.POST.get('role', None)
        if role in ['b','c']:
            context = {}
            profile.role = role
            profile.save()
            context['profile'] = profile
            context['role_choices'] = ROLE_CHOICES
            # context['site_list'] = get_available_sites_for_user(request.user)
            return render(request, 'core/htmx/company_configuration_row.html', context)
    return HttpResponse("You are not allowed to edit this, please contact your manager.",status=500)
@login_required
@not_demo_or_superuser_check
def change_profile_site(request):
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, profile):
        site_pk = request.POST.get('site_pk', None)
        if site_pk:
            context = {}
            profile.site = Site.objects.get(pk=site_pk)
            profile.save()
            context['profile'] = profile
            context['role_choices'] = ROLE_CHOICES
            # context['site_list'] = get_available_sites_for_user(request.user)
            return render(request, 'core/htmx/company_configuration_row.html', context)
    return HttpResponse("You are not allowed to edit this, please contact your manager.",status=500)
@login_required
@not_demo_or_superuser_check
def change_site_allowed(request):
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    context = {}
    site_pk = int(request.POST.get('site_pk', 0))
    context['profile'] = profile
    # context['role_choices'] = ROLE_CHOICES
    context['site_permissions'] = SiteProfilePermissions.objects.get(profile=profile, site=Site.objects.get(pk=site_pk))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, profile):
        sites_allowed_pk_list = list(profile.active_sites_allowed.values_list('pk', flat=True))
        site_allowed = request.POST.get('site_allowed', 'off') == 'on'
        if site_allowed:
            if not site_pk in sites_allowed_pk_list:
                sites_allowed_pk_list.append(site_pk) 
        else:
            if site_pk in sites_allowed_pk_list:
                sites_allowed_pk_list.remove(site_pk)
        profile.sites_allowed.set(Site.objects.filter(pk__in=sites_allowed_pk_list).exclude(active=False))
        profile.save()
    else:
        context['error'] = "You do not have permission to do this"
    if request.POST.get('add_user', False):
        context['site'] = Site.objects.get(pk=site_pk)
        return render(request, 'core/htmx/site_configuration_htmx.html', context)
    return render(request, 'campaign_leads/htmx/edit_permissions.html', context)
@login_required
def submit_feedback_form(request):
    existing_feedback = Feedback.objects.filter(user=request.user).order_by('created').last()
    if existing_feedback:
        if existing_feedback.created > (datetime.now() - timedelta(seconds = 5)):
            return HttpResponse(status=400)
    comment = request.POST.get('comment')
    if comment:
        feedback, created = Feedback.objects.get_or_create(
            user=request.user,
            comment=comment,
        )

    return HttpResponse(status=200)

@login_required
@not_demo_or_superuser_check
def deactivate_profile(request):
    user = User.objects.get(pk=request.POST.get('user_pk'))
    if not user.profile.role == 'a':
        if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile) and not user.profile.role == 'a':
            user.is_active = False
            user.save()
            return HttpResponse(status=200)
    return HttpResponse(status=403)


@login_required
@not_demo_or_superuser_check
def reactivate_profile(request):
    site = Site.objects.get(pk=request.POST.get('site_pk'))
    user = User.objects.get(pk=request.POST.get('user_pk'))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile):
        if site.subscription.max_profiles:
            if site.users.count() >= site.subscription.max_profiles:
                return HttpResponse("You already have the maximum number of users", status=400)
        user.is_active = True
        user.save()
        user.profile.sites_allowed.set([site])
        user.profile.site = site
        user.profile.save()
        return HttpResponse(status=200)
    return HttpResponse(status=403)




# def custom_login_post(request):    
#     user = authenticate(username=request.POST.get('username', ''), email=request.POST.get('email', ''), password=request.POST.get('password', ''))
#     if user:
#         login(request, user)
#         return HttpResponse(status=200)
#     return HttpResponse("Account not found", status=404)


# @method_decorator(login_required, name='dispatch')
# @method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
# class FreeTasterOverviewView(TemplateView):
#     template_name='core/free_taster_overview.html'

#     def get_context_data(self, **kwargs):
#         self.request.GET._mutable = True       
#         context = super(FreeTasterOverviewView, self).get_context_data(**kwargs)
#         if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
#             self.template_name = 'core/htmx/free_taster_table_htmx.html'
#         # context['site_list'] = get_available_sites_for_user(self.request.user)
#         free_taster_links = FreeTasterLink.objects.all()

#         site_pks = get_site_pks_from_request_and_return_sites(self.request)
#         if site_pk:
#             free_taster_links = free_taster_links.filter(site__pk=site_pk)
#             self.request.GET['site_pk'] = site_pk                    
#         context['free_taster_links'] = free_taster_links

#         return context
        
 
class FeedbackListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Feedback
    # template_name = "core/feedback_list.html"
    def get(self, request, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/feedback_list_htmx.html'
        return super().get(request, *args, **kwargs)
    def test_func(self):
        return self.request.user.is_superuser
        
# @method_decorator(login_required, name='dispatch')
# class ConfigurationView(TemplateView):
#     template_name='core/configuration.html'

#     def get_context_data(self, **kwargs):
#         context = super(ConfigurationView, self).get_context_data(**kwargs)        
#         return context

def free_taster_redirect(request, **kwargs):
    try:
        free_taster_link = FreeTasterLink.objects.get(guid=kwargs.get('guid'))
        FreeTasterLinkClick.objects.create(link=free_taster_link)
    except:
        pass
    return HttpResponseRedirect("https://WinserSystemss.co.uk/book-free-taster-sessions-abingdon/")

@login_required
def get_site_pks_from_request_and_return_sites(request):
    #make request.GET mutable and get request_dict
    request.GET._mutable = True 
    profile = request.user.profile
    if request.method == 'GET':
        request_dict = request.GET
    elif request.method == 'POST':
        request_dict = request.POST
    
    #get site_pks from request
    temp_site_pks = request.GET.get('site_pks', [])
    #if site_pks is a string, convert to list
    if type(temp_site_pks) == list:
        site_pks = temp_site_pks
    else:
        site_pks = request.GET.getlist('site_pks', [])
        
    #remove empty strings from list
    while "" in site_pks:
        site_pks.pop(site_pks.index(""))
        
    if not site_pks:
        if profile and not request_dict.get('campaign_category_pk', None) and not request_dict.get('campaign_pk', None):
            if profile.site:
                site_pks = [profile.site.pk]
    request.GET['site_pks'] = site_pks
    if site_pks:
        return request.user.profile.active_sites_allowed.filter(pk__in=site_pks) #this only allows active sites in the user's active sites list
    return Site.objects.none()
#this doesn't needs a method decorator because it is not directly used by urls.py
def get_single_site_pk_from_request_or_default_profile_site(request):  
    if request.method == 'GET':
        request_dict = request.GET
    elif request.method == 'POST':
        request_dict = request.POST
    site_pk = request_dict.get('site_pk', None)
    if site_pk:
        return site_pk
    profile = Profile.objects.filter(user=request.user).first()
    if profile and not request_dict.get('campaign_category_pk', None) and not request_dict.get('campaign_pk', None):
        if profile.site:
            return request.user.profile.site.pk

#this doesn't needs a method decorator because it is not directly used by urls.py
def get_campaign_category_pks_from_request(request):  
    if request.method == 'GET':
        request_dict = request.GET
    elif request.method == 'POST':
        request_dict = request.POST
    campaign_category_pks = request_dict.getlist('campaign_category_pks', None)
    if type(campaign_category_pks) == list:
        campaign_category_pks = campaign_category_pks
    else:
        campaign_category_pks = []
        
    return campaign_category_pks
    
def handler500(request):
    template_name = '500.html'
    known_errors = []
    try:
        type_, value, tb = sys.exc_info()
        
        if str(value) not in known_errors:
            if request.user.id:
                id = str(request.user.id)
            else:
                id = "None"

            if request.user.username:
                name = str(request.user.username)
            else:
                name = "None"

            if request.META['PATH_INFO']:
                path = os.getenv('SITE_URL')+str(request.META['PATH_INFO'])
            else:
                path = "None"

            body = "None"
            try:
                if request.body:
                    body = str(request.body)
            except:
                pass

            if request.headers:
                headers = str(request.headers)
            else:
                headers = "None"
                
            error_description = f"<p>user id: {str(id)} <br> user name: {str(name)} <br> url: {str(path)}  <br> Error type: {str(value)}  <br> Request Body: {str(body)}  <br> Request Headers: {str(headers)} <br><br><br> Traceback: {str(traceback.format_exception(type, value, tb))}</p>"
            send_mail(
                subject=f'Winser Systems {os.getenv("SITE_URL")} - 500 error ',
                message=error_description,
                from_email='jobiewinser@gmail.com',
                recipient_list=['jobiewinser@gmail.com'])

    except Exception as e:
        logger.error(   "couldn't send error email", str(e))
    if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
        template_name = '500_snackbar.html'  
    return render(request, template_name, status=500)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class SwitchSubscriptionBeginView(TemplateView):
    template_name='core/htmx/choose_attached_profiles.html'

    def get(self, request, *args, **kwargs):
        request.GET._mutable = True   
        site_pk = request.GET.get('site_pk')
        site = request.user.profile.active_sites_allowed.filter(pk=site_pk).first()
        if site:  
            if get_profile_allowed_to_change_subscription(request.user.profile, site):
                return super(SwitchSubscriptionBeginView, self).get(request, args, kwargs)

    def get_context_data(self):    
        context = super(SwitchSubscriptionBeginView, self).get_context_data()
        site_pk = self.request.GET.get('site_pk')
        site = self.request.user.profile.active_sites_allowed.get(pk=site_pk)
        site_subscription_change_pk = self.request.GET.get('site_subscription_change_pk')
        if not site_subscription_change_pk:
            switch_subscription = Subscription.objects.get(numerical=self.request.GET.get('numerical'))        
            SiteSubscriptionChange.objects.filter(subscription_to=switch_subscription, subscription_from = site.subscription, site=site, canceled=None, completed=None).exclude(version_started=str(settings.VERSION)).update(canceled=datetime.now())
            existing_site_subscription_changes = SiteSubscriptionChange.objects.filter(version_started=str(settings.VERSION), subscription_to=switch_subscription, subscription_from = site.subscription, site=site, canceled=None, completed=None).order_by('created')
            if existing_site_subscription_changes:
                latest_existing_site_subscription_change = existing_site_subscription_changes.last()
                existing_site_subscription_changes.exclude(pk=latest_existing_site_subscription_change.pk).update(canceled=datetime.now())
            site_subscription_change, created = SiteSubscriptionChange.objects.get_or_create(
                version_started=str(settings.VERSION),
                subscription_to=switch_subscription, 
                subscription_from = site.subscription, 
                site=site, 
                canceled=None, 
                completed=None
            )
        else:
            site_subscription_change = SiteSubscriptionChange.objects.get(
                pk=site_subscription_change_pk
            )
        if (site_subscription_change.subscription_to.max_profiles > site_subscription_change.subscription_from.max_profiles and not site_subscription_change.subscription_from.max_profiles == 0) or site_subscription_change.subscription_to.max_profiles == 0:
            #if not reducing number of allowed profiles
            self.template_name = 'core/htmx/subscription_payment.html'
        context['site'] = site
        # context['switch_subscription'] = switch_subscription
        context['site_subscription_change'] = site_subscription_change
        
        return context

@login_required
@check_core_profile_requirements_fulfilled
def choose_attached_profiles(request):
    site_subscription_change_pk = request.POST.get('site_subscription_change_pk')
    # del request.POST['site_subscription_change_pk']
    site_subscription_change = SiteSubscriptionChange.objects.get(pk=site_subscription_change_pk)
    if site_subscription_change.site in request.user.profile.active_sites_allowed.all():
        user_pks = []
        for k,v in request.POST.items():
            if 'choose_profile_' in k and v == 'on':
                user_pks.append(k.replace('choose_profile_', ''))
        if len(user_pks) > site_subscription_change.subscription_to.max_profiles:
            return HttpResponse("Too many profiles chosen", status=400)

        site_subscription_change.users_to_keep.set(User.objects.filter(pk__in=user_pks, profile__company=site_subscription_change.site.company))
        site_subscription_change.stripe_session_id = f"{site_subscription_change.site.guid}_{str(datetime.timestamp(datetime.now()))}"
        site_subscription_change.completed_by = request.user
        site_subscription_change.save()
        # if site_subscription_change.subscription_to.whatsapp_enabled:
        #     return render(request, 'templates/core/htmx/setup_payment.html', {'site_subscription_change':site_subscription_change})
        # else:
        
        
        
        try:
            stripe_customer = get_or_create_customer(customer_id=site_subscription_change.site.stripecustomer.customer_id)
        except Site.stripecustomer.RelatedObjectDoesNotExist as e:
            stripe_customer = get_or_create_customer(billing_email=site_subscription_change.site.billing_email)
        customer_id = stripe_customer['id']
        stripe_customer_object, created = StripeCustomer.objects.get_or_create(
            customer_id=customer_id
        )
        stripe_customer_object.json_data = stripe_customer
        stripe_customer_object.site = site_subscription_change.site
        stripe_customer_object.save()
        if site_subscription_change.subscription_to.stripe_price_id:
            return render(request, 'core/htmx/subscription_payment.html', {'site_subscription_change':site_subscription_change})
        cancel_subscription(site_subscription_change.site.stripecustomer.subscription_id)
        site_subscription_change.complete()
        site_subscription_change.process()
        return render(request, 'core/htmx/subscription_changed.html', {})
    return HttpResponse("Not allowed to change that site", status=403)
    
@login_required
@check_core_profile_requirements_fulfilled
def change_default_payment_method(request):
    site_pk = request.POST.get('site_pk')
    invoice_id = request.POST.get('invoice_id')
    site = request.user.profile.active_sites_allowed.get(pk=site_pk)
    payment_method_id = request.POST.get('payment_method_id')
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        update_payment_method(site.stripecustomer.subscription_id, payment_method_id)   
        if invoice_id and not invoice_id == 'None': 
            invoice = retry_invoice(invoice_id)
        return render(request, 'core/htmx/subscription_changed.html', {})
    return HttpResponse("Not allowed to change that site subscription", status=403)

@login_required
@check_core_profile_requirements_fulfilled
def complete_stripe_subscription_handler(request):
    complete_stripe_subscription(request.POST.get('site_subscription_change_pk'), request.POST.get('payment_method_id'), request.user)
    return render(request, 'core/htmx/subscription_changed.html', {})

def complete_stripe_subscription(site_subscription_change_pk, payment_method_id, user):
    site_subscription_change_pk = site_subscription_change_pk
    site_subscription_change = SiteSubscriptionChange.objects.get(pk=site_subscription_change_pk) 
    site = site_subscription_change.site
    
    if get_profile_allowed_to_change_subscription(user.profile, site):
        try:
            #check it exists
            site.stripecustomer.pk
        except Site.stripecustomer.RelatedObjectDoesNotExist as e:
            stripe_customer = get_or_create_customer(billing_email=site.billing_email)
            customer_id = stripe_customer['id']
            stripe_customer_object, created = StripeCustomer.objects.get_or_create(
                customer_id=customer_id
            )
            stripe_customer_object.site = site
            stripe_customer_object.save()
        
        if site_subscription_change.subscription_from.numerical < site_subscription_change.subscription_to.numerical:
            #if upgrading, upgrade immediately and prorate
            stripe_subscription = add_or_update_subscription(
                site.stripecustomer.customer_id, 
                payment_method_id, 
                site_subscription_change.subscription_to.stripe_price_id,
                subscription_id=site.stripecustomer.subscription_id,
                proration_behavior='create_prorations',
            )
        else:
            #if downgrading, keep current membership until end of period
            stripe_subscription = add_or_update_subscription(
                site.stripecustomer.customer_id, 
                payment_method_id, 
                site_subscription_change.subscription_to.stripe_price_id,
                subscription_id=site.stripecustomer.subscription_id,
                proration_behavior='none',
            )
        site.stripecustomer.subscription_id = stripe_subscription.stripe_id
        site.stripecustomer.save()
        site.get_stripe_subscriptions_and_update_models()
        site_subscription_change.completed_by = user
        site_subscription_change.complete()
    return HttpResponse("Not allowed to change that site subscription", status=403)


@login_required
def complete_stripe_subscription_new_site_handler(request):
    payment_method_id = request.POST.get('payment_method_id')
    if payment_method_id:
        profile = request.user.profile
        site = profile.sites_allowed.get(pk=request.POST['site_pk'])
        if get_profile_allowed_to_change_subscription(profile, site):
            site.complete_stripe_subscription_new_site(payment_method_id)
            
            site.active = True
            site.sign_up_subscription = None
            site.save()
            profile.sites_allowed.add(site)
            profile.save()
            response = HttpResponse( status=200)
            response["HX-Redirect"] = f"/configuration/site-configuration/?site_pk={site.pk}"
            return response
        return HttpResponse("Not allowed to change that site subscription", status=403)

@login_required
@check_core_profile_requirements_fulfilled
def renew_stripe_subscription(request):
    site_pk = request.POST['site_pk']   
    site = Site.objects.get(pk=site_pk)    
    if get_profile_allowed_to_change_subscription(request.user.profile, site): 
        payment_method_id = request.POST.get('payment_method_id')
        if site.stripecustomer.subscription_id and payment_method_id:
            renew_subscription(site.stripecustomer.subscription_id, payment_method_id)
            return render(request, 'core/htmx/subscription_changed.html', {})
    return HttpResponse("Not allowed to change that site subscription", status=403)

# @method_decorator(login_required, name='dispatch')
# @method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
# class PaymentsAndBillingView(TemplateView):
#     template_name='core/payments_and_billing.html'

#     def get(self, request, *args, **kwargs):   
#         # site = Site.objects.get(pk=site_pk) 
#         if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
#             self.template_name = 'core/htmx/payments_and_billing_htmx.html'
#         return super(PaymentsAndBillingView, self).get(request, args, kwargs)

#     def get_context_data(self, **kwargs):
#         self.request.GET._mutable = True   
#         context = {}
#         site_pk = get_single_site_pk_from_request_or_default_profile_site(self.request)   
#         self.request.GET['site_pk'] = site_pk   
#         site = Site.objects.get(pk=site_pk)     

#         # permissions
#         context['permitted'] = False
#         if get_profile_allowed_to_view_site_configuration(self.request.user.profile, site):
#             context['permitted'] = True
#         # end permissions
        
#         context['site'] = site
#         # context['stripe_subscriptions'] = list_subscriptions(site.stripecustomer.customer_id)
#         return context
    
# @method_decorator(login_required, name='dispatch')
# @method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
# class StripeSubscriptionCanceledView(TemplateView):
#     template_name='core/stripe_subscription_canceled.html'

#     def get_context_data(self, **kwargs):
#         context = super(StripeSubscriptionCanceledView, self).get_context_data(**kwargs)       
#         return context


    
@login_required
@check_core_profile_requirements_fulfilled
def add_stripe_payment_method_handler(request): 
    context = {}
    site_pk = request.POST.get('site_pk')
    site = request.user.profile.active_sites_allowed.get(pk=site_pk)
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        add_stripe_payment_method(site, 
            request.POST['cardNumber'], 
            request.POST['expiryMonth'],
            request.POST['expiryYear'],
            request.POST['cvc'])
        context['site'] = site
        site_subscription_change_pk = request.POST.get('site_subscription_change_pk')        
        if site_subscription_change_pk:
            context['site_subscription_change'] = SiteSubscriptionChange.objects.filter(pk=site_subscription_change_pk).last()
        return render(request, 'core/htmx/payment_methods.html', context)
    return HttpResponse(status=403)

@login_required
# @check_core_profile_requirements_fulfilled
def add_stripe_payment_method_new_site_handler(request): 
    context = {}
    site_pk = request.POST.get('site_pk')
    site = request.user.profile.sites_allowed.get(pk=site_pk)
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        add_stripe_payment_method(site, 
            request.POST['cardNumber'], 
            request.POST['expiryMonth'],
            request.POST['expiryYear'],
            request.POST['cvc']) 
        context['site'] = site
        site_subscription_change_pk = request.POST.get('site_subscription_change_pk')        
        if site_subscription_change_pk:
            context['site_subscription_change'] = SiteSubscriptionChange.objects.filter(pk=site_subscription_change_pk).last()
        return render(request, 'campaign_leads/htmx/new_site_payment_methods.html', context)
    return HttpResponse(status=403)

def add_stripe_payment_method(site, card_number, expiry_month, expiry_year, cvc):    
    try:
        # Check if exists
        site.stripecustomer.pk
    except Site.stripecustomer.RelatedObjectDoesNotExist as e:
        stripe_customer = get_or_create_customer(billing_email=site.billing_email)
        customer_id = stripe_customer['id']
        stripe_customer_object, created = StripeCustomer.objects.get_or_create(
            customer_id=customer_id
        )
        stripe_customer_object.site = site
        stripe_customer_object.save()
    
    payment_method, error = add_payment_method(card_number, expiry_month, expiry_year, cvc)
    if error:
        return HttpResponse(str(error), status=400)
    payment_method = attach_payment_method(
        site.stripecustomer.customer_id, 
        payment_method['id']
    )
@login_required
@check_core_profile_requirements_fulfilled
def detach_stripe_payment_method_handler(request): 
    context = {}
    site_pk = request.POST.get('site_pk')
    site = request.user.profile.active_sites_allowed.get(pk=site_pk)
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        payment_method, error = detach_stripe_payment_method(request.POST['payment_method_id'])
        if error:
            return HttpResponse(str(error), status=400)
        context['site'] = site
        site_subscription_change_pk = request.POST.get('site_subscription_change_pk')        
        if site_subscription_change_pk:
            context['site_subscription_change'] = SiteSubscriptionChange.objects.filter(pk=site_subscription_change_pk).last
        return render(request, 'core/htmx/payment_methods.html', context)
    return HttpResponse(status=403)

@login_required
def detach_stripe_payment_method_new_site_handler(request): 
    context = {}
    site_pk = request.POST.get('site_pk')
    site = request.user.profile.active_sites_allowed.get(pk=site_pk)
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        payment_method, error = detach_stripe_payment_method(request.POST['payment_method_id'])
        if error:
            return HttpResponse(str(error), status=400)
        context['site'] = site
        site_subscription_change_pk = request.POST.get('site_subscription_change_pk')        
        if site_subscription_change_pk:
            context['site_subscription_change'] = SiteSubscriptionChange.objects.filter(pk=site_subscription_change_pk).last
        return render(request, 'core/htmx/payment_methods.html', context)
    return HttpResponse(status=403)
def detach_stripe_payment_method(payment_method_id):
    payment_method, error = detach_payment_method(
        payment_method_id
    )
    return payment_method, error
    
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.template import loader
import uuid
class RegisterNewCompanyView(TemplateView):
    template_name='registration/register_new_company.html'
    def get(self, request, *args, **kwargs):
        # if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
        #     self.template_name = 'core/change_log_htmx.html'
        return super().get(request, *args, **kwargs)
    def post(self, request):
        error_found = False
        context= {'errors':{
            'owner_email':[],
            'company_name':[],
            'password':[],
        }}
        if settings.DEBUG:
            Company.objects.filter(name__iexact = 'bleap').delete()
            Profile.objects.filter(user__email__iexact = 'jobiewinser@live.co.uk').delete()
            User.objects.filter(email__iexact = 'jobiewinser@live.co.uk').delete()
            Site.objects.filter(billing_email__iexact = 'jobiewinser@live.co.uk').update(billing_email='')
            
        owner_email = request.POST.get('owner_email').lower()
        company_name = request.POST.get('company_name')
        password = request.POST.get('password')
        
        context['owner_email'] = owner_email
        context['company_name'] = company_name
        context['password'] = password
        
        
        for error in is_password_safe(password):
            context['errors']['password'].append(error)
            error_found = True
        
        existing_users = User.objects.filter(email=owner_email)        
        if existing_users:
            if existing_users.filter(is_active=True):
                context['errors']['owner_email'].append("This email is already used within our system.")
            else:
                context['errors']['owner_email'].append("This email is already in the process of registering. <br>If they have not completed this in 24 hours, it will become available again.")
            error_found = True
        
        existing_sites_with_email = Site.objects.filter(billing_email=owner_email)        
        if existing_sites_with_email:
            context['errors']['owner_email'].append("This email is already used within our system for a billing account.")
            error_found = True
        
        existing_companies = Company.objects.filter(name__iexact=company_name)
        if existing_companies:
            if existing_companies.filter(is_active=True):
                context['errors']['company_name'].append("This company already exists within our system.")
            else:
                context['errors']['company_name'].append("This company name is already in the process of registering. <br>If they have not completed this in 24 hours, it will become available again.")            
            error_found = True
            
        if error_found:
            return HttpResponse(render(request, "registration/register_new_company_snippet.html", context), status=200)
        
        user = User.objects.create(
            email = owner_email,
            username = owner_email,
            password = password,
            is_active = False,
        )
        
        company = Company.objects.create(
            name = company_name
        )
        
        profile = Profile.objects.create(
            user=user,
            company = company,
            register_uuid = str(uuid.uuid4())[:16],
            role="a"
        )
        
        message = loader.render_to_string('registration/registration_email.html', {
            'user': user,
            'domain': os.getenv("SITE_URL"),
            'profile': profile,
            'title': "Activate your account",
        })
        
        send_email(user.email, 'Activate your account.', {"message": message})
        return HttpResponse(render(request, "registration/register_new_company_success.html", context), status=200)

def send_email(recipients, subject, messages):
    
    if settings.DEBUG:
        messages['message'] = 'Debug - sent to jobiewinser@gmail.com instead of: ' +str(recipients)+ '<br>' + messages['message']
        subject = "[DEBUG] "+subject
        recipients = "jobiewinser@gmail.com"

    if type(recipients) == str:
        recipients = [recipients]

    response = send_mail(
        subject,
        messages.get('plain_message',None) or '',
        "jobiewinser@gmail.com",
        recipients,
        html_message=messages['message'],
        fail_silently=False,
    )
    return response


def activate(request, register_uuid, email):
    try:
        profile = Profile.objects.get(register_uuid=register_uuid, user__email__iexact=email, user__is_active=False, role="a")
    except(Profile.DoesNotExist):
        profile = None
    if profile:
        user = profile.user
        user.is_active = True
        user.save()
        login(request, user, backend='core.backends.CustomBackend')
        return redirect("/")
    else:
        return HttpResponse('Activation link is invalid!')
    
def is_password_safe(password):
    if len(password) < 10:
        yield "Password must be at least 10 characters Long"
    if len(password) > 32:
        yield "Password must be at most 32 characters Long"
    if not any(char.isdigit() for char in password):
        yield "Password must have a digit"
    if not any(char.isupper() for char in password):
        yield "Password must contain an upper case character"
    if not any(char.islower() for char in password):
        yield "Password must contain a lower case character"
        
@login_required
@not_demo_or_superuser_check
def profile_assign_color_htmx(request):
    from campaign_leads.views import hex_to_rgb_tuple
    #this function is used to assign a color to a profile and refresh the profile config row
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'), site__in=request.user.profile.active_sites_allowed)
    profile.color = hex_to_rgb_tuple(request.POST.get('color', "60F83D"))
    profile.save()
    return render(request, 'core/htmx/company_configuration_row.html', {'profile':profile})
    