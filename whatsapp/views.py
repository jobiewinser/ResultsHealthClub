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
        x = 0
        x = x+1
        print(x)
        for entry in body.get('entry'):
            x = x+1
            print(x)
            for change in entry.get('changes'):
                x = x+1
                print(x)
                value = change.get('value')
                x = x+1
                print(x)
                for message in value.get('messages', []):
                    x = x+1
                    print(x)
                    metadata = value.get('metadata')
                    x = x+1
                    print(x)
                    wamid = message.get('id')
                    x = x+1
                    print(x)
                    to_number = metadata.get('display_phone_number')
                    x = x+1
                    print(x)
                    from_number = message.get('from')
                    x = x+1
                    print(x)
                    datetime_from_request = datetime.fromtimestamp(int(message.get('timestamp')))
                    x = x+1
                    print(x)
                    existing_messages = WhatsAppMessage.objects.filter( wamid=wamid ).exclude(wamid=1)
                    x = x+1
                    print(x)
                    if not existing_messages or settings.DEBUG:
                        print("REACHED past if not existing_messages or settings.DEBUG")
                        x = x+1
                        print(x)
                        try:
                            lead = Campaignlead.objects.get(whatsapp_number__icontains=from_number[-10:])
                            # name = lead.name
                        except Exception as e:
                            lead = None
                        name = str(from_number)
                        x = x+1
                        print(x)
                        # Likely a message from a customer     
                        lead = Campaignlead.objects.filter(whatsapp_number=from_number).last()
                        x = x+1
                        print(x)
                        site = Site.objects.get(whatsapp_number=to_number)
                        x = x+1
                        print(x)
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
                        x = x+1
                        print(x)
                        whatsapp_message.save()
                        x = x+1
                        print(x)
                        group_name = f"chat_{from_number}_{site.pk}"
                        x = x+1
                        print(x)
                        from channels.layers import get_channel_layer
                        x = x+1
                        print(x)
                        channel_layer = get_channel_layer()
                        x = x+1
                        print(x)
                        
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