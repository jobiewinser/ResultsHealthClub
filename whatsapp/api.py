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
# https://developers.facebook.com/docs/whatsapp/cloud-api/reference
# https://business.facebook.com/settings/people/100085397745468?business_id=851701125750291
class Whatsapp:
    
    whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_url = os.getenv("WHATSAPP_URL")
    whatsapp_app_id = os.getenv("WHATSAPP_APP_ID")
    
    whatsapp_business_id = os.getenv("WHATSAPP_BUSINESS_ID")
    whatsapp_business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

    def _get_headers(self):
        headers = {
            'Authorization': 'Bearer ' + self.whatsapp_access_token,
                   'Content-Type': 'application/json'
                   }
        return headers
    #POST
    def send_message(self, recipient_number, message, whatsapp_business_phone_number_id, preview_url = False):   
        if settings.WHATSAPP_PHONE_OVERRIDE:
            recipient_number = settings.WHATSAPP_PHONE_OVERRIDE     
        url = f"{self.whatsapp_url}{whatsapp_business_phone_number_id}/messages"
        headers = self._get_headers()
        body = { 
            "messaging_product": "whatsapp", 
            "to": f"{recipient_number}", 
            "type": "text",
            "text": json.dumps({
                "body": f"{message}",
                "preview_url": preview_url,
                })
        }
        response = requests.post(url=url, json=body, headers=headers)
        response_body = response.json()
        return response_body
    #GET
    def get_phone_numbers(self):        
        url = f"{self.whatsapp_url}{self.whatsapp_business_account_id}/phone_numbers?access_token={self.whatsapp_access_token}"
        # headers = self._get_headers()
        response = requests.get(url=url)
        response_body = response.json()
        return response_body
        