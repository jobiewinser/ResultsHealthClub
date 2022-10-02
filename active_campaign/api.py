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

# https://developers.activecampaign.com/reference
class ActiveCampaign:
    
    active_campaign_api_key = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
    active_campaign_url = os.getenv("ACTIVE_CAMPAIGN_URL")
    site_url = os.getenv("SITE_URL")

    def _get_headers(self):
        headers = {
            'Api-Token': self.active_campaign_api_key
                   }
        return headers
    #POST
    def create_webhook(self, name, guid, list_id):        
        url = f"{self.active_campaign_url}api/3/webhooks"
        headers = self._get_headers()
        body = {
            "webhook": {
                "name": f"{name} (Campaign Lead System)",
                "url": f"{self.site_url}/active-campaign-webhooks/{guid}/",
                "listid": list_id,                
                "events": [
                    "subscribe",                    
                    "update"
                ],
                "sources": [
                    "public",
                    "admin",
                    "api",
                    "system"
                ]
            }
        }
        response = requests.post(url=url, json=body, headers=headers)
        return response
    # Get
    # def get_campaigns(self):        
    #     url = f"{self.active_campaign_url}api/3/campaigns"
    #     headers = self._get_headers()
    #     response = requests.get(url=url, headers=headers)
    #     return response.json()
    def get_lists(self, activate_campaign_url):       
        if activate_campaign_url: 
            url = f"{activate_campaign_url}api/3/lists?limit=100"
            headers = self._get_headers()
            response = requests.get(url=url, headers=headers)
            return response.json()
        return {}
    # Get
    def get_all_messages(self):        
        url = f"{self.active_campaign_url}api/3/messages?limit=100"
        headers = self._get_headers()
        i = 0
        count = 0
        messages = []
        response_json = requests.get(url=url, headers=headers).json()
        while count < int(response_json.get('meta', {}).get('total', 0)):
            count += len(response_json.get('messages',[]))
            messages += response_json.get('messages',[])
            i+=1
            response_json = requests.get(url=f"{url}&offset={i}", headers=headers).json()
        return messages

    