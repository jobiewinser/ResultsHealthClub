import json
from channels.generic.websocket import AsyncWebsocketConsumer
from campaign_leads.models import Campaignlead

from whatsapp.api import Whatsapp

class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_box_name = self.scope["url_route"]["kwargs"]["chat_box_name"]
        self.group_name = "chat_%s" % self.chat_box_name
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
        if(user.is_authenticated and self.chat_box_name):
            if await send_whatsapp_message_to_lead(message, self.chat_box_name, user):            
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chatbox_message",
                        "message": message,
                        "user": user,
                    },
                )
    # Receive message from room group.
    async def chatbox_message(self, event):
        message = event["message"]
        user = event["user"]
        #send message and user of sender to websocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "user": user,
                }
            )
        )

    pass
from asgiref.sync import async_to_sync, sync_to_async

@sync_to_async
def send_whatsapp_message_to_lead(message, lead_pk, user):    
    lead = Campaignlead.objects.get(pk=lead_pk)
    print(lead.active_campaign_list.site.get_company)
    print(user.profile.get_company)
    if lead.active_campaign_list.site.get_company == user.profile.get_company:        
        return lead.send_whatsapp_message(message=message, user=user)
    return False