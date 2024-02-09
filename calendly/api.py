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
# https://developers.facebook.com/docs/calendly/cloud-api/reference
# https://business.facebook.com/settings/people/100085397745468?business_id=851701125750291
class Calendly():    
    site_url = os.getenv("SITE_URL")

    # calendly_access_token = os.getenv("CALENDLY_ACCESS_TOKEN")
    calendly_url = os.getenv("CALENDLY_URL")

    def __init__(self, calendly_access_token):
        self.calendly_access_token = calendly_access_token

    def _get_headers(self):
        headers = {
            'Authorization': 'Bearer ' + self.calendly_access_token,
                   'Content-Type': 'application/json'
                   }
        return headers
    #POST
    def create_webhook_subscription(self, guid, organization = None, user = None):   
        url = f"{self.calendly_url}/webhook_subscriptions"
        headers = self._get_headers()
        body = { 
            "url": f"{self.site_url}/calendly-webhooks/{guid}/",
            "events": [
                "invitee.created",
                "invitee.canceled"
            ],
        }
        if user or organization:
            if user:
                body.update({'user':f"{os.getenv('CALENDLY_URL')}/users/{user}", 'scope':'user'})
            else:
                body.update({'organization':f"{os.getenv('CALENDLY_URL')}/organizations/{organization}", 'scope':'organization'})
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            return response_body
        print("create_webhook_subscription no organization or user")
    #GET
    def get_from_uri(self, uri):   
        headers = self._get_headers()
        
        response = requests.get(url=uri, headers=headers)
        response_body = response.json()
        print("response_body", response_body)
        return response_body
    #GET
    def get_user(self):   
        url = f"{self.calendly_url}/users/me"
        headers = self._get_headers()
        
        response = requests.get(url=url, headers=headers)
        response_body = response.json()
        return response_body
    #GET
    def list_webhook_subscriptions(self, organization = None, user = None):   
        url = f"{self.calendly_url}/webhook_subscriptions?organization={os.getenv('CALENDLY_URL')}/organizations/{organization}&scope=organization"
        headers = self._get_headers()
        
        response = requests.get(url=url, headers=headers)
        response_body = response.json()
        return response_body
    #DELETE
    def delete_webhook_subscriptions(self, webhook_guuid):   
        url = f"{self.calendly_url}/webhook_subscriptions/{webhook_guuid}"
        headers = self._get_headers()
        
        response = requests.delete(url=url, headers=headers)
        return response
        # response_body = response.json()
        # print("response_body", response_body)
        # return response_body

    