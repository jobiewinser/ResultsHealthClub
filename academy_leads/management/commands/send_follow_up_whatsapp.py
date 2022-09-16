import logging
from django.core.management.base import BaseCommand
from academy_leads.models import AcademyLead, Booking, Communication, Note, WhatsappTemplate, communication_choices_dict
logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = 'help text'

    def handle(self, *args, **options):
        for academy_lead in AcademyLead.objects.filter(booking=None,sold=False,complete=False):
            print("")
            print(academy_lead.pk)