import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaignlead
from core.views import get_site_pk_from_request
from active_campaign.api import ActiveCampaign
from active_campaign.models import CampaignWebhook, ActiveCampaignList
from core.models import Site
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import OuterRef, Subquery, Count
from django.conf import settings
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs): 
        try:
            logger.debug(str(request.POST))     
            data = request.POST  
            guid = kwargs.get('guid')
            CampaignWebhook.objects.create(json_data = data, guid=guid)       
            if data.get('type') in ['subscribe','update']:
                if guid:
                    active_campaign_list = ActiveCampaignList.objects.get(guid=guid)
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
                                whatsapp_number=f"whatsapp:+{phone_number_whole}",
                                active_campaign_list=active_campaign_list,
                                active_campaign_form_id=data.get('form[id]', None),
                                possible_duplicate = possible_duplicate
                            )
            response = HttpResponse("")
            response.status_code = 200             
            return response
        except Exception as e:     
            logger.error(f"Webhooks POST {str(e)}")         
            response = HttpResponse(str(e))
            response.status_code = 500             
            return response


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
    
def get_active_campaign_list_qs(request):
    first_model_query = (Campaignlead.objects
        .filter(active_campaign_list=OuterRef('pk'), complete=False)
        .values('active_campaign_list')
        .annotate(cnt=Count('pk'))
        .values('cnt')
    )    
    active_campaign_list_qs = ActiveCampaignList.objects.annotate(
        first_model_count=Subquery(first_model_query)
    )     
    site_pk = get_site_pk_from_request(request)
    if site_pk and not site_pk == 'all':
        active_campaign_list_qs = active_campaign_list_qs.filter(site__pk=site_pk)
    return active_campaign_list_qs.order_by('first_model_count')

@login_required
def get_active_campaign_lists(request, **kwargs):
    # try:
    if not settings.DEBUG:
        if request.user.profile.company:
            request.user.profile.company.first().get_and_generate_active_campaign_list_objects()
        return render(request, f"active_campaign/htmx/active_campaign_lists_select.html", 
        {'active_campaign_lists':get_active_campaign_list_qs(request)})
    return render(request, f"active_campaign/htmx/active_campaign_lists_select.html", 
    {'active_campaign_lists':get_active_campaign_list_qs(request)})
@login_required
def set_active_campaign_lists_site(request, **kwargs):
    # try:
    print(request.POST.get('site_pk'))
    active_campaign_list = ActiveCampaignList.objects.get(pk=kwargs.get('list_pk'))
    site_pk = request.POST.get('site_pk',None)
    if site_pk:
        site = Site.objects.get(pk=site_pk)
        active_campaign_list.site = site
    else:
        active_campaign_list.site = None
    active_campaign_list.save()
    return render(request, 'active_campaign/htmx/leads_configuration_select.html', {'active_campaign_list':active_campaign_list, 'site_list':Site.objects.all()})
    # except Exception as e:        
    #     logger.error(f"set_active_campaign_lists_site {str(e)}")
