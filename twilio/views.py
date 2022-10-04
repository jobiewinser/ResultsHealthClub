import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaignlead

from twilio.models import TwilioMessage, TwilioRawWebhook
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel
@method_decorator(csrf_exempt, name="dispatch")
class MessageWebhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(f"MessageWebhooks get {str(request.GET.dict())}")     
        webhook = TwilioRawWebhook.objects.create(
            json_data=request.GET.dict(),
            request_type='b',
            twilio_webhook_type='a',
        )
        # try:
        #     webhook.request_type = 
        # except Exception as e:
        #     error = ErrorModel.objects.create({'error':str(e)})
        #     webhook.errors.add(error)
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        post_dict = request.POST.dict()
        logger.debug(f"MessageWebhooks post {str(post_dict)}")       
        webhook = TwilioRawWebhook.objects.create(
            json_data=post_dict,
            request_type='a',
            twilio_webhook_type='a',
        )          
        message = TwilioMessage.objects.create(
            inbound = True,
            Type = 'a',
            raw_webhook = webhook,
            customer_number = post_dict.get('From', ''),
            system_user_number = post_dict.get('To', ''),
        )

        for key in [
            'raw_webhook','Body','ProfileName','SmsSid','MessageSid',
            'SmsMessageSid','AccountSid','ApiVersion',
            'WaId','NumMedia','NumSegments',
            'ReferralNumMedia','SmsStatus'
        ]:
            try:
                message.__setattr__(key, post_dict.get(key, ''))
            except Exception as e:
                error = ErrorModel.objects.create(json_data={'error':str(e)})
                message.errors.add(error)
        lead = Campaignlead.objects.filter(whatsapp_number=post_dict.get('From', '')).last()
        if lead:
            message.communication.lead = lead
        message.save()
        response = HttpResponse("")
        response.status_code = 200             
        return response

@method_decorator(csrf_exempt, name="dispatch")
class StatusWebhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(f"StatusWebhooks get {str(request.GET.dict())}")
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        logger.debug(f"StatusWebhooks post {str(request.POST.dict())}")
        response = HttpResponse("")
        response.status_code = 200
        return response