from datetime import datetime
import logging
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from academy_leads.models import AcademyLead, Communication

from whatsapp.models import WhatsAppMessage, WhatsAppMessageStatus
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        challenge = request.GET.get('hub.challenge',{})
        response = HttpResponse(challenge)
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        logger.debug(str(request.POST))
        body = json.loads(request.body)
        for entry in body.get('entry'):
            for change in entry.get('changes'):
                value = change.get('value')
                for message in value.get('messages', []):
                    metadata = value.get('metadata')
                    wamid = message.get('id')
                    to_number = metadata.get('display_phone_number')
                    from_number = message.get('from')
                    datetime_from_request = datetime.fromtimestamp(int(message.get('timestamp')))
                    try:
                        lead = AcademyLead.objects.get(phone__icontains=from_number[-10:])
                        communication = Communication.objects.get_or_create(    
                            datetime = datetime_from_request,
                            lead = lead,
                            type = 'b',
                            successful = True,
                            automatic = False,
                            staff_user = None
                        )[0]
                    except Exception as e:
                        lead = None
                        communication = None
                    existing_messages = WhatsAppMessage.objects.filter( wamid=wamid )
                    if not existing_messages:
                        # Likely a message from a customer     
                        WhatsAppMessage.objects.create(
                            wamid=wamid,
                            message = message.get('text').get('body',''),
                            datetime = datetime_from_request,
                            phone_to = f"{to_number}",
                            phone_from = from_number,
                            communication=communication
                            )
                for status_dict in value.get('statuses', []):
                    whats_app_messages = WhatsAppMessage.objects.filter(wamid=status_dict.get('id'))
                    if whats_app_messages:
                        whatsapp_message_status = WhatsAppMessageStatus.objects.get_or_create(
                            whats_app_message=whats_app_messages[0],
                            datetime = datetime.fromtimestamp(int(status_dict.get('timestamp'))),
                            status = status_dict.get('status'),
                        )[0]
                        if status_dict.get('status') == 'read':
                            try:
                                communication = whatsapp_message_status.whats_app_message.communication
                                communication.successful = True
                                communication.save()
                            except:
                                pass
                        
        response = HttpResponse("")
        response.status_code = 200     
        
        return response