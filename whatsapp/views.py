from datetime import datetime
import logging
from django.conf import settings
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaignlead, Call
from messaging.consumers import ChatRoomConsumer

from whatsapp.models import WhatsAppMessage, WhatsAppMessageStatus
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel, Site
from asgiref.sync import async_to_sync, sync_to_async
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        challenge = request.GET.get('hub.challenge',{})
        response = HttpResponse(challenge)
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        print(str(body))
        logger.debug(str(body))
        
        for entry in body.get('entry'):
            for change in entry.get('changes'):
                value = change.get('value')
                for message in value.get('messages', []):
                    metadata = value.get('metadata')
                    wamid = message.get('id')
                    to_number = metadata.get('display_phone_number')
                    from_number = message.get('from')
                    datetime_from_request = datetime.fromtimestamp(int(message.get('timestamp')))
                    existing_messages = WhatsAppMessage.objects.filter( wamid=wamid ).exclude(wamid="ABGGFlA5Fpa1")
                    print(f"existing_messages", str(existing_messages))
                    print(f"wamid", str(wamid))
                    if not existing_messages or settings.DEBUG:
                        print("REACHED past if not existing_messages or settings.DEBUG")
                        try:
                            lead = Campaignlead.objects.get(whatsapp_number__icontains=from_number[-10:])
                            # name = lead.name
                        except Exception as e:
                            lead = None
                        name = str(from_number)
                        # Likely a message from a customer     
                        lead = Campaignlead.objects.filter(whatsapp_number=from_number).last()
                        site = Site.objects.get(whatsapp_number=to_number)
                        whatsapp_message = WhatsAppMessage.objects.create(
                            wamid=wamid,
                            message = message.get('text').get('body',''),
                            datetime = datetime_from_request,
                            customer_number = from_number,
                            system_user_number = to_number,
                            inbound=True,
                            site=site,
                            lead=lead,
                        )
                        whatsapp_message.save()
                        group_name = f"chat_{from_number}_{site.pk}"
                        from channels.layers import get_channel_layer
                        channel_layer = get_channel_layer()
                        
                        logger.debug(f"webhook sending to chat start: groupname {group_name}") 
                        print(f"webhook sending to chat start: groupname {group_name}") 
                        async_to_sync(channel_layer.group_send)(
                            group_name,
                            {
                                'type': 'chatbox_message',
                                "message": message.get('text').get('body',''),
                                "user_name": name,
                                "inbound": True,
                            }
                        )
                        logger.debug("webhook sending to chat end")
                        print("webhook sending to chat end")
                        # .group_send)(
                        #     f"chat_{str(lead.pk)}",
                        #     {'text_data':json.dumps(
                        #         {
                        #             "message": message.message,
                        #             "user_name": lead.name,
                        #             "user_avatar": None,
                        #         }
                        #     )}
                        # )
                        
                        

                for status_dict in value.get('statuses', []):
                    whats_app_messages = WhatsAppMessage.objects.filter(wamid=status_dict.get('id'))
                    if whats_app_messages:
                        whatsapp_message_status = WhatsAppMessageStatus.objects.get_or_create(
                            whats_app_message=whats_app_messages[0],
                            datetime = datetime.fromtimestamp(int(status_dict.get('timestamp'))),
                            status = status_dict.get('status'),
                        )[0]
                        
        response = HttpResponse("")
        response.status_code = 200     
        
        return response