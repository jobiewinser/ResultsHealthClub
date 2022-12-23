from datetime import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from campaign_leads.models import Campaignlead
from core.models import Site, WhatsappNumber, SiteUsersOnline
from core.templatetags.core_tags import nice_datetime_tag
from django.template import loader
from core.user_permission_functions import get_user_allowed_to_use_site_messaging

from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage
import logging    
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.whatsappnumber_pk = self.scope["url_route"]["kwargs"]["whatsappnumber_pk"]
        self.group_name = f"messaging_{self.whatsappnumber_pk}"
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chatbox_message',
                'message': f"""<span hx-swap-oob="outerHTML:.messaging_disconnected_indicator">
                                            <div class="htmx-indicator disconnected_indicator messaging_disconnected_indicator">
                                                <b>Connecting</b> <img class="invert" src="/staticfiles/img/bars.svg">
                                            </div>
                                        </span>""",
            }
        )

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
            whatsappnumber = await get_whatsappnumber(self.scope["url_route"]["kwargs"]["whatsappnumber_pk"])
            
            if message:
                message_context = {
                    "message": message,
                    "whatsappnumber": whatsappnumber,
                }
                
                rendered_html = await get_rendered_html(message, message_context, messaging_customer_number, whatsappnumber)
                # rendered_html = await get_sending_rendered_html(message, message_context, messaging_customer_number, whatsappnumber)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chatbox_message',
                        "message": rendered_html,                       
                    }
                )
                company_pk = await get_user_company_pk(user)
                await self.channel_layer.group_send(
                    f"message_count_{company_pk}",
                    {
                        'type': 'messages_count_update',
                        'data':{
                            'rendered_html':f"""<span hx-swap-oob="afterbegin:.company_message_count"><span hx-trigger="load" hx-swap="none" hx-get="/update-message-counts/"></span>""",
                        }
                    }
                )
            else:
                
                rendered_html = await get_rendered_html_failed(messaging_customer_number, whatsappnumber)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chatbox_message',
                        "message": rendered_html,                       
                    }
                )
            await mark_past_messages_as_read(whatsappnumber, user, messaging_customer_number)
    # Receive message from room group.    
    async def chatbox_message(self, event):
        await self.send(
            text_data=event['message']
        )
        
        


def normalize_phone_number(number):
    if number[:2] == '44':
        number = '0' + number[2:]
    return number


@sync_to_async
def send_whatsapp_message_to_number(message, customer_number, user, whatsappnumber_pk):  
    customer_number = normalize_phone_number(customer_number)
    whatsappnumber = WhatsappNumber.objects.get(pk=whatsappnumber_pk)
    logger.debug("send_whatsapp_message_to_number start") 
    lead = Campaignlead.objects.filter(whatsapp_number=customer_number).first()  
    if get_user_allowed_to_use_site_messaging(user, whatsappnumber.site):
        if lead:     
            if whatsappnumber.site.company == user.profile.company: 
                logger.debug("send_whatsapp_message_to_number success lead true") 
                return whatsappnumber.send_whatsapp_message(customer_number=customer_number, message=message, user=user, lead=lead)

        if WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber, customer_number=customer_number):
            logger.debug("send_whatsapp_message_to_number success lead false") 
            return whatsappnumber.send_whatsapp_message(customer_number=customer_number, message=message, user=user)
        logger.debug("send_whatsapp_message_to_number fail") 
@sync_to_async
def message_details_user(user):   
    logger.debug("message_details_user start")
    avatar = user.profile.avatar.url
    name = user.profile.name
    return avatar, name
@sync_to_async
def get_whatsappnumber(whatsappnumber_pk):   
    return WhatsappNumber.objects.get(pk=whatsappnumber_pk)
@sync_to_async
def mark_past_messages_as_read(whatsappnumber, user, messaging_customer_number):   
    WhatsAppMessage.objects.filter(
        site=whatsappnumber.whatsapp_business_account.site,
        user=user,
        customer_number=messaging_customer_number,
        whatsappnumber=whatsappnumber,
    ).update(read=True)
@sync_to_async
def get_user_company_pk(user):   
    print(user.profile.company.pk)
    return user.profile.company.pk
# @sync_to_async
# def get_lead(lead_pk):   
#     return Campaignlead.objects.get(pk=lead_pk)
@sync_to_async
def get_rendered_html(message, message_context, messaging_customer_number, whatsappnumber):
    rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
    rendered_html = f"""
    <span id='latest_message_row_{messaging_customer_number}' hx-swap-oob='delete'></span>
    <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin'>{rendered_message_list_row}</span> #this line is clearing the whole message list?!
    <span id='messageWindowInnerBody_{messaging_customer_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>                
    """
    print(f"messageWindowInnerBody_{messaging_customer_number}")

    if message.inbound:
        rendered_html = f"""{rendered_html}
        <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
            <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                <span class="visually-hidden">New alerts</span>
            </span>
        </span>
        """
    else:
        rendered_html = f"""{rendered_html}
        <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
        </span>
        """
    return rendered_html
# @sync_to_async
# def get_sending_rendered_html(message, message_context, messaging_customer_number, whatsappnumber):
#     # rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
#     rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
#     rendered_html = f"""
#     <span id='messageWindowInnerBody_{messaging_customer_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>                
#     """

#     if message.inbound:
#         rendered_html = f"""{rendered_html}
#         <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
#             <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
#                 <span class="visually-hidden">New alerts</span>
#             </span>
#         </span>
#         """
#     else:
#         rendered_html = f"""{rendered_html}
#         <span hx-swap-oob="true" id="chat_notification_{message.customer_number}">
#         </span>
#         """
#     return rendered_html

@sync_to_async
def get_rendered_html_failed(messaging_customer_number, whatsappnumber):
    message_context = {
        "customer_number":messaging_customer_number,
        "whatsappnumber":whatsappnumber,
    }
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row_failed.html', message_context)
    rendered_html = f"""
    <span id='messageWindowInnerBody_{messaging_customer_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>                
    """

    rendered_html = f"""{rendered_html}"""
    return rendered_html

@sync_to_async
def add_user_to_users_online(consumer):  
    chat_object, created = SiteUsersOnline.objects.get_or_create(feature="leads", site=consumer.user.profile.site)
    chat_object.users_online = chat_object.users_online.replace(f"{consumer.user.pk};", '')+(str(consumer.user.pk)+";")
    chat_object.save()
    return f"""<div hx-swap-oob="true" id="users_online_leads">{loader.render_to_string('campaign_leads/htmx/connected_users.html', {'chat_object':chat_object})}</div> """
@sync_to_async
def remove_user_from_users_online(consumer):              
    chat_object = SiteUsersOnline.objects.get(feature="leads", site=consumer.user.profile.site)
    chat_object.users_online = chat_object.users_online.replace(f"{consumer.user.pk};", '')
    chat_object.save()
    return f"""<div hx-swap-oob="true" id="users_online_leads">{loader.render_to_string('campaign_leads/htmx/connected_users.html', {'chat_object':chat_object})}</div> """
class LeadsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.company_pk = self.scope["url_route"]["kwargs"]["company_pk"]
        self.group_name = f"lead_{self.company_pk}"
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
        else:

            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            
            rendered_html = await add_user_to_users_online(self)
            await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'lead_update',
                        'data':{
                            'rendered_html':rendered_html,
                        }                     
                    }
            )



            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'lead_update',
                    'data':{
                        'rendered_html':"""

                                            <div hx-swap-oob="outerHTML:.leads_disconnected_indicator">
                                                <div class="htmx-indicator whole_page_disconnected_indicator leads_disconnected_indicator">
                                                    <div class="whole_page_disconnected_indicator_content">
                                                        <b>Connecting</b> <img class="invert" src="/staticfiles/img/bars.svg">
                                                        
                                                        <script>
                                                            var elem = $('#leads_disconnected_indicator');
                                                            var user_id = $('#user_id').val();
                                                            
                                                            if (elem.hasClass('htmx-request')){
                                                                elem.removeClass('htmx-request');
                                                                htmx.ajax('GET', "/refresh-leads-board/", {include:'.overview_table_filters', indicator:'#page_load_indicator', swap:'outerHTML', target: '#leads_board_span_wrapper'})
                                                            }
                                                        </script>  
                                                    </div>
                                                    
                                                </div>
                                            </div>
                                            
                                            
                                            """,                        
                    }
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.user.is_anonymous:
            self.close()
        else:
            rendered_html = await remove_user_from_users_online(self)
            await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'lead_update',
                        'data':{
                            'rendered_html':rendered_html,
                        }                     
                    }
            )

    # This function receive messages from WebSocket.
    async def receive(self, text_data):        
        text_data_json = json.loads(text_data)
        user = self.scope["user"]
        if(user.is_authenticated):
            await self.channel_layer.group_send(
                self.group_name,    
                {
                    'type': 'lead_update',
                    "message": text_data_json["rendered_html"],
                }
            )

    # Receive message from room group.    
    async def lead_update(self, event):
        await self.send(
            text_data=event['data']['rendered_html']
        )
    # async def lead_move(self, event):
    #     await self.send(
    #         text_data=json.dumps({
    #             'message':event['data']['rendered_html']
    #             # 'message':"<span hx-swap-oob='afterbegin:.column'>TEST</span>"
    #         })
    #     )

    
class CompanyMessageCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.company_pk = self.scope["url_route"]["kwargs"]["company_pk"]
        self.group_name = f"message_count_{self.company_pk}"
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'messages_count_update',
                    'data':{
                        'rendered_html':f"""<span hx-swap-oob="outerHTML:.message_count_disconnected_indicator">
                                                <div class="htmx-indicator disconnected_indicator message_count_disconnected_indicator">
                                                    <b>Connecting</b> <img class="invert" src="/staticfiles/img/bars.svg">
                                                </div>
                                            </span>""",
                    }
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This function receive messages from WebSocket.
    # async def receive(self, text_data):        
    #     text_data_json = json.loads(text_data)
    #     user = self.scope["user"]
    #     if(user.is_authenticated):
    #         await self.channel_layer.group_send(
    #             self.group_name,
    #             {
    #                 'type': 'messages_count_update',
    #                 "message": text_data_json["rendered_html"],
    #             }
    #         )

    # Receive message from room group.    
    async def messages_count_update(self, event):
        await self.send(
            text_data=event['data']['rendered_html']
        )
        