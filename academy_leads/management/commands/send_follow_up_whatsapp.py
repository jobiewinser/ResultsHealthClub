import logging
from django.core.management.base import BaseCommand
from academy_leads.models import AcademyLead, Booking, Communication, Note, WhatsappTemplate, communication_choices_dict
logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = 'help text'

    def handle(self, *args, **options):
        for academy_lead in AcademyLead.objects.filter(booking=None).exclude(sold=True).exclude(complete=True).exclude(communication__whatsappmessage__template__send_order=3):
            if not academy_lead.communication_set.filter(whatsappmessage__template__send_order=1):
                academy_lead.send_whatsapp_message(1, user=None)
            elif not academy_lead.communication_set.filter(whatsappmessage__template__send_order=2):
                academy_lead.send_whatsapp_message(2, user=None)
            else:
                academy_lead.send_whatsapp_message(3, user=None)