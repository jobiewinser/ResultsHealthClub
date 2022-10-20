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


from whatsapp.models import WhatsappTemplate
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
    def send_free_text_message(self, recipient_number, message, whatsapp_number, preview_url = False):   
        from core.models import AttachedError
        if message:  
            if settings.WHATSAPP_PHONE_OVERRIDE1:
                recipient_number = settings.WHATSAPP_PHONE_OVERRIDE1
            url = f"{self.whatsapp_url}{whatsapp_number.whatsapp_business_phone_number_id}/messages"
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

            potential_error = response_body.get('error', None)
            if potential_error:
                code = potential_error.get('code')
                if str(code) == '132000':
                    AttachedError.objects.create(
                        type = '103',
                        attached_field = "whatsapp_number",
                        whatsapp_number = whatsapp_number,
                        recipient_number = recipient_number,
                        admin_action_required = True,
                    )
            else:
                AttachedError.objects.filter(
                    type = '103',
                    whatsapp_number = whatsapp_number,
                    archived = False,
                    recipient_number = recipient_number,
                ).update(archived = True)

            print(response_body)
            return response_body
    def send_template_message(self, recipient_number, whatsapp_number, template_object, language, components):  
        from core.models import AttachedError
        template_name = template_object.name
        #  "components": [{
        #     "type": "body",
        #     "parameters": [{
        #                     "type": "text",
        #                     "text": "name"
        #                 },
        #                 {
        #                 "type": "text",
        #                 "text": "Hi there"
        #                 }]
        #         }] 
        if settings.WHATSAPP_PHONE_OVERRIDE1:
            recipient_number = settings.WHATSAPP_PHONE_OVERRIDE1
        if template_name:  
            AttachedError.objects.filter(
                type = '102',
                whatsapp_template = template_object,
                recipient_number = recipient_number,
                whatsapp_number = whatsapp_number,
                archived = False,
            ).update(archived = True)
            url = f"{self.whatsapp_url}{whatsapp_number.whatsapp_business_phone_number_id}/messages"
            headers = self._get_headers()
            body = { 
                "messaging_product": "whatsapp", 
                "to": f"{recipient_number}", 
                "type": "template",
                # "template": json.dumps({
                #     "name": template_name,
                #     "language": language,
                #     "components": components
                #     })
                "template": {
                    "name": template_name,
                    "language": language,
                    "components": components
                    }
            }
            print("")
            print("")
            print(str(body))
            print("")
            print("")
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            
            
            potential_error = response_body.get('error', None)
            if potential_error:
                code = potential_error.get('code')
                if str(code) == '132000':
                    AttachedError.objects.create(
                        type = '103',
                        attached_field = "whatsapp_template",
                        whatsapp_template = template_object,
                        recipient_number = recipient_number,
                        whatsapp_number = whatsapp_number,
                        admin_action_required = True,
                    )
            else:
                AttachedError.objects.filter(
                    type = '103',
                    whatsapp_template = template_object,
                    archived = False,
                    whatsapp_number = whatsapp_number,
                    recipient_number = recipient_number,
                ).update(archived = True)

            print(response_body)
            return response_body
        else:
            AttachedError.objects.create(
                type = '102',
                attached_field = "whatsapp_template",
                whatsapp_template = template_object,
                whatsapp_number = whatsapp_number,
                recipient_number = recipient_number,
            )
    #POST
    def create_template(self, template_object):   
        url = f"{self.whatsapp_url}{template_object.site.whatsapp_business_account_id}/message_templates"
        headers = self._get_headers()
        pending_components = template_object.pending_components
        counter = 1
        for component in pending_components:
            text = component.get('text', '')
            if '[[1]]' in text:
                text.replace('[[1]]','{{'+str(counter)+'}}')
                counter = counter + 1
            component['text'] = text
            
        body = { 
            "name": template_object.pending_name,
            "category": template_object.pending_category,
            "language": "en_GB",
            "components": pending_components,
        }
        
                
        from django.core.mail import send_mail
        from django.shortcuts import render
        response = requests.post(url=url, json=body, headers=headers)
        response_body = response.json()
        description = f"<p>body: {str(body)}</p><br><p>response_body: {str(response_body)}</p>"
        send_mail(
            subject='Winser Systems Prod - create template ',
            message=description,
            from_email='jobiewinser@gmail.com',
            recipient_list=['jobiewinser@gmail.com'])
        print(response_body)
        template_object.message_template_id = response_body['id']
        template_object.save()
        return response_body
    #POST
    def edit_template(self, template_object):   
        if template_object.status in ["APPROVED", "REJECTED", "PAUSED"]:
            url = f"{self.whatsapp_url}{template_object.message_template_id}"
            headers = self._get_headers()
            pending_components = template_object.pending_components
            counter = 1
            for component in pending_components:
                text = component.get('text', '')
                if '[[1]]' in text:
                    text.replace('[[1]]','{{'+str(counter)+'}}')
                    counter = counter + 1
                component['text'] = text
            body = { 
                "components": pending_components
            }
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            potential_error = response_body.get('error', None)
            from core.models import AttachedError
            if potential_error:
                code = potential_error.get('code')
                if str(code) == '100':
                    AttachedError.objects.create(
                        type = '101',
                        attached_field = "whatsapp_template",
                        whatsapp_template = template_object,
                    )
            else:
                AttachedError.objects.filter(
                    type = '101',
                    whatsapp_template = template_object,
                    archived = False,
                ).update(archived = True)

            print("edit_template", str(response_body))
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
            
    def get_phone_numbers(self, whatsapp_business_account_id):        
        url = f"{self.whatsapp_url}{whatsapp_business_account_id}/phone_numbers?access_token={self.whatsapp_access_token}"
        # headers = self._get_headers()
        response = requests.get(url=url)
        response_body = response.json()
        return response_body
        