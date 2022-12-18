import json
import os
import uuid
from calendly.api import Calendly
from core.models import ROLE_CHOICES, FreeTasterLink, Profile, Site, WhatsappNumber, Contact, Company, SiteProfilePermissions, CompanyProfilePermissions
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from core.user_permission_functions import get_available_sites_for_user, get_profile_allowed_to_edit_other_profile, get_user_allowed_to_edit_site_configuration 
from core.views import get_site_pk_from_request
from django.http import QueryDict
from campaign_leads.models import Campaignlead
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
logger = logging.getLogger(__name__)


@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
            context["site"] = Site.objects.get(pk=site_pk)
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            # context = {'site_list':get_available_sites_for_user(request.user)}
            # if template_name == 'switch_user':
            #     context['users'] = User.objects.filter(is_authenticated=True).order_by('first_name')
            if template_name == 'edit_user':
                user_pk = request.GET.get('user_pk', None)
                if user_pk:
                    context["edit_user"] = User.objects.get(pk=user_pk)
            elif template_name == 'edit_permissions':
                profile_pk = request.GET.get('profile_pk', None)
                if profile_pk:
                    profile = Profile.objects.get(pk=profile_pk)
                    context["profile"] = profile
                    CompanyProfilePermissions.objects.get_or_create(profile=profile, company=profile.company)
                    for site in profile.company.active_sites:
                        SiteProfilePermissions.objects.get_or_create(profile=profile, site=site)
            elif template_name == 'add_phone_number':
                site_pk = request.GET.get('site_pk', None)
                if site_pk:
                    context["site"] = Site.objects.get(pk=site_pk)
            elif template_name == 'add_user':
                context['role_choices'] = ROLE_CHOICES                 
            elif template_name == 'send_new_template_message':
                whatsappnumber_pk = request.GET.get('whatsappnumber_pk', None)
                context['whatsappnumber'] = WhatsappNumber.objects.get(pk=whatsappnumber_pk)
                # context['site'] = context['whatsappnumber'].whatsapp_business_account.site
                lead_pk = request.GET.get('lead_pk', None)
                contact_pk = request.GET.get('contact_pk', None)
                customer_number = request.GET.get('customer_number', None)                
                if lead_pk:
                    context['lead'] = Campaignlead.objects.filter(pk=lead_pk).first()
                if contact_pk:
                    context['contact'] = Contact.objects.filter(pk=contact_pk).first()
                if customer_number:
                    context['customer_number'] = customer_number
                    
            
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@method_decorator(login_required, name="dispatch")
class ModifyUser(View):
    def post(self, request, **kwargs):
        if settings.DEMO and not request.user.is_superuser:
            return HttpResponse(status=500)
        try:
            action = request.POST.get('action', '')
            if action == 'add':
                username = request.POST.get('username', '')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password = request.POST.get('password', '')
                role = request.POST.get('role', '')
                if not first_name:
                    return HttpResponse("Please enter a First Name", status=400)
                if not password:
                    return HttpResponse("Please enter a Password", status=400)
                try:
                    validate_password(password)
                    # if 'passw0rd' in password.lower():
                    #     raise ValidationError("The word password is not allowed as a password")
                except ValidationError as e:
                    return HttpResponse(e, status=400)
                if not role:
                    return HttpResponse("Please enter a Role", status=400)
                profile_picture = request.FILES.get('profile_picture')
                site = Site.objects.get(pk=request.POST.get('site_pk', ''))
                # calendly_event_page_url = request.POST.get('calendly_event_page_url', '')
                if not username:
                    username = f"{first_name}{last_name}"
                    index = 0
                    while User.objects.filter(username=username):
                        index = index + 1
                        username = f"{first_name}{last_name}_{index}"
                if User.objects.filter(username=username):
                    return HttpResponse("Username already taken", status=400)
                user = User.objects.create(username=username, 
                                            first_name=first_name,
                                            last_name=last_name)
                user.set_password(password)
                user.save()
                Profile.objects.create(user = user, 
                                        avatar = profile_picture, 
                                        company = request.user.profile.company, 
                                        role = role, 
                                        site = site)
            elif action == 'edit':       
                user = User.objects.get(pk=request.POST['user_pk'])   
                profile = Profile.objects.get_or_create(user = user)[0] 
                user.profile = profile     
                if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile):
                    first_name = request.POST.get('first_name', '')
                    last_name = request.POST.get('last_name', '')
                    site_pk = request.POST.get('site_pk', '')
                    calendly_event_page_url = request.POST.get('calendly_event_page_url', '')
                    # user.username=f"{first_name}{last_name}" 
                    user.first_name=first_name
                    user.last_name=last_name
                    user.save()

                    profile_picture = request.FILES.get('profile_picture', None)
                    if profile_picture:
                        profile.avatar = profile_picture
                    if site_pk:
                        profile.site=Site.objects.get(pk=site_pk)
                    profile.calendly_event_page_url = calendly_event_page_url
                    profile.save()   
                else:
                    return HttpResponse("You do not have permission to do this", status=500)
            context = {}
            context['user'] = user
            context['role_choices'] = ROLE_CHOICES
            # context['site_list'] = get_available_sites_for_user(request.user)
            return render(request, "core/htmx/company_configuration_row.html", context)   
        except Exception as e:
            logger.debug("ModifyUser Post Error "+str(e))
            #return HttpResponse(e, status=500)
            raise e
@login_required
def create_calendly_webhook_subscription(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    site = Site.objects.get(pk=request.POST.get('site_pk')) 
    if get_user_allowed_to_edit_site_configuration(request.user.profile, site): 
        calendly = Calendly(site.calendly_token)
        print("calendly", calendly)
        calendly_webhooks = calendly.list_webhook_subscriptions(organization = site.calendly_organization).get('collection')
        print("calendly_webhooks", site)
        for webhook in calendly_webhooks:
            if webhook.get('state') == 'active' \
            and webhook.get('callback_url') == f"{os.getenv('SITE_URL')}/calendly-webhooks/{site.guid}/" \
            and webhook.get('organization') == f"{os.getenv('CALENDLY_URL')}/organizations/{site.calendly_organization}":
                active_webhook_uuid = webhook.get('uri').replace(f"{os.getenv('CALENDLY_URL')}/webhook_subscriptions/", "")
                calendly.delete_webhook_subscriptions(webhook_guuid = active_webhook_uuid)
        print("site.guid", site.guid)
        print("site.calendly_organization", site.calendly_organization)
        response = calendly.create_webhook_subscription(site.guid, organization = site.calendly_organization)
        print("create_calendly_webhook_subscription response", response)
    return render(request, "core/htmx/calendly_webhook_status_wrapper.html", {'site':site, 'site_webhook_active':(response.get('resource',{}).get('state')=='active')})
    
@login_required
def delete_calendly_webhook_subscription(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    site = Site.objects.get(pk=request.POST.get('site_pk'))    
    if get_user_allowed_to_edit_site_configuration(request.user.profile, site): 
        calendly = Calendly(site.calendly_token)
        calendly_webhooks = calendly.list_webhook_subscriptions(organization = site.calendly_organization).get('collection')
        for webhook in calendly_webhooks:
            if webhook.get('state') == 'active' \
            and webhook.get('callback_url') == f"{os.getenv('SITE_URL')}/calendly-webhooks/{site.guid}/" \
            and webhook.get('organization') == f"{os.getenv('CALENDLY_URL')}/organizations/{site.calendly_organization}":
                active_webhook_uuid = webhook.get('uri').replace(f"{os.getenv('CALENDLY_URL')}/webhook_subscriptions/", "")
                response = calendly.delete_webhook_subscriptions(webhook_guuid = active_webhook_uuid)
                break
    return render(request, "core/htmx/calendly_webhook_status_wrapper.html", {'site':site, 'site_webhook_active':False})

@login_required
def add_site(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    company = Company.objects.get(pk=request.POST.get('company_pk'))
    if not company.subscription == 'pro':
        site = Site.objects.create(
            name = "New Site",
            company = company,
        )

        response = HttpResponse( status=200)
        response["HX-Redirect"] = f"/site-configuration/?site_pk={site.pk}"
        return response
    return HttpResponse("This feature requires a Pro subscription", status=403)

@login_required
def generate_free_taster_link(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    try:
        if request.user.is_authenticated:
            customer_name = request.POST.get('customer_name', '')
            site_pk = request.POST.get('site_pk','')
            if customer_name:
                guid = str(uuid.uuid4())[:8]
                while FreeTasterLink.objects.filter(guid=guid):
                    guid = str(uuid.uuid4())[:8]
                generated_link = FreeTasterLink.objects.create(customer_name=customer_name, user=request.user, guid=guid, site=Site.objects.get(pk=site_pk))
                return render(request, f"core/htmx/generated_link_display.html", {'generated_link':generated_link})  
    except Exception as e:
        logger.debug("generate_free_taster_link Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@login_required
def delete_free_taster_link(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            link_pk = request.POST.get('link_pk','')
            if link_pk:
                FreeTasterLink.objects.get(pk=link_pk).delete()
            return HttpResponse( "text", 200)
    except Exception as e:
        logger.debug("delete_free_taster_link Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


        