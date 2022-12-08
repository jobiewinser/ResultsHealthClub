import os
import sys
import traceback
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from calendly.api import Calendly
from core.core_decorators import check_core_profile_requirements_fulfilled
from core.models import ROLE_CHOICES, Company, FreeTasterLink, FreeTasterLinkClick, Profile, Site  
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from core.user_permission_functions import *
from whatsapp.api import Whatsapp
from core.startup import run_debug_startup
logger = logging.getLogger(__name__)

run_debug_startup()

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
    


class ChangeLogView(TemplateView):
    template_name='core/change_log.html'
    def get(self, request, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/change_log_htmx.html'
        return super().get(request, *args, **kwargs)
class CustomerLoginView(TemplateView):
    template_name='core/customer_login.html'
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super(CustomerLoginView, self).get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super(CustomerLoginView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'registration/login.html'
        return context
    
PROFILE_ERROR_OPTIONS = {
    '1':"No profile set up for your user account.",
    '2':"No company assigned to your profile (please contact: <a href='mailto:jobiewinser@gmail.com'>jobiewinser@gmail.com</a> or <a href='tel:+447872000364'>+44 7872 000364</a>).",
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
            if not self.request.user.profile.sites_allowed.all():
                errors.append(PROFILE_ERROR_OPTIONS['3'])
            if not self.request.user.profile.site:
                errors.append(PROFILE_ERROR_OPTIONS['4'])
        context['errors'] = errors
        return context

@method_decorator(login_required, name='dispatch')
class SitePermissionsView(TemplateView):
    template_name='campaign_leads/htmx/site_permissions.html'

    def get_context_data(self, **kwargs):
        context = super(SitePermissionsView, self).get_context_data(**kwargs)       
        site = Site.objects.get(pk=self.request.GET.get('site_pk'))
        # context['site'] = Site.objects.get(pk=self.request.GET.get('site_pk'))
        context['permissions'] = SiteProfilePermissions.objects.get(profile=self.request.user.profile, site=site)
        return context
    def post(self, request):
        permissions = SiteProfilePermissions.objects.get(pk = request.POST.get('permissions_pk'))
        context = {'permissions':permissions}
        if get_user_allowed_to_edit_other_user_permissions(request.user.profile, permissions.site):
            if request.user.profile.role == 'a' or (request.user.profile.role == 'b' and permissions.profile.role == 'c'):      
                for key in ['view_site_configuration',
                            'edit_site_configuration',
                            'edit_whatsapp_settings',
                            'toggle_active_campaign',
                            'edit_user_permissions',] :

                    setattr(permissions, key, request.POST.get(key, False))
                permissions.save()
                return render(request, 'campaign_leads/htmx/site_permissions.html', context)
        context['error'] = "You do not have permission to do this"
        return render(request, 'campaign_leads/htmx/site_permissions.html', context)

@method_decorator(login_required, name='dispatch')
class SiteConfigurationView(TemplateView):
    template_name='core/site_configuration.html'

    def get(self, request, *args, **kwargs):
        request.GET._mutable = True   
        site_pk = get_site_pk_from_request(request)
        request.GET['site_pk'] = site_pk      
        site = Site.objects.get(pk=site_pk) 

        # permissions
        if get_user_allowed_to_view_site_configuration(request.user.profile, site):
            return super(SiteConfigurationView, self).get(request, args, kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            return HttpResponse("You don't have permission to access this page")
        raise PermissionDenied()
        # endpermissions

    def get_context_data(self, **kwargs):    
        context = super(SiteConfigurationView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/site_configuration_htmx.html'
        site = Site.objects.get(pk=self.request.GET['site_pk'])     
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
        # context['user_allowed_to_edit_site_configuration'] = get_user_allowed_to_edit_site_configuration(self.request.user.profile, site)
        # context['user_allowed_to_edit_whatsapp_settings'] = get_user_allowed_to_edit_whatsapp_settings(self.request.user.profile, site)
        # context['user_allowed_to_toggle_active_campaign'] = get_user_allowed_to_toggle_active_campaign(self.request.user.profile, site)
        
        return context
    def post(self, request):
        self.request.POST._mutable = True 
        site = Site.objects.get(pk=request.POST.get('site_pk'))   

        # permissions
        if not get_user_allowed_to_edit_site_configuration(request.user.profile, site):
            if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                return HttpResponse("You don't have permission to edit this")
            raise PermissionDenied()
        # endpermissions


        response_text = ""     
        if 'name' in request.POST:
            site.name = request.POST['name']
            response_text = f"{response_text} <span hx-swap-oob='innerHTML:.name_display_{site.pk}'>{site.name}</span>"
            
        if 'calendly_organization' in request.POST:
            site.calendly_organization = request.POST['calendly_organization']
            response_text = f"""{response_text} 
                <span hx-swap-oob='innerHTML:#calendly_webhook_status_wrapper'><br><div class="mt-3"><b>Organization changed, please refresh page</b></div></span>"""
            
        if 'calendly_token' in request.POST:
            site.calendly_token = request.POST['calendly_token']
            response_text = f"""{response_text} 
                <span hx-swap-oob='innerHTML:#calendly_webhook_status_wrapper'><br><div class="mt-3"><b>Organization changed, please refresh page</b></div></span>"""
            
        site.save()
        return HttpResponse(response_text, status=200)

@method_decorator(login_required, name='dispatch')
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
        
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        return context
@login_required
def change_profile_role(request):
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if (not request.user == profile.user and get_user_allowed_to_edit_other_user(request.user, profile.user)):
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
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if get_user_allowed_to_edit_other_user(request.user, profile.user):
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
def change_profile_sites_allowed(request):
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if get_user_allowed_to_edit_other_user(request.user, profile.user):
        sites_allowed = request.POST.getlist('sites_allowed', None)
        if sites_allowed:
            context = {}
            profile.sites_allowed.set(Site.objects.filter(pk__in=sites_allowed))
            profile.save()
            context['profile'] = profile
            context['role_choices'] = ROLE_CHOICES
        return render(request, 'core/htmx/company_configuration_row.html', context)
    return HttpResponse("You are not allowed to edit this, please contact your manager.",status=500)


class CampaignLeadsProductPageView(TemplateView):
    template_name='core/campaign_leads_product_page.html'



def custom_login_post(request):    
    user = authenticate(username=request.POST.get('username', ''), email=request.POST.get('email', ''), password=request.POST.get('password', ''))
    if user:
        login(request, user)
        return HttpResponse(status=200)
    return HttpResponse("Account not found", status=404)

@method_decorator(login_required, name='dispatch')
class FreeTasterOverviewView(TemplateView):
    template_name='core/free_taster_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True       
        context = super(FreeTasterOverviewView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/free_taster_table_htmx.html'
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        free_taster_links = FreeTasterLink.objects.all()

        site_pk = get_site_pk_from_request(self.request)
        if site_pk:
            free_taster_links = free_taster_links.filter(site__pk=site_pk)
            self.request.GET['site_pk'] = site_pk                    
        context['free_taster_links'] = free_taster_links

        return context
        
        
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
def get_site_pk_from_request(request):  
    if request.method == 'GET':
        request_dict = request.GET
    elif request.method == 'POST':
        request_dict = request.POST
    site_pk = request_dict.get('site_pk', None)
    if site_pk:
        return site_pk
    profiles = Profile.objects.filter(user=request.user)
    if profiles:
        if profiles.first().site:
            return request.user.profile.site.pk
    

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