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
class ActiveCampaignApi:
    
    # active_campaign_api_key = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
    # active_campaign_url = os.getenv("ACTIVE_CAMPAIGN_URL")
    site_url = os.getenv("SITE_URL")

    def __init__(self, active_campaign_api_key, active_campaign_url):
        self.active_campaign_api_key = active_campaign_api_key
        self.active_campaign_url = active_campaign_url

    def _get_headers(self):
        headers = {
            'Api-Token': self.active_campaign_api_key
                   }
        return headers
    def get(self, endpoint, result_key, params={}, limit=100):       
        if self.active_campaign_url: 
        #     url = f"{self.active_campaign_url}/{endpoint}?limit={str(limit)}"
        #     headers = self._get_headers()
        #     response = requests.get(url=url, headers=headers)
        #     if response:
        #         return response.json() or {}
        # return {}
            param_string = ""
            for k,v in params.items():
                if type(v) == list:
                    value_string = ','.join(v)
                else:
                    value_string = v
                param_string = f"{param_string}&{k}={value_string}"
        
            url = f"{self.active_campaign_url}/{endpoint}?limit={str(limit)}{param_string}"
            headers = self._get_headers()
            i = 0
            count = 0
            results = []
            response = requests.get(url=url, headers=headers)
            if not response.status_code == 200:
                return []
            response_json = response.json()
            while count < int(response_json.get('meta', {}).get('total', 0)):
                count += len(response_json.get(result_key,[]))
                results += response_json.get(result_key,[])
                i+=1
                response_json = requests.get(url=f"{url}&offset={i}", headers=headers).json()
            return results
        return None

    # Get\
    #POST
    def create_webhook(self, name, guid, list_id):     
        if not settings.DEBUG:   
            url = f"{self.active_campaign_url}/api/3/webhooks"
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
    def get_webhooks(self, active_campaign_url): 
        return self.get("api/3/webhooks", "webhooks")      
    # Get
    # def get_campaigns(self):        
    #     url = f"{self.active_campaign_url}/api/3/campaigns"
    #     headers = self._get_headers()
    #     response = requests.get(url=url, headers=headers)
    #     return response.json()
    def get_lists(self, active_campaign_url):      
        return self.get("api/3/lists")      
    # Get
    def get_all_messages(self):        
        url = f"{self.active_campaign_url}/api/3/messages?limit=100"
        headers = self._get_headers()
        i = 0
        count = 0
        messages = []
        response_json = self.get("api/3/messages")      
        while count < int(response_json.get('meta', {}).get('total', 0)):
            count += len(response_json.get('messages',[]))
            messages += response_json.get('messages',[])
            i+=1
            response_json = requests.get(url=f"{url}&offset={i}", headers=headers).json()
        return messages
    # Get
    def list_contacts_by_campaign(self, campaign_id):      
        if not self.active_campaign_url:
            return []  
        url = f"{self.active_campaign_url}/api/3/contacts?listid={campaign_id}&limit=100"
        headers = self._get_headers()
        i = 0
        count = 0
        contacts = []
        response_json = requests.get(url=url, headers=headers).json()
        while count < int(response_json.get('meta', {}).get('total', 0)):
            count += len(response_json.get('contacts',[]))
            contacts += response_json.get('contacts',[])
            i+=1
            response_json = requests.get(url=f"{url}&offset={i}", headers=headers).json()
        return contacts
    # Get
    def list_contacts_by_id_list(self, id_list):        
        url = f"{self.active_campaign_url}/api/3/contacts?ids={','.join(id_list)}&limit=100"
        headers = self._get_headers()
        i = 0
        count = 0
        contacts = []
        response_json = requests.get(url=url, headers=headers).json()
        while count < int(response_json.get('meta', {}).get('total', 0)):
            count += len(response_json.get('contacts',[]))
            contacts += response_json.get('contacts',[])
            i+=1
            response_json = requests.get(url=f"{url}&offset={i}", headers=headers).json()
        return contacts

    