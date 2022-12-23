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
from core.models import ROLE_CHOICES, StripeCustomer, FreeTasterLink, FreeTasterLinkClick, Profile, Site, CompanyProfilePermissions, SiteProfilePermissions, Feedback, Subscription,SiteSubscriptionChange
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
class HomeView(TemplateView):
    template_name='core/customer_home.html'
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.profile:
                return redirect("/leads-and-calls/")
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/customer_home_htmx.html'
        return super(HomeView, self).get(request, args, kwargs)
    


@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
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
    '4':"You have not been allocated a main site.",
}
class ProfileIncorrectlyConfiguredView(TemplateView):
    template_name='profile_incorrectly_configured.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileIncorrectlyConfiguredView, self).get_context_data(**kwargs)       
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
class CompanyPermissionsView(TemplateView):
    template_name='campaign_leads/htmx/edit_permissions.html'

    def get_context_data(self, **kwargs):
        context = super(CompanyPermissionsView, self).get_context_data(**kwargs)       
        # permission_company = self.request.user.profile.company
        
        # profile = Profile.objects.get(pk=self.request.GET.get('profile_pk'))
        # context['company_permissions'], created = CompanyProfilePermissions.objects.get_or_create(profile=profile, company=permission_company)
        company_permissions = CompanyProfilePermissions.objects.get(pk=self.request.GET.get('company_permissions_pk'))
        company_permissions.save()
        context['company_permissions'] = company_permissions
        context['profile'] = company_permissions.profile
        # context['permission_company'] = permission_company
        return context
    def post(self, request):
        if settings.DEMO and not request.user.is_superuser:
            return HttpResponse(status=500)
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
class SitePermissionsView(TemplateView):
    template_name='campaign_leads/htmx/edit_permissions.html'

    def get_context_data(self, **kwargs):
        context = super(SitePermissionsView, self).get_context_data(**kwargs)       
        # permission_site = Site.objects.get(pk=self.request.GET.get('site_pk'))
        # context['site'] = Site.objects.get(pk=self.request.GET.get('site_pk'))
        # profile = Profile.objects.get(pk=self.request.GET.get('profile_pk'))
        site_permissions = SiteProfilePermissions.objects.get(pk=self.request.GET.get('site_permissions_pk'))
        site_permissions.save()
        context['site_permissions'] = site_permissions
        context['profile'] = site_permissions.profile
        # context['permission_site'] = permission_site
        return context
    def post(self, request):
        if settings.DEMO and not request.user.is_superuser:
            return HttpResponse(status=500)
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
    site_pk = get_single_site_pk_from_request(request)   
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
        return context
    def post(self, request):
        if settings.DEMO and not request.user.is_superuser:
            return HttpResponse(status=500)
        self.request.POST._mutable = True 
        site = Site.objects.get(pk=request.POST.get('site_pk'))   

        # permissions
        # if not get_profile_allowed_to_edit_site_configuration(request.user.profile, site):
        #     if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
        #         return HttpResponse("You don't have permission to edit this")
        #     raise PermissionDenied()
        # endpermissions


        response_text = ""     
        if 'name' in request.POST:
            if not get_profile_allowed_to_edit_site_configuration(request.user.profile, site):
                if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                    return HttpResponse("You don't have the edit site configuration permission", status=403)
                raise PermissionDenied()
            site.name = request.POST['name']
            response_text = f"{response_text} <span hx-swap-oob='innerHTML:.name_display_{site.pk}'>{site.name}</span>"            
            site.save()
            return HttpResponse(response_text, status=200)
            
        if 'calendly_organization' in request.POST or 'calendly_token' in request.POST:
            if not get_profile_allowed_to_edit_site_calendly_configuration(request.user.profile, site):
                if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                    return HttpResponse("You don't have the edit Calendly configuration permission", status=403)
                raise PermissionDenied()
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
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class CompanyConfigurationView(TemplateView):
    template_name='core/company_configuration.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True       
        context = super(CompanyConfigurationView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/company_configuration_htmx.html'
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        
        context['role_choices'] = ROLE_CHOICES
        context['company'] = self.request.user.profile.company
        for profile in context['company'].profile_set.all():
            CompanyProfilePermissions.objects.get_or_create(profile=profile, company=profile.company)
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        return context
@login_required
def change_profile_role(request):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
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
def change_profile_site(request):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
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
def change_site_allowed(request):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
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
        profile.sites_allowed.set(Site.objects.filter(pk__in=sites_allowed_pk_list))
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
def deactivate_profile(request):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=403)
    user = User.objects.get(pk=request.POST.get('user_pk'))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile):
        user.is_active = False
        user.save()
        return HttpResponse(status=200)
    return HttpResponse(status=403)


@login_required
def reactivate_profile(request):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=403)
    site = Site.objects.get(pk=request.POST.get('site_pk'))
    user = User.objects.get(pk=request.POST.get('user_pk'))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile):
        if site.subscription_new.max_profiles:
            if site.users.count() >= site.subscription_new.max_profiles:
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
    request.GET._mutable = True 
    if request.method == 'GET':
        request_dict = request.GET
    elif request.method == 'POST':
        request_dict = request.POST
    temp_site_pks = request.GET.get('site_pks', None)
    if type(temp_site_pks) == list:
        site_pks = temp_site_pks
    else:
        site_pks = request.GET.getlist('site_pks',request.user.profile.active_sites_allowed.values_list('pk', flat=True))
    while "" in site_pks:
        site_pks.pop(site_pks.index(""))
    if not site_pks:
        profile = Profile.objects.filter(user=request.user).first()
        if profile and not request_dict.get('campaign_category_pk', None) and not request_dict.get('campaign_pk', None):
            if profile.site:
                site_pks == [request.user.profile.site.pk]
    request.GET['site_pks'] = list(site_pks)
    return Site.objects.filter(pk__in=site_pks)

@login_required
def get_single_site_pk_from_request(request):  
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

@login_required
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
    

from django.core.mail import send_mail
from django.shortcuts import redirect, render
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
                subject='Winser Systems Prod - 500 error ',
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
        site = Site.objects.filter(pk=site_pk).first()
        if site:  
            if get_profile_allowed_to_change_subscription(request.user.profile, site):
                return super(SwitchSubscriptionBeginView, self).get(request, args, kwargs)

    def get_context_data(self):    
        context = super(SwitchSubscriptionBeginView, self).get_context_data()
        site_pk = self.request.GET.get('site_pk')
        site = Site.objects.get(pk=site_pk)
        switch_subscription = Subscription.objects.get(numerical=self.request.GET.get('numerical'))
        
        SiteSubscriptionChange.objects.filter(subscription_to=switch_subscription, subscription_from = site.subscription_new, site=site, canceled=None, completed=None).exclude(version_started=str(settings.VERSION)).update(canceled=datetime.now())
        existing_site_subscription_changes = SiteSubscriptionChange.objects.filter(version_started=str(settings.VERSION), subscription_to=switch_subscription, subscription_from = site.subscription_new, site=site, canceled=None, completed=None).order_by('created')
        if existing_site_subscription_changes:
            latest_existing_site_subscription_change = existing_site_subscription_changes.last()
            existing_site_subscription_changes.exclude(pk=latest_existing_site_subscription_change.pk).update(canceled=datetime.now())
        site_subscription_change, created = SiteSubscriptionChange.objects.get_or_create(
            version_started=str(settings.VERSION),
            subscription_to=switch_subscription, 
            subscription_from = site.subscription_new, 
            site=site, 
            canceled=None, 
            completed=None
        )
        context['site'] = site
        context['switch_subscription'] = switch_subscription
        context['site_subscription_change'] = site_subscription_change
        
        return context

@login_required
@check_core_profile_requirements_fulfilled
def choose_attached_profiles(request):
    site_subscription_change_pk = request.POST.get('site_subscription_change_pk')
    # del request.POST['site_subscription_change_pk']
    site_subscription_change = SiteSubscriptionChange.objects.get(pk=site_subscription_change_pk)
    user_pks = []
    for k,v in request.POST.items():
        if 'choose_profile_' in k and v == 'on':
            user_pks.append(k.replace('choose_profile_', ''))
    if len(user_pks) > site_subscription_change.subscription_to.max_profiles:
        return HttpResponse("Too many profiles chosen", status=400)

    site_subscription_change.users_to_keep.set(User.objects.filter(pk__in=user_pks, profile__company=site_subscription_change.site.company))
    site_subscription_change.stripe_session_id = f"{site_subscription_change.site.guid}_{str(datetime.timestamp(datetime.now()))}"
    site_subscription_change.save()
    # if site_subscription_change.subscription_to.whatsapp_enabled:
    #     return render(request, 'templates/core/htmx/setup_payment.html', {'site_subscription_change':site_subscription_change})
    # else:
    
    
    
    try:
        stripe_customer = get_or_create_customer(site_subscription_change.site.stripecustomer.customer_id)
    except Site.stripecustomer.RelatedObjectDoesNotExist:
        stripe_customer = get_or_create_customer("")
    customer_id = stripe_customer['id']
    stripe_customer_object, created = StripeCustomer.objects.get_or_create(
        customer_id=customer_id
    )
    stripe_customer_object.json_data = stripe_customer
    stripe_customer_object.site = site_subscription_change.site
    stripe_customer_object.save()
    
    
    
    session = create_checkout_session(site_subscription_change.stripe_session_id, site_subscription_change.subscription_to.stripe_price_id, site_subscription_change.site.stripecustomer.customer_id)
    return HttpResponse(status=200,headers={'HX-Redirect':session.url})
    # temp = create_subscription(stripe_customer_object.customer_id, [site_subscription_change.subscription_to.stripe_price_id])
    # return render(request, 'core/htmx/setup_payment.html', {'site_subscription_change':site_subscription_change})

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class StripeSubscriptionsSummaryView(TemplateView):
    template_name='core/stripe_subscriptions_summary.html'

    def get(self, request, *args, **kwargs):   
        # site = Site.objects.get(pk=site_pk) 
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/stripe_subscriptions_summary_htmx.html'
        return super(StripeSubscriptionsSummaryView, self).get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True   
        context = {}
        site_pk = get_single_site_pk_from_request(self.request)   
        self.request.GET['site_pk'] = site_pk   
        site = Site.objects.get(pk=site_pk)     

        # permissions
        context['permitted'] = False
        if get_profile_allowed_to_view_site_configuration(self.request.user.profile, site):
            context['permitted'] = True
        # end permissions
        
        context['site'] = site
        context['stripe_subscriptions'] = list_subscriptions(site.stripecustomer.customer_id)
        return context
    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class StripeSubscriptionCanceledView(TemplateView):
    template_name='core/stripe_subscription_canceled.html'

    def get_context_data(self, **kwargs):
        context = super(StripeSubscriptionCanceledView, self).get_context_data(**kwargs)       
        return context


    