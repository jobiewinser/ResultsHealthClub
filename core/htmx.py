#0.9 safe
import os
from calendly.api import Calendly
from core.models import ROLE_CHOICES, Profile, Site, WhatsappNumber, SiteProfilePermissions, CompanyProfilePermissions, Subscription, SiteContact
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from core.user_permission_functions import get_profile_allowed_to_edit_other_profile, get_profile_allowed_to_edit_site_configuration 
from core.views import get_site_pks_from_request_and_return_sites
from campaign_leads.models import Campaignlead
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from core.core_decorators import *
logger = logging.getLogger(__name__)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        context["sites"] = get_site_pks_from_request_and_return_sites(request)
        if request.user.is_authenticated:
            site_pk = request.GET.get('site_pk', None)
            template_name = request.GET.get('template_name', '')
            # context = {'site_list':get_available_sites_for_user(request.user)}
            # if template_name == 'switch_user':
            #     context['users'] = User.objects.filter(is_authenticated=True).order_by('first_name')
            if template_name == 'edit_user':
                user_pk = request.GET.get('user_pk', None)
                if user_pk:
                    context["edit_user"] = User.objects.get(pk=user_pk)
            elif template_name == 'add_site':
                if site_pk:
                    context["site"] = request.user.profile.active_sites_allowed.get(pk=site_pk)     
                elif request.user.profile.company.part_created_site:
                    context["site"] = request.user.profile.company.part_created_site   
            elif template_name == 'edit_contact':
                site_contact_pk = request.GET.get('site_contact_pk')
                if site_contact_pk:
                    context["site_contact"] = SiteContact.objects.get(pk=site_contact_pk, site__in=request.user.profile.active_sites_allowed)
                if site_pk:
                    context["site"] = request.user.profile.active_sites_allowed.get(pk=site_pk)     
                    
            elif template_name == 'edit_permissions':
                profile_pk = request.GET.get('profile_pk', None)
                if profile_pk:
                    profile = Profile.objects.get(pk=profile_pk)
                    context["profile"] = profile
                    company_profile_permissions, created = CompanyProfilePermissions.objects.get_or_create(profile=profile, company=profile.company)
                    company_profile_permissions.save()
                    for site in profile.company.active_sites:
                        site_profile_permissions, created = SiteProfilePermissions.objects.get_or_create(profile=profile, site=site)
                        site_profile_permissions.save()
            elif template_name == 'add_user':
                context['role_choices'] = ROLE_CHOICES    
                if site_pk:
                    context["site"] = request.user.profile.active_sites_allowed.get(pk=site_pk) 
            elif template_name == 'reactivate_user':
                if site_pk:
                    context["site"] = request.user.profile.active_sites_allowed.get(pk=site_pk)   
            elif template_name == 'choose_template_message_site_contact':
                site = request.user.profile.active_sites_allowed.get(pk=site_pk)   
                context["site"] = site
                context["site_contacts"] = SiteContact.objects.filter(site=site)   
                             
            elif template_name == 'send_new_template_message':
                
                whatsappnumber_pk = request.GET.get('whatsappnumber_pk', None)
                
                if whatsappnumber_pk:
                    whatsappnumber = WhatsappNumber.objects.get(pk=whatsappnumber_pk, whatsapp_business_account__active=True)
                else:
                    lead_pk = request.GET.get('lead_pk') 
                    # latest_message = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber__whatsapp_business_account__site=site).order_by('datetime').last()
                    # if latest_message:
                    #     whatsappnumber = latest_message.whatsappnumber
                    # else:
                    if lead_pk:
                        lead = Campaignlead.objects.get(pk=lead_pk)
                    else:
                        customer_number = request.GET.get('customer_number') 
                        site = Site.objects.filter(pk=request.GET.get('site_pk')).exclude(active=False).first()                        
                        lead = Campaignlead.objects.filter(campaign__site=site, contact__customer_number=customer_number).last()
                        context['customer_numbers'] = [customer_number]   
                    if not lead.campaign.whatsapp_business_account:
                        return HttpResponse("You don't have a whatsapp number linked to this campaign!", status="400")
                    context['lead'] = lead
                    whatsappnumber = lead.campaign.whatsapp_business_account.whatsappnumber
                context['whatsappnumber'] = whatsappnumber
                 
                # context['site'] = context['whatsappnumber'].whatsapp_business_account.site
                # lead_pk = request.GET.get('lead_pk', None)
                site_contact_pk = request.GET.get('site_contact_pk', None)
                customer_number = request.GET.get('customer_number', None)                
                # if lead_pk:
                #     context['lead'] = Campaignlead.objects.filter(pk=lead_pk).first()
                if site_contact_pk:
                    context['site_contact'] = SiteContact.objects.filter(pk=site_contact_pk).first()
                if customer_number:
                    context['customer_number'] = customer_number
            # elif template_name == 'change_default_payment_method':
            #     context["site"] = Site.objects.get(pk=site_pk)     
            #     context['switch_subscription'] = Subscription.objects.filter(numerical=request.GET.get('switch_subscription')).first()
                    
            
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@method_decorator(login_required, name="dispatch")
@method_decorator(check_core_profile_requirements_fulfilled, name='post')
class ModifyUser(View):
    def post(self, request, **kwargs):
        try:
            action = request.POST.get('action', '')
            if action == 'add':
                site = request.user.profile.active_sites_allowed.get(pk=request.POST.get('site_pk', ''))
                if site.subscription.max_profiles:
                    if site.users.count() >= site.subscription.max_profiles:
                        return HttpResponse("You already have the maximum number of users", status=400)
                username = request.POST.get('username', '')[:25]
                first_name = request.POST.get('first_name', '')[:25]
                last_name = request.POST.get('last_name', '')[:25]
                password = request.POST.get('password', '')
                role = request.POST.get('role', '')
                calendly_event_page_url = request.POST.get('calendly_event_page_url', '')
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
                if not role or request.user.profile.role == 'c':
                    return HttpResponse(f"Please enter a Role with lower permissions than yourself {str(request.user.profile.get_role_display)}", status=400)
                profile_picture = request.FILES.get('profile_picture')
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
                                        calendly_event_page_url = calendly_event_page_url, 
                                        site = site)
            elif action == 'edit':       
                user = User.objects.get(pk=request.POST['user_pk'])   
                profile = Profile.objects.get_or_create(user = user)[0] 
                user.profile = profile     
                if get_profile_allowed_to_edit_other_profile(request.user.profile, user.profile):
                    first_name = request.POST.get('first_name', '')[:25]
                    last_name = request.POST.get('last_name', '')[:25]
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
@not_demo_or_superuser_check
def create_calendly_webhook_subscription(request, **kwargs):
    site = Site.objects.get(pk=request.POST.get('site_pk')) 
    if get_profile_allowed_to_edit_site_configuration(request.user.profile, site): 
        if site.calendly_organization and site.calendly_token:
            calendly = Calendly(site.calendly_token)
            print("calendly", calendly)
            calendly_webhooks = calendly.list_webhook_subscriptions(organization = site.calendly_organization).get('collection')
            print("calendly_webhooks", site)
            if calendly_webhooks == None:
                # if site.subscription.max_profiles:
                    # if site.users.count() >= site.subscription.max_profiles:
                return HttpResponse("Invalid Calendly details", status=400)
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
        return HttpResponse("Your Calendly settings are not submitted yet", status=400)
    return render(request, "core/htmx/calendly_webhook_status_wrapper.html", {'site':site, 'site_webhook_active':(response.get('resource',{}).get('state')=='active')})
    
@login_required
@not_demo_or_superuser_check
def delete_calendly_webhook_subscription(request, **kwargs):
    site = Site.objects.get(pk=request.POST.get('site_pk'))    
    if get_profile_allowed_to_edit_site_configuration(request.user.profile, site): 
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
@not_demo_or_superuser_check
def add_site(request, **kwargs):
    site_pk = request.POST.get('site_pk')
    name = request.POST.get('name')
    sign_up_subscription = Subscription.objects.get(pk=request.POST.get('subscription'))
    profile = request.user.profile
    if not sign_up_subscription.stripe_price_id and profile.company.free_sites.exists():
        return HttpResponse("You already have a free site within your company (max 1). Please purchase a subscription for that site or this new one to continue.", status=400)
    if request.user.profile.role == 'a' and name and sign_up_subscription:
        if site_pk:
            site = Site.objects.get(pk=site_pk)
        else:
            if request.user.profile.company.part_created_site:
                return HttpResponse("Another site is being added (potentially by another user within your company)", status=400)
            site = Site(
                company = request.user.profile.company,
                active = False,
                billing_email = request.user.email,
            )
        site.name = name
        site.sign_up_subscription = sign_up_subscription
        
        if site.sign_up_subscription.stripe_price_id: #do we need to move to the next stage of setting up payment?
            site.save()
            profile.sites_allowed.add(site)
            profile.save()
            return render(request, "campaign_leads/htmx/new_site_payment_methods.html", {'site':site})
        else: #or can we just create the new site!
            site.active = True
            site.subscription = sign_up_subscription
            site.sign_up_subscription = None
            site.save()
            profile.sites_allowed.add(site)
            profile.save()
            response = HttpResponse( status=200)
            response["HX-Redirect"] = f"/configuration/site-configuration/?site_pk={site.pk}"
            return response
            
    return HttpResponse("This feature requires a Pro subscription", status=403)

# @login_required
# def generate_free_taster_link(request, **kwargs):
#     if settings.DEMO and not request.user.is_superuser:
#         return HttpResponse(status=500)
#     try:
#         if request.user.is_authenticated:
#             customer_name = request.POST.get('customer_name', '')
#             site_pk = request.POST.get('site_pk','')
#             if customer_name:
#                 guid = str(uuid.uuid4())[:8]
#                 while FreeTasterLink.objects.filter(guid=guid):
#                     guid = str(uuid.uuid4())[:8]
#                 generated_link = FreeTasterLink.objects.create(customer_name=customer_name, user=request.user, guid=guid, site=Site.objects.get(pk=site_pk))
#                 return render(request, f"core/htmx/generated_link_display.html", {'generated_link':generated_link})  
#     except Exception as e:
#         logger.debug("generate_free_taster_link Error "+str(e))
#         #return HttpResponse(e, status=500)
#         raise e


# @login_required
# def delete_free_taster_link(request, **kwargs):
#     if settings.DEMO and not request.user.is_superuser:
#         return HttpResponse(status=500)
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             link_pk = request.POST.get('link_pk','')
#             if link_pk:
#                 FreeTasterLink.objects.get(pk=link_pk).delete()
#             return HttpResponse( "text", 200)
#     except Exception as e:
#         logger.debug("delete_free_taster_link Error "+str(e))
#         #return HttpResponse(e, status=500)
#         raise e


        