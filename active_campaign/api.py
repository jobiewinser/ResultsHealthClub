import logging
import os
from datetime import datetime

import requests
from django.conf import settings
import json
from django.utils.decorators import method_decorator
from django.http import HttpResponse, Http404
from django.views import View 
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseRedirect
from django.template import loader
logger = logging.getLogger(__name__)
class ActiveCampaign:
    
    active_campaign_api_key = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
    active_campaign_url = os.getenv("ACTIVE_CAMPAIGN_URL")

    def _get_headers(self):
        headers = {
            'Authorization': 'Bearer ' + self.active_campaign_api_key,
                   'Content-Type': 'application/json'
                   }
        return headers
    #POST
    # def send_message(self, recipient_number, message, preview_url = False):        
    #     url = f"{self.whatsapp_url}{self.whatsapp_business_phone_number_id}/messages"
    #     headers = self._get_headers()
    #     body = { 
    #         "messaging_product": "whatsapp", 
    #         "to": f"{recipient_number}", 
    #         "type": "text",
    #         "text": json.dumps({
    #             "body": f"{message}",
    #             "preview_url": preview_url,
    #             })
    #     }
    #     response = requests.post(url=url, json=body, headers=headers)
    #     response_body = response.json()
    #     return response_body