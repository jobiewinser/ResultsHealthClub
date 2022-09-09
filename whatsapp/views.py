from datetime import datetime
import logging
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt

from whatsapp.models import WhatsAppMessage
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        challenge = request.GET.get('hub.challenge',{})
        response = HttpResponse(challenge)
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        for k,v in json.loads(request.body).items():
            print(k, v)
        body = json.loads(request.body)
        for entry in body.get('entry'):
            for change in entry.get('changes'):
                value = change.get('value')
                metadata = value.get('metadata')
                to_number = metadata.get('display_phone_number')
                from_number = metadata.get('display_phone_number')
                messages = value.get('messages', [])
                for message in messages:
                    WhatsAppMessage.objects.get_or_create(
                        wamid=message.get('id'),
                        datetime = datetime.fromtimestamp(int(message.get('timestamp'))),
                        message = message.get('text').get('body',''),
                        phone_to = to_number,
                        phone_from = from_number,
                        )
                        
        response = HttpResponse("")
        response.status_code = 200
        return response