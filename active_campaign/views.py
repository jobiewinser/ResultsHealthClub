import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaign, Campaignlead
from campaign_leads.views import get_campaign_qs
from core.user_permission_functions import get_available_sites_for_user
from core.views import get_site_pk_from_request
from active_campaign.api import ActiveCampaignApi
from active_campaign.models import ActiveCampaignWebhookRequest, ActiveCampaign
from core.models import Site
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta, time
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        return HttpResponse("", "text", 200)

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
                            phone_number_whole = str(data.get('contact[phone]', "")).replace(' ','').replace('+','')

                            possible_duplicate  = False
                            today = datetime.now().date()
                            tomorrow = today + timedelta(1)
                            today_start = datetime.combine(today, time())
                            today_end = datetime.combine(tomorrow, time())
                            if Campaignlead.objects.filter(
                                    campaign=campaign,
                                    active_campaign_contact_id=data.get('contact[id]')
                                ) or  Campaignlead.objects.filter(
                                    campaign=campaign,
                                    whatsapp_number=phone_number_whole,
                                    created__lte=today_end, 
                                    created__gte=today_start, 
                                ): 
                                possible_duplicate  = True
                            if not possible_duplicate:
                                lead = Campaignlead.objects.create(
                                    active_campaign_contact_id=data.get('contact[id]'),
                                    first_name=data.get('contact[first_name]', "None"),
                                    whatsapp_number=phone_number_whole,
                                    campaign=campaign,
                                    active_campaign_form_id=data.get('form[id]', None),
                                    possible_duplicate = possible_duplicate,
                                    email = data.get('contact[email]', "")
                                )
                                lead.trigger_refresh_websocket()
            return HttpResponse("", "text", 200)
     
logger = logging.getLogger(__name__)
    

@login_required
def set_campaign_site(request, **kwargs):
    try:
        campaign = Campaign.objects.get(pk=kwargs.get('campaign_pk'))
        site_pk = request.POST.get('site_pk',None)
        campaign.first_send_template = None
        campaign.second_send_template = None
        campaign.third_send_template = None

        if site_pk:
            site = Site.objects.get(pk=site_pk)
            campaign.site = site
        else:
            campaign.site = None
        campaign.save()
        return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign,})
                                                                                # 'site_list': get_available_sites_for_user(request.user)})
    except Exception as e:        
        logger.error(f"set_campaign_site {str(e)}")
        return HttpResponse("Couldn't set Campaign Site", status=500)

@login_required
def set_active_campaign_sending_status(request, **kwargs):
    try:
        site = Site.objects.get(pk=request.POST.get('site_pk',None))
        site.template_sending_enabled = request.POST.get('template_sending_enabled', 'off') == 'on'
        site.save()
        return render(request, 'core/htmx/active_campaign_lead_sending_enabled_htmx.html', {'site':site,})
                                                                                # 'site_list': get_available_sites_for_user(request.user)})
    except Exception as e:        
        logger.error(f"set_active_campaign_sending_status {str(e)}")
        return HttpResponse("Couldn't set_active_campaign_sending_status", status=500)

