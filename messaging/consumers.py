import json
from channels.generic.websocket import AsyncWebsocketConsumer
from campaign_leads.models import Campaignlead
from core.models import Site

from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage
import logging
logger = logging.getLogger(__name__)
class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Connect Print")
        self.chat_box_whatsapp_number = self.scope["url_route"]["kwargs"]["chat_box_whatsapp_number"]
        self.chat_box_site_pk = self.scope["url_route"]["kwargs"]["chat_box_site_pk"]
        self.group_name = f"chat_{self.chat_box_whatsapp_number}_{self.chat_box_site_pk}"
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        user = self.scope["user"]
        if(user.is_authenticated and self.chat_box_whatsapp_number):
            if await send_whatsapp_message_to_number(message, self.chat_box_whatsapp_number, user, self.scope["url_route"]["kwargs"]["chat_box_site_pk"]):
                avatar, name = await message_details_user(user)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chatbox_message",
                        "message": message,
                        "user_name": name,
                        "user_avatar": avatar,
                        "inbound": False
                    },
                )
    # Receive message from room group.
    async def chatbox_message(self, event):
        message = event["message"]
        user_name = event.get("user_name", None)
        user_avatar = event.get("user_avatar", None)
        inbound = event.get("inbound", None)
        #send message and user of sender to websocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "user_name": user_name,
                    "user_avatar": user_avatar,
                    "inbound": inbound,
                }
            )
        )

    pass
from asgiref.sync import async_to_sync, sync_to_async

@sync_to_async
def send_whatsapp_message_to_number(message, whatsapp_number, user, site_pk):   
    logger.debug("send_whatsapp_message_to_number start") 
    lead = Campaignlead.objects.filter(whatsapp_number=whatsapp_number).first()  
    if lead:     
        if lead.active_campaign_list.site.get_company == user.profile.get_company: 
            logger.debug("send_whatsapp_message_to_number success lead true") 
            return Site.objects.get(pk = site_pk).send_whatsapp_message(customer_number=whatsapp_number, message=message, user=user, lead=lead)
    user_company_site_pk_list = Site.objects.filter(company__in=user.profile.company.all()).values_list('pk', flat=True)
    if WhatsAppMessage.objects.filter(customer_number=whatsapp_number, site__pk__in=user_company_site_pk_list):
        logger.debug("send_whatsapp_message_to_number success lead false") 
        return Site.objects.get(pk = site_pk).send_whatsapp_message(customer_number=whatsapp_number, message=message, user=user)
    logger.debug("send_whatsapp_message_to_number fail") 
    return False

@sync_to_async
def message_details_user(user):   
    logger.debug("message_details_user start")
    avatar = user.profile.avatar.url
    name = user.profile.name()
    return avatar, name