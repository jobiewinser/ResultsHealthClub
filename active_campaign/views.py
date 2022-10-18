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
            ActiveCampaignWebhookRequest.objects.create(json_data = data, guid=guid)       
            if data.get('type') in ['subscribe','update']:
                if guid:
                    active_campaign_list = ActiveCampaign.objects.get(guid=guid)
                    if active_campaign_list.site:
                        phone_number_whole = str(data.get('contact[phone]', "")).replace(' ','')
                        # phone_number_whole = str(data.get('contact[phone]', "")).replace('+','').replace(' ','')
                        # if phone_number_whole:
                        #     if phone_number_whole[0] == "0":
                        #         phone_number = phone_number_whole[1:]
                        #         country_code = "44"
                        #     elif phone_number_whole[:2] == "44":
                        #         phone_number = phone_number_whole[2:]
                        #         country_code = "44"
                        #     else:
                        #         phone_number = phone_number_whole
                        #         country_code = "44"
                        # else:
                        #     phone_number = "None"
                        #     country_code = "None"
                        possible_duplicate  = False
                        if Campaignlead.objects.filter(
                                active_campaign_list=active_campaign_list,
                                active_campaign_contact_id=data.get('contact[id]')
                            ): 
                            possible_duplicate  = True
                        if not possible_duplicate:
                            Campaignlead.objects.create(
                                active_campaign_contact_id=data.get('contact[id]'),
                                first_name=data.get('contact[first_name]', "None"),
                                whatsapp_number=phone_number_whole,
                                active_campaign_list=active_campaign_list,
                                active_campaign_form_id=data.get('form[id]', None),
                                possible_duplicate = possible_duplicate,
                                email = data.get('contact[email]', "")
                            )
            return HttpResponse("", "text", 200)
        # except Exception as e:     
        #     logger.error(f"Webhooks POST {str(e)}")     
        #     return HttpResponse(str(e), "text", 500)


# @login_required
# def get_campaigns(request):
#     # for campaign_dict in active_campaign.get_campaigns().get('campaigns',[]):
#     #     campaign = Campaign.objects.get_or_create(
#     #         active_campaign_id = campaign_dict.pop('id'),
#     #     )[0]
#     #     campaign.name = campaign_dict.pop('name')
#     #     campaign.status = campaign_dict.pop('status')
#     #     campaign.uniqueopens = int(campaign_dict.pop('uniqueopens'))
#     #     campaign.opens = int(campaign_dict.pop('opens'))
#     #     campaign.active_campaign_created = datetime.strptime(campaign_dict.pop('created_timestamp'), '%Y-%m-%d %H:%M:%S')
#     #     campaign.active_campaign_updated = datetime.strptime(campaign_dict.pop('updated_timestamp'), '%Y-%m-%d %H:%M:%S')
#     #     campaign.json_data = campaign_dict
#     #     campaign.save()
#     # temp = active_campaign.get_all_messages()
#     return render(request, f"active_campaign/htmx/campaigns_select.html", {'campaigns':Campaign.objects.all()})
    
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
        return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign,
                                                                                'site_list': get_available_sites_for_user(request.user)})
    except Exception as e:        
        logger.error(f"set_campaign_site {str(e)}")
        return HttpResponse("Couldn't set Campaign Site", status=500)

