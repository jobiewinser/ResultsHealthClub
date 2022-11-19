import json
import os
import uuid
from calendly.api import Calendly
from core.models import ROLE_CHOICES, FreeTasterLink, Profile, Site, WhatsappNumber, Contact
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from core.user_permission_functions import get_available_sites_for_user, get_user_allowed_to_edit_other_user, get_user_allowed_to_edit_site 
from core.views import get_site_pk_from_request
from django.http import QueryDict
from campaign_leads.models import Campaignlead
logger = logging.getLogger(__name__)

# @login_required
# def switch_user(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             user_pk = request.POST.get('user_pk')
#             if type(user_pk) == list:
#                 user_pk = user_pk[0]
#             logger.debug(f"TEST {str(user_pk)}")
#             login(request, User.objects.get(pk=user_pk))
#             return render(request, f"core/htmx/profile-nav-section.html", {})   
#     except Exception as e:
#         logger.debug("switch_user Error "+str(e))
#         return HttpResponse(e, status=500)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
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
                    context["profile"] = Profile.objects.get(pk=profile_pk)
            elif template_name == 'add_phone_number':
                site_pk = request.GET.get('site_pk', None)
                if site_pk:
                    context["site"] = Site.objects.get(pk=site_pk)
            elif template_name == 'send_new_template_message':
                whatsappnumber_pk = request.GET.get('whatsappnumber_pk', None)
                context['whatsappnumber'] = WhatsappNumber.objects.get(pk=whatsappnumber_pk)
                context['site'] = context['whatsappnumber'].whatsapp_business_account.site
                lead_pk = request.GET.get('lead_pk', None)
                contact_pk = request.GET.get('contact_pk', None)
                if lead_pk:
                    context['lead'] = Campaignlead.objects.filter(pk=lead_pk).first()
                if contact_pk:
                    context['contact'] = Contact.objects.filter(pk=contact_pk).first()
            
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)


@method_decorator(login_required, name="dispatch")
class ModifyUser(View):
    def post(self, request, **kwargs):
        try:
            action = request.POST.get('action', '')
            if action == 'add':
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password = request.POST.get('password', '')
                profile_picture = request.FILES.get('profile_picture')
                # site_pk = request.POST.get('site_pk', '')
                # calendly_event_page_url = request.POST.get('calendly_event_page_url', '')
                username = f"{first_name}{last_name}"
                index = 0
                while User.objects.filter(username=username):
                    index = index + 1
                    username = f"{first_name}{last_name}_{index}"
                user = User.objects.create(username=username, 
                                            first_name=first_name,
                                            last_name=last_name,
                                            password=password)
                Profile.objects.create(user = user, 
                                        avatar = profile_picture, 
                                        company = request.user.profile.company)
            elif action == 'edit':       
                user = User.objects.get(pk=request.POST['user_pk'])   
                profile = Profile.objects.get_or_create(user = user)[0] 
                user.profile = profile     
                if get_user_allowed_to_edit_other_user(request.user, user):
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
            return HttpResponse(e, status=500)
@login_required
def create_calendly_webhook_subscription(request, **kwargs):
    site = Site.objects.get(pk=request.POST.get('site_pk'))    
    if get_user_allowed_to_edit_site(request.user, site): 
        calendly = Calendly(site.calendly_token)
        calendly_webhooks = calendly.list_webhook_subscriptions(organization = site.calendly_organization).get('collection')
        for webhook in calendly_webhooks:
            if webhook.get('state') == 'active' \
            and webhook.get('callback_url') == f"{os.getenv('SITE_URL')}/calendly-webhooks/{site.guid}/" \
            and webhook.get('organization') == f"{os.getenv('CALENDLY_URL')}/organizations/{site.calendly_organization}":
                active_webhook_uuid = webhook.get('uri').replace(f"{os.getenv('CALENDLY_URL')}/webhook_subscriptions/", "")
                calendly.delete_webhook_subscriptions(webhook_guuid = active_webhook_uuid)
        response = calendly.create_webhook_subscription(site.guid, organization = site.calendly_organization)
        print("create_calendly_webhook_subscription response", response)
    return render(request, "core/htmx/calendly_webhook_status_wrapper.html", {'site':site, 'site_webhook_active':(response.get('resource',{}).get('state')=='active')})
    
@login_required
def delete_calendly_webhook_subscription(request, **kwargs):
    site = Site.objects.get(pk=request.POST.get('site_pk'))    
    if get_user_allowed_to_edit_site(request.user, site): 
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
def generate_free_taster_link(request, **kwargs):
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
        return HttpResponse(e, status=500)


@login_required
def delete_free_taster_link(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            link_pk = request.POST.get('link_pk','')
            if link_pk:
                FreeTasterLink.objects.get(pk=link_pk).delete()
            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("delete_free_taster_link Error "+str(e))
        return HttpResponse(e, status=500)


        