import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from academy_leads.models import AcademyLead
from active_campaign.api import ActiveCampaign
from active_campaign.models import CampaignWebhook, ActiveCampaignList
from core.models import Site
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import OuterRef, Subquery, Count
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
                    phone_number_whole = str(data.get('contact[phone]', "")).replace('+','').replace(' ','')
                    if phone_number_whole:
                        if phone_number_whole[0] == "0":
                            phone_number = phone_number_whole[1:]
                            country_code = "44"
                        elif phone_number_whole[:2] == "44":
                            phone_number = phone_number_whole[2:]
                            country_code = "44"
                        else:
                            phone_number = phone_number_whole
                            country_code = "44"
                    else:
                        phone_number = "None"
                        country_code = "None"

                    if not AcademyLead.objects.filter(
                            active_campaign_list=active_campaign_list,
                            active_campaign_contact_id=data.get('contact[id]')
                        ):
                        AcademyLead.objects.create(
                            active_campaign_contact_id=data.get('contact[id]'),
                            first_name=data.get('contact[first_name]', "None"),
                            phone=phone_number,
                            country_code=country_code,
                            active_campaign_list=active_campaign_list,
                            active_campaign_form_id=data.get('form[id]', None)
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

def get_and_generate_active_campaign_list_objects():
    for active_campaign_list_dict in ActiveCampaign().get_lists().get('lists',[]):
        active_campaign_list, created = ActiveCampaignList.objects.get_or_create(
            active_campaign_id = active_campaign_list_dict.pop('id'),
            name = active_campaign_list_dict.pop('name')
        )
        active_campaign_list.json_data = active_campaign_list_dict
        active_campaign_list.save()
    return ActiveCampaignList.objects.all()

@login_required
def get_active_campaign_lists(request):
    # try:
        get_and_generate_active_campaign_list_objects()
        first_model_query = (AcademyLead.objects
            .filter(active_campaign_list=OuterRef('pk'), complete=False)
            .values('active_campaign_list')
            .annotate(cnt=Count('pk'))
            .values('cnt')
        )
        
        active_campaign_list_qs = ActiveCampaignList.objects.annotate(
            first_model_count=Subquery(first_model_query)
        ) 
        
        return render(request, f"active_campaign/htmx/active_campaign_lists_select.html", 
        {'active_campaign_lists':active_campaign_list_qs.order_by('first_model_count')})

@login_required
def set_active_campaign_lists_site(request, **kwargs):
    # try:
    print(request.POST.get('site_choice'))
    active_campaign_list = ActiveCampaignList.objects.get(pk=kwargs.get('list_pk'))
    active_campaign_list.site = Site.objects.get(pk=request.POST.get('site_choice'))
    active_campaign_list.save()
    return render(request, 'active_campaign/htmx/leads_configuration_select.html', {'active_campaign_list':active_campaign_list, 'sites':Site.objects.all()})
    # except Exception as e:        
    #     logger.error(f"set_active_campaign_lists_site {str(e)}")
