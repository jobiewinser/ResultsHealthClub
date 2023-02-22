import logging
from django.core.management.base import BaseCommand
from campaign_leads.models import Campaignlead, Booking, Call, Note, WhatsappTemplate
logger = logging.getLogger(__name__)
from whatsapp.models import WhatsAppMessage
from datetime import datetime, timedelta
class Command(BaseCommand):
    help = 'help text'

    def handle(self, *args, **options):
        for campaign_lead in Campaignlead.objects.filter(booking=None).exclude(sale__archived=True).exclude(archived=True).exclude(disabled_automated_messaging=True):
            whatsapp_messages = WhatsAppMessage.objects.filter(site_contact=campaign_lead.site_contact)
            day_ago =  datetime.now() - timedelta(days = 1)
            week_ago =  datetime.now() - timedelta(days = 7)
            if not whatsapp_messages.filter(inbound=True, datetime__gte=campaign_lead.created).exists(): #never send a message if they have sent us a message since the lead was created. 
                #Basically they could have sent a message saying i'm not interested that we haven'y seen and archived yet
                
                if not whatsapp_messages.filter(datetime__gte=day_ago).exists(): #never send an auto message if they have sent a message within 24 hours, will ruin the conversation
                    if not whatsapp_messages.filter(send_order=1).exists():
                        pass
                    #     campaign_lead.send_template_whatsapp_message(send_order=1)
                    #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=2).exists():
                        print(2)
                        # campaign_lead.send_template_whatsapp_message(send_order=2)
                        # campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=3).exists():
                        print(3)
                        # campaign_lead.send_template_whatsapp_message(send_order=3)#
                        # campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=4).exists():
                        print(4)
                        # campaign_lead.send_template_whatsapp_message(send_order=4)#
                        # campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=5).exists():
                        print(5)
                        # campaign_lead.send_template_whatsapp_message(send_order=5)#
                        # campaign_lead.trigger_refresh_websocket(refresh_position=False)