import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
            json_data=json.loads(request.GET.dict()),
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
        logger.debug(f"MessageWebhooks post {str(request.POST.dict())}")       
        webhook = TwilioRawWebhook.objects.create(
            json_data=json.loads(request.POST.dict()),
            request_type='a',
            twilio_webhook_type='a',
        )          
           
        From_raw = request.POST.dict().get('From')[0]
        Type_and_From = From_raw.split(':')
        Type = Type_and_From[0]
        From = Type_and_From[1]
        message = TwilioMessage.objects.create(
            inbound = 'a',
            type = 'a',
            raw_webhook = webhook,
            Type = Type,
            From = From,
        )

        for key in [
            'raw_webhook','Body','ProfileName',
            'From','To','SmsSid','MessageSid',
            'SmsMessageSid','AccountSid','ApiVersion',
            'WaId','NumMedia','NumSegments',
            'ReferralNumMedia','SmsStatus'
        ]:
            try:
                message.__setattr__(key, request.POST.dict().get(key, [''])[0])
            except Exception as e:
                error = ErrorModel.objects.create({'error':str(e)})
                message.errors.add(error)
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