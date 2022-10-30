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


from whatsapp.models import WhatsappMessageImage, WhatsappTemplate
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
    def send_free_text_message(self, customer_number, message, whatsapp_number, preview_url = False):   
        from core.models import AttachedError
        if message:  
            if settings.WHATSAPP_PHONE_OVERRIDE1:
                non_overwritten_customer_number = customer_number
                customer_number = settings.WHATSAPP_PHONE_OVERRIDE1
            url = f"{self.whatsapp_url}/{whatsapp_number.whatsapp_business_phone_number_id}/messages"
            headers = self._get_headers()
            body = { 
                "messaging_product": "whatsapp", 
                "to": f"{customer_number}", 
                "type": "text",
                "text": json.dumps({
                    "body": f"{message}",
                    "preview_url": preview_url,
                    })
            }
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            attached_errors = []
            # response_body = {
            #     "object": "whatsapp_business_account",
            #     "entry": [
            #         {
            #             "id": "104128642479500",
            #             "changes": [
            #                 {
            #                     "value": {
            #                         "messaging_product": "whatsapp",
            #                         "metadata": {
            #                             "display_phone_number": "447872000364",
            #                             "phone_number_id": "108208485398311"
            #                         },
            #                         "statuses": [
            #                             {
            #                                 "id": "wamid.HBgMNDQ3ODI3Nzc3OTQwFQIAERgSNjgxNDQ4MjVENUM5NkY3NTc2AA==",
            #                                 "status": "failed",
            #                                 "timestamp": "1666789627",
            #                                 "recipient_id": "447827777940",
            #                                 "errors": [
            #                                     {
            #                                         "code": 131047,
            #                                         "title": "Message failed to send because more than 24 hours have passed since the customer last replied to this number.",
            #                                         "href": "https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes/"
            #                                     }
            #                                 ]
            #                             }
            #                         ]
            #                     },
            #                     "field": "messages"
            #                 }
            #             ]
            #         }
            #     ]
            # }
            for entry in response_body.get('entry', []):
                for change in entry.get('changes'):
                    value = change.get('value')
                    for status in value.get('statuses'):
                        potential_errors = status.get('errors', None)
                        if potential_errors:
                            for error in potential_errors:
                                code = error.get('code')
                                if str(code) == '131047':
                                    attached_errors.append(
                                        AttachedError.objects.create(
                                            type = '1104',
                                            attached_field = "whatsapp_number",
                                            whatsapp_number = whatsapp_number,
                                            customer_number = non_overwritten_customer_number,
                                        )
                                    )                                
            if not attached_errors:
                AttachedError.objects.filter(
                    type__in = ['1104','1105'],
                    archived = False,
                    whatsapp_number = whatsapp_number,
                    customer_number = non_overwritten_customer_number,
                ).update(archived = True)

            print("send_free_text_message response_body", response_body)
            return response_body, attached_errors
    def send_template_message(self, customer_number, whatsapp_number, template_object, language, components):  
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
        non_overwritten_customer_number = customer_number
        if settings.WHATSAPP_PHONE_OVERRIDE1:
            customer_number = settings.WHATSAPP_PHONE_OVERRIDE1
        if template_name:  
            AttachedError.objects.filter(
                type = '1102',
                whatsapp_template = template_object,
                customer_number = non_overwritten_customer_number,
                whatsapp_number = whatsapp_number,
                archived = False,
            ).update(archived = True)
            url = f"{self.whatsapp_url}/{whatsapp_number.whatsapp_business_phone_number_id}/messages"
            headers = self._get_headers()
            body = { 
                "messaging_product": "whatsapp", 
                "to": f"{customer_number}", 
                "type": "template",
                "template": json.dumps({
                    "name": template_name,
                    "language": language,
                    "components": components
                    })
            }
            print("")
            print("")
            print("send_template_message body", str(body))
            print("")
            print("")
            response = requests.post(url=url, json=body, headers=headers)
            response_body = response.json()
            
            from campaign_leads.models import Campaignlead            
            potential_error = response_body.get('error', None)
            if potential_error:
                code = potential_error.get('code')
                campaign_lead = Campaignlead.objects.filter(whatsapp_number=non_overwritten_customer_number).last()
                if str(code) == '132000':
                    AttachedError.objects.create(
                        type = '1103',
                        attached_field = "whatsapp_template",
                        whatsapp_template = template_object,
                        campaign_lead=campaign_lead,
                        customer_number = non_overwritten_customer_number,
                        whatsapp_number = whatsapp_number,
                        admin_action_required = True,
                    )
                elif str(code) == '133010':
                    AttachedError.objects.create(
                        type = '1105',
                        attached_field = "whatsapp_template",
                        whatsapp_template = template_object,
                        campaign_lead=campaign_lead,
                        customer_number = non_overwritten_customer_number,
                        whatsapp_number = whatsapp_number,
                        admin_action_required = True,
                    )
            else:
                AttachedError.objects.filter(
                    type__in = ['1103','1105'],
                    whatsapp_template = template_object,
                    archived = False,
                    whatsapp_number = whatsapp_number,
                    customer_number = non_overwritten_customer_number,
                ).update(archived = True)

            print("send_template_message response_body", response_body)
            return response_body
        else:
            campaign_lead = Campaignlead.objects.filter(whatsapp_number=non_overwritten_customer_number).last()
            AttachedError.objects.create(
                type = '1102',
                attached_field = "whatsapp_template",
                whatsapp_template = template_object,
                        campaign_lead=campaign_lead,
                whatsapp_number = whatsapp_number,
                customer_number = non_overwritten_customer_number,
            )
    #POST
    def create_template(self, template_object):   
        url = f"{self.whatsapp_url}/{template_object.site.whatsapp_business_account_id}/message_templates"
        headers = self._get_headers()
        pending_components = template_object.pending_components
        for component in pending_components:
            counter = 1
            text = component.get('text', '')
            if '[[1]]' in text:
                text = text.replace('[[1]]','{{'+str(counter)+'}}')
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
        template_object = WhatsappTemplate.objects.get(pk=template_object.pk)
        template_object.message_template_id = response_body['id']
        template_object.save()
        return response_body
    #POST
    def edit_template(self, template_object):   
        if template_object.status in ["APPROVED", "REJECTED", "PAUSED"]:
            url = f"{self.whatsapp_url}/{template_object.message_template_id}"
            headers = self._get_headers()
            pending_components = template_object.pending_components
            for component in pending_components:
                counter = 1
                text = component.get('text', '')
                if '[[1]]' in text:
                    text = text.replace('[[1]]','{{'+str(counter)+'}}')
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
                        type = '1101',
                        attached_field = "whatsapp_template",
                        whatsapp_template = template_object,
                    )
            else:
                AttachedError.objects.filter(
                    type = '1101',
                    whatsapp_template = template_object,
                    archived = False,
                ).update(archived = True)

            print("edit_template", str(response_body))
            return response_body
    #GET
    def get_templates(self, whatsapp_business_account_id):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}/{whatsapp_business_account_id}/message_templates"
            headers = self._get_headers()
            response = requests.get(url=url, headers=headers)
            response_body = response.json()
            return response_body
            
    #GET
    def get_template(self, whatsapp_business_account_id, message_template_id):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}/{message_template_id}"
            headers = self._get_headers()
            response = requests.get(url=url, headers=headers)
            response_body = response.json()
            return response_body
    #DELETE
    def delete_template(self, whatsapp_business_account_id, template_name):   
        if whatsapp_business_account_id:  
            url = f"{self.whatsapp_url}/{whatsapp_business_account_id}/message_templates"
            headers = self._get_headers()
            body = { 
                "name": template_name,
            }
            response = requests.delete(url=url, json=body, headers=headers)
            response_body = response.json()
            return response_body
            
    def get_phone_numbers(self, whatsapp_business_account_id):        
        url = f"{self.whatsapp_url}/{whatsapp_business_account_id}/phone_numbers?access_token={self.whatsapp_access_token}"
        # headers = self._get_headers()
        response = requests.get(url=url)
        response_body = response.json()
        return response_body     
            
    def create_phone_number(self, whatsapp_business_account_id, cc, phone_number, migrate_phone_number=True):        
        url = f"{self.whatsapp_url}/{whatsapp_business_account_id}/phone_numbers"
        headers = self._get_headers()
        filtered_number = ""
        for c in phone_number:
            if c.isdigit():
                filtered_number = filtered_number + c
        body = { 
            "cc": cc, 
            "phone_number": filtered_number,
            "migrate_phone_number": str(migrate_phone_number).lower(), 
            "access_token": self.whatsapp_access_token, 
        }
        response = requests.post(url=url, json=body, headers=headers)
        response_body = response.json()
        return response_body        
            
    def get_media_url(self, media_id):        
        url = f"{self.whatsapp_url}/{media_id}"
        headers = self._get_headers()
        response = requests.get(url=url, headers=headers)
        response_body = response.json()
        return response_body
            
    def get_media_file(self, media_url):        
        url = f"{media_url}"
        headers = self._get_headers()
        response = requests.get(url=url, headers=headers)
        
        return response
            
    def get_media_file_from_media_id(self, media_id):        
        media_url = self.get_media_url(media_id).get('url') 
        response = self.get_media_file(media_url)
        filename = get_filename_from_cd(response.headers.get('content-disposition'))
        # file = open(filename, "wb")
        # file.write(response.content)
        # file.close()
        import io
        from django.core.files.images import ImageFile
        image = ImageFile(io.BytesIO(response.content), name=filename)  # << the answer!
        return image


import re
def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]