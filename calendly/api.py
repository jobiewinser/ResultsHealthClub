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
    def create_webhook_subscription(self, organization = None, user = None):   
        url = f"{self.calendly_url}webhook_subscriptions"
        headers = self._get_headers()
        body = { 
            "url": f"{self.site_url}/active-campaign-webhooks/",
            "events": [
                "invitee.created",
                "invitee.canceled"
            ],
        }
        if user or organization:
            if user:
                body.update({'user':f"https://api.calendly.com/organizations/{user}", 'scope':'user'})
            else:
                body.update({'organization':f"https://api.calendly.com/users/{organization}", 'scope':'organization'})
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            print("response_body", response_body)
            print("body", body)
            return response_body