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
class Whatsapp():    
    # whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_url = os.getenv("WHATSAPP_URL")
    whatsapp_app_id = os.getenv("WHATSAPP_APP_ID")
    
    whatsapp_business_id = os.getenv("WHATSAPP_BUSINESS_ID")
    whatsapp_business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

    def __init__(self, whatsapp_access_token):
        self.whatsapp_access_token = whatsapp_access_token

    def _get_headers(self):
        headers = {
            'Authorization': 'Bearer ' + self.whatsapp_access_token,
                   'Content-Type': 'application/json'
                   }
        return headers
    #POST
    def send_message(self, recipient_number, message, whatsapp_business_phone_number_id, preview_url = False):   
        if message:  
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
            print(response_body)
            return response_body
    #POST
    def create_template(self, template_object):   
        url = f"{self.whatsapp_url}{template_object.site.whatsapp_business_account_id}/message_templates"
        headers = self._get_headers()
        body = { 
            "name": template_object.pending_name,
            "category": template_object.pending_category,
            "language": "en_GB",
            "components": template_object.pending_components,
        }
        response = requests.post(url=url, json=body, headers=headers)
        response_body = response.json()
        template_object.message_template_id = response_body['id']
        template_object.save()
        return response_body
    #POST
    def edit_template(self, template_object):   
        if template_object.status in ["APPROVED", "REJECTED", "PAUSED"]:
            url = f"{self.whatsapp_url}{template_object.message_template_id}"
            headers = self._get_headers()
            body = { 
                "components": template_object.pending_components
            }
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            return response_body
    #GET
    def get_templates(self, whatsapp_business_account_id):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}{whatsapp_business_account_id}/message_templates"
            headers = self._get_headers()
            response = requests.get(url=url, headers=headers)
            response_body = response.json()
            return response_body
            
    #GET
    def get_template(self, whatsapp_business_account_id, message_template_id):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}{message_template_id}"
            headers = self._get_headers()
            response = requests.get(url=url, headers=headers)
            response_body = response.json()
            return response_body
    #DELETE
    def delete_template(self, whatsapp_business_account_id, template_name):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}{whatsapp_business_account_id}/message_templates"
            headers = self._get_headers()
            body = { 
                "name": template_name,
            }
            response = requests.delete(url=url, json=body, headers=headers)
            response_body = response.json()
            return response_body
            
    def get_phone_numbers(self):        
        url = f"{self.whatsapp_url}{self.whatsapp_business_account_id}/phone_numbers?access_token={self.whatsapp_access_token}"
        # headers = self._get_headers()
        response = requests.get(url=url)
        response_body = response.json()
        return response_body
        