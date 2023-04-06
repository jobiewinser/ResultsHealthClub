import logging
from django.core.management.base import BaseCommand
from campaign_leads.models import Campaignlead, Booking, Call, Note, WhatsappTemplate
logger = logging.getLogger(__name__)
from whatsapp.models import WhatsAppMessage
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count
class Command(BaseCommand):
    help = 'help text'

    def handle(self, *args, **options):
        for campaign_lead in Campaignlead.objects.filter(booking=None).exclude(campaign=None).exclude(sale__archived=True).exclude(archived=True).exclude(disabled_automated_messaging=True).annotate(calls=Count('call')):
            whatsapp_messages = WhatsAppMessage.objects.filter(site_contact=campaign_lead.site_contact)
            ten_minutes_ago =  datetime.now() - timedelta(minutes = 10)
            day_ago =  datetime.now() - timedelta(days = 1)
            week_ago =  datetime.now() - timedelta(days = 7)
            if settings.DEBUG:
                ten_minutes_ago =  datetime.now() - timedelta(minutes = 0)
                day_ago =  datetime.now() - timedelta(days = 0)
            now =  datetime.now()
            if not Call.objects.filter(lead = campaign_lead, datetime__gt=ten_minutes_ago): #check if call is made within last 10 mins
                if not whatsapp_messages.filter(inbound=True, datetime__gte=week_ago).exists(): #check if they have messaged us within a week
                    if not whatsapp_messages.filter(datetime__gte=day_ago).exists(): #check if we have messaged them in the last day
                        # if not whatsapp_messages.filter(send_order=1).exists():
                        #     pass
                        #     campaign_lead.send_template_whatsapp_message(send_order=1)
                        #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                        # else:
                            campaigntemplatelinks = campaign_lead.campaign.campaigntemplatelink_set.all()
                            if campaigntemplatelinks.exists():
                                method = campaigntemplatelinks.order_by('-send_order').first().method
                                
                                
                                previous_auto_message = None
                                for campaigntemplatelink in campaigntemplatelinks.filter(send_order__gt=0):
                                    if not whatsapp_messages.filter(send_order=campaigntemplatelink.send_order).exists():
                                        if not previous_auto_message: #if there's no messages to worry about vefore this one, just send
                                            campaign_lead.send_template_whatsapp_message(send_order=campaigntemplatelink.send_order)
                                            campaign_lead.trigger_refresh_websocket(refresh_position=False)
                                        else:
                                            if method == 'time':
                                                previous_auto_message_send_time = previous_auto_message.datetime #the time that the previous template was sent
                                                if previous_auto_message_send_time < (now - timedelta(days=campaigntemplatelink.time_interval)): # If the previous template was x amount of days ago
                                                    campaign_lead.send_template_whatsapp_message(send_order=campaigntemplatelink.send_order) #send adn refresh
                                                    campaign_lead.trigger_refresh_websocket(refresh_position=False)
                                            elif method == 'call':
                                                if campaign_lead.calls >= campaigntemplatelink.call_interval:  #if enough calls have been made for this template link to be satisfied, 
                                                    campaign_lead.send_template_whatsapp_message(send_order=campaigntemplatelink.send_order) #send adn refresh
                                                    campaign_lead.trigger_refresh_websocket(refresh_position=False)
                                        break #break if this the next template to send, regardless of whether we send in the logic above or not
                                    previous_auto_message = campaigntemplatelink
                                    
                        # elif not whatsapp_messages.filter(send_order=2).exists():
                        #     campaign_lead.send_template_whatsapp_message(send_order=2)
                        #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                        # elif not whatsapp_messages.filter(send_order=3).exists():
                        #     campaign_lead.send_template_whatsapp_message(send_order=3)#
                        #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                        # elif not whatsapp_messages.filter(send_order=4).exists():
                        #     campaign_lead.send_template_whatsapp_message(send_order=4)#
                        #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                        # elif not whatsapp_messages.filter(send_order=5).exists():
                        #     campaign_lead.send_template_whatsapp_message(send_order=5)#
                        #     campaign_lead.trigger_refresh_websocket(refresh_position=False)