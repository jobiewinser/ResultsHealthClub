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
            if not whatsapp_messages.filter(inbound=True, datetime__gte=week_ago).exists():
                if not whatsapp_messages.filter(datetime__gte=day_ago).exists():
                    if not whatsapp_messages.filter(send_order=1).exists():
                        pass
                    #     campaign_lead.send_template_whatsapp_message(send_order=1)
                    #     campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=2).exists():
                        campaign_lead.send_template_whatsapp_message(send_order=2)
                        campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=3).exists():
                        campaign_lead.send_template_whatsapp_message(send_order=3)#
                        campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=4).exists():
                        campaign_lead.send_template_whatsapp_message(send_order=4)#
                        campaign_lead.trigger_refresh_websocket(refresh_position=False)
                    elif not whatsapp_messages.filter(send_order=5).exists():
                        campaign_lead.send_template_whatsapp_message(send_order=5)#
                        campaign_lead.trigger_refresh_websocket(refresh_position=False)