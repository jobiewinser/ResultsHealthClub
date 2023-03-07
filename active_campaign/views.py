import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaignlead
from active_campaign.models import ActiveCampaignWebhookRequest, ActiveCampaign, Campaign
from core.models import Site
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from core.core_decorators import *
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta, time
from core.models import Company
from core.user_permission_functions import *
from active_campaign.api import ActiveCampaignApi
from core.utils import normalize_phone_number
from core.views import get_and_create_contact_and_site_contact_for_lead, get_company_configuration_context
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        return HttpResponse( "text", 200)

    def post(self, request, *args, **kwargs): 
        # try:
            logger.debug(str(request.POST))     
            data = request.POST  
            guid = kwargs.get('guid')
            if not data.get('initiated_by') == 'admin':
                ActiveCampaignWebhookRequest.objects.create(json_data = data, meta_data = str(request.META), guid=guid)       
                if data.get('type') in ['subscribe','update']:
                    if guid:
                        campaign = ActiveCampaign.objects.get(guid=guid)
                        if campaign.site:
                            if campaign.site.active_campaign_leads_enabled:
                                phone_number_whole = normalize_phone_number(str(data.get('contact[phone]', "")))
                                if not Campaignlead.objects.filter(
                                        active_campaign_contact_id=data.get('contact[id]'),
                                        campaign=campaign,
                                    ).exclude(archived=True).exclude(sale__archived=False):                                    
                                    campaign_lead, created = Campaignlead.objects.get_or_create(
                                            active_campaign_contact_id=data.get('contact[id]'),
                                            campaign=campaign,
                                        )
                                    campaign_lead.first_name=data.get('contact[first_name]', "None")
                                    campaign_lead.active_campaign_form_id = data.get('form[id]', None)
                                    campaign_lead.email = data.get('contact[email]', "")
                                    
                                    if not campaign.site.subscription.whatsapp_enabled:
                                        campaign_lead.disabled_automated_messaging = True
                                    campaign_lead.save()
                                    get_and_create_contact_and_site_contact_for_lead(campaign_lead, phone_number_whole)
                                    campaign_lead.check_if_should_send_first_message()
                                    campaign_lead.trigger_refresh_websocket(refresh_position=True)
                                    campaign_lead.contact.company.get_company_cache().clear()
            return HttpResponse( "text", 200)
     
logger = logging.getLogger(__name__)
    

@login_required
def set_campaign_site(request, **kwargs):
    try:
        campaign = Campaign.objects.get(pk=kwargs.get('campaign_pk'))
        site_pk = request.POST.get('site_pk',None)
        campaign.campaigntemplatelink_set.all().delete()

        if site_pk:
            site = request.user.profile.active_sites_allowed.get(pk=site_pk)
            campaign.site = site
        else:
            campaign.site = None
        campaign.save()
        return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign,})
    except Exception as e:        
        logger.error(f"set_campaign_site {str(e)}")
        return HttpResponse("Couldn't set Campaign Site", status=500)

@login_required
def set_whatsapp_template_sending_status(request, **kwargs):
    try:
        site = request.user.profile.active_sites_allowed.get(pk=request.POST.get('site_pk',None))
        if get_profile_allowed_to_toggle_whatsapp_sending(request.user.profile, site):
            site.whatsapp_template_sending_enabled = request.POST.get('whatsapp_template_sending_enabled', 'off') == 'on'
            site.save()
            return render(request, 'core/htmx/whatsapp_template_sending_enabled_htmx.html', {'site':site,'site_warning_section_swap':True})
        return HttpResponse(status=403)
    except Exception as e:        
        logger.error(f"set_whatsapp_template_sending_status {str(e)}")
        return HttpResponse("Couldn't set_whatsapp_template_sending_status", status=500)

@login_required
def set_active_campaign_leads_status(request, **kwargs):
    try:
        site = request.user.profile.active_sites_allowed.get(pk=request.POST.get('site_pk',None))
        if get_profile_allowed_to_toggle_active_campaign(request.user.profile, site):
            site.active_campaign_leads_enabled = request.POST.get('active_campaign_leads_enabled', 'off') == 'on'
            site.save()
            return render(request, 'core/htmx/active_campaign_enabled_htmx.html', {'site':site,'site_warning_section_swap':True})
        return HttpResponse(status=403)
    except Exception as e:        
        logger.error(f"set_active_campaign_leads_status {str(e)}")
        return HttpResponse("Couldn't set_active_campaign_leads_status", status=500)

@login_required
def import_active_campaign_leads(request, **kwargs):
    try:
        successful_import = False
        active_campaign_contact_id_list = request.POST.getlist('active_campaign_contact_id[]')
        active_campaign_api = ActiveCampaignApi(request.user.profile.company.active_campaign_api_key, request.user.profile.company.active_campaign_url)
        if active_campaign_contact_id_list:
            contacts = active_campaign_api.list_contacts_by_id_list(active_campaign_contact_id_list)
            campaign = ActiveCampaign.objects.get(pk=request.POST.get('campaign_pk'))
            disabled_automated_messaging = request.POST.get('disabled_automated_messaging', 'false') == 'true'
            for contact in contacts:
                if not Campaignlead.objects.filter(active_campaign_contact_id=contact['id'], campaign=campaign).exclude(archived=True).exclude(sale__archived=False):
                    lead = Campaignlead()
                    lead.active_campaign_contact_id = contact['id']
                    refresh_position = True
                    lead.campaign = campaign
                    lead.first_name = contact.get('firstName')
                    lead.last_name = contact.get('lastName')
                    lead.email = contact.get('email')
                    lead.disabled_automated_messaging = disabled_automated_messaging
                    if not campaign.site.subscription.whatsapp_enabled:
                        lead.disabled_automated_messaging = True
                    lead.save()
                    get_and_create_contact_and_site_contact_for_lead(lead, contact.get('phone'))
                    lead.check_if_should_send_first_message()
                    lead.trigger_refresh_websocket(refresh_position=refresh_position)
                    successful_import = True
                    request.user.profile.company.get_company_cache().clear()
        if successful_import:
            return HttpResponse("Successfully import contacts", status=200)
        return HttpResponse("No valid contacts selected", status=400)
    except Exception as e:        
        logger.error(f"import_active_campaign_leads {str(e)}")
        return HttpResponse("Couldn't import_active_campaign_leads", status=500)
    
    
@login_required
@not_demo_or_superuser_check
def set_active_campaign_company_config(request, **kwargs):
    try:
        context = {}
        company = Company.objects.get(pk=request.POST.get('company_pk',None))
        if not get_profile_allowed_to_edit_active_campaign_settings(request.user.profile, company):
            return HttpResponse("You need the edit Active Campaign permission", status=403)
        active_campaign_url = request.POST.get('active_campaign_url', '*')
        active_campaign_api_key = request.POST.get('active_campaign_api_key', '*')
        if active_campaign_url.replace('*', ''):
            company.active_campaign_url = active_campaign_url
        if active_campaign_api_key.replace('*', ''):
            company.active_campaign_api_key = active_campaign_api_key        
        company.save()
        active_campaign = ActiveCampaignApi(company.active_campaign_api_key, company.active_campaign_url)
        
        context.update(get_company_configuration_context(request))
        context['company'] = company
        context['hx_swap_oob'] = True
        active_campaign = ActiveCampaignApi(request.user.profile.company.active_campaign_api_key, request.user.profile.company.active_campaign_url)
        context['webhooks'] = active_campaign.get_webhooks(request.user.profile.company.active_campaign_url)
        
        return render(request, 'core/htmx/active_campaign_company_config_row.html', context)
    except Exception as e:        
        logger.error(f"set_active_campaign_template_sending_status {str(e)}")
        return HttpResponse("Couldn't set Active Campaign configuration", status=500)
