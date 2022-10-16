from datetime import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from campaign_leads.models import Campaignlead
from core.models import Site, WhatsappNumber
from core.templatetags.core_tags import nice_datetime_tag
from django.template import loader

from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage
import logging    
from channels.layers import get_channel_layer
logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.whatsappnumber_pk = self.scope["url_route"]["kwargs"]["whatsappnumber_pk"]
        self.group_name = f"messaging_{self.whatsappnumber_pk}"
        self.user = self.scope["user"]
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This function receive messages from WebSocket.
    async def receive(self, text_data):        
        text_data_json = json.loads(text_data)
        input_message = text_data_json["message"]
        messaging_customer_number = text_data_json["messaging_customer_number"]
        user = self.scope["user"]
        if(user.is_authenticated):
            message = await send_whatsapp_message_to_number(input_message, messaging_customer_number, user, self.scope["url_route"]["kwargs"]["whatsappnumber_pk"])
            if message:
                whatsappnumber = await get_whatsappnumber(self.scope["url_route"]["kwargs"]["whatsappnumber_pk"])
                message_context = {
                    "message": message,
                    "whatsappnumber": whatsappnumber,
                }
                
                rendered_htmx = await get_rendered_htmx(message, message_context, messaging_customer_number, whatsappnumber)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chatbox_message',
                        "message": rendered_htmx,
                    }
                )
    # Receive message from room group.    
    async def chatbox_message(self, event):
        await self.send(
            text_data=event['message']
        )
from asgiref.sync import async_to_sync, sync_to_async
@sync_to_async
def send_whatsapp_message_to_number(message, customer_number, user, whatsappnumber_pk):  
    if settings.ENABLE_WHATSAPP_MESSAGING:
        whatsappnumber = WhatsappNumber.objects.get(pk=whatsappnumber_pk)
        logger.debug("send_whatsapp_message_to_number start") 
        lead = Campaignlead.objects.filter(whatsapp_number=customer_number).first()  
        if lead:     
            if lead.campaign.site.company == user.profile.company: 
                logger.debug("send_whatsapp_message_to_number success lead true") 
                return whatsappnumber.send_whatsapp_message(customer_number=customer_number, message=message, user=user, lead=lead)

        if WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber, customer_number=customer_number):
            logger.debug("send_whatsapp_message_to_number success lead false") 
            return whatsappnumber.send_whatsapp_message(customer_number=customer_number, message=message, user=user)
        logger.debug("send_whatsapp_message_to_number fail") 
        return None
    return None
@sync_to_async
def message_details_user(user):   
    logger.debug("message_details_user start")
    avatar = user.profile.avatar.url
    name = user.profile.name()
    return avatar, name
@sync_to_async
def get_whatsappnumber(whatsappnumber_pk):   
    return WhatsappNumber.objects.get(pk=whatsappnumber_pk)
# @sync_to_async
# def get_lead(lead_pk):   
#     return Campaignlead.objects.get(pk=lead_pk)
@sync_to_async
def get_rendered_htmx(message, message_context, messaging_customer_number, whatsappnumber):
    rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
    rendered_htmx = f"""
    <span id='message_list_row_{messaging_customer_number}_{whatsappnumber.pk}' hx-swap-oob='delete'></span>
    <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin '>{rendered_message_list_row}</span>
    <span id='messageWindowCollapse_{messaging_customer_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>                
    """

    if message.inbound:
        rendered_htmx = f"""{rendered_htmx}
        <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
            <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                <span class="visually-hidden">New alerts</span>
            </span>
        </span>
        """
    else:
        rendered_htmx = f"""{rendered_htmx}
        <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
        </span>
        """
    return rendered_htmx

    
class LeadsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.company_pk = self.scope["url_route"]["kwargs"]["company_pk"]
        self.group_name = f"lead_{self.company_pk}"
        self.user = self.scope["user"]
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This function receive messages from WebSocket.
    async def receive(self, text_data):        
        text_data_json = json.loads(text_data)
        user = self.scope["user"]
        if(user.is_authenticated):
            lead_pk = text_data_json["lead_pk"]
            new_position = text_data_json["new_position"]
            
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'lead_update',
                    "message": get_leads_htmx(lead_pk, new_position=new_position),
                }
            )

    # Receive message from room group.    
    async def lead_update(self, event):
        message = await get_leads_htmx(event['data']['lead_pk'])
        await self.send(
            text_data=json.dumps({
                'message':message
            })
        )

@sync_to_async
def get_leads_htmx(lead_pk, new_position=None):
    # new_position = text_data_json["new_position"]
    if lead_pk:
        if not new_position:    
            return f"<span hx-swap-oob='delete' id='lead-{lead_pk}'></span>"
            # await self.channel_layer.group_send(
            #     self.group_name,
            #     {
            #         'type': 'lead_update',
            #         "message": f"<span hx-swap-oob='delete' id='lead-{lead_pk}'></span>",
            #     }
            # )
        else:
            lead = Campaignlead.objects.get(pk=lead_pk) 
            message_context = {
                "messaleadge": lead,
                "site": lead.campaign.site,
            }
            rendered_message_list_row = loader.render_to_string('campaign_leads/htmx/lead_article.html', message_context)
            rendered_htmx = f"""
                <span id='lead-{lead_pk}' hx-swap-oob='outerHTML'>{rendered_message_list_row}</span>           
            """
            return rendered_htmx
            
            # await self.channel_layer.group_send(
            #     self.group_name,
            #     {
            #         'type': 'lead_update',
            #         "message": rendered_htmx,
            #     }
            # )

