from datetime import datetime
import logging
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from academy_leads.models import AcademyLead, Communication
from active_campaign.api import ActiveCampaign
from active_campaign.models import Campaign
from whatsapp.models import WhatsAppMessage, WhatsAppMessageStatus
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):                        
        response = HttpResponse("")
        response.status_code = 200     
        
        return response


active_campaign = ActiveCampaign()
@login_required
def get_campaigns(request):
    # for campaign_dict in active_campaign.get_campaigns().get('campaigns',[]):
    #     campaign = Campaign.objects.get_or_create(
    #         active_campaign_id = campaign_dict.pop('id'),
    #     )[0]
    #     campaign.name = campaign_dict.pop('name')
    #     campaign.status = campaign_dict.pop('status')
    #     campaign.uniqueopens = int(campaign_dict.pop('uniqueopens'))
    #     campaign.opens = int(campaign_dict.pop('opens'))
    #     campaign.active_campaign_created = datetime.strptime(campaign_dict.pop('created_timestamp'), '%Y-%m-%d %H:%M:%S')
    #     campaign.active_campaign_updated = datetime.strptime(campaign_dict.pop('updated_timestamp'), '%Y-%m-%d %H:%M:%S')
    #     campaign.json_data = campaign_dict
    #     campaign.save()
    # temp = active_campaign.get_all_messages()
    return render(request, f"active_campaign/htmx/campaigns_select.html", {'campaigns':Campaign.objects.all() })
