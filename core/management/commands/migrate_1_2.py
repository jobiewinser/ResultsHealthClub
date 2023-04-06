import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Sale, Booking, CampaignTemplateLink
from core.models import Site, Contact, SiteContact, WhatsappNumber
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
from whatsapp.models import WhatsAppMessage
from core.utils import normalize_phone_number
from core.views import get_and_create_contact_and_site_contact_for_lead
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaigntemplatelink in CampaignTemplateLink.objects.all():
            campaigntemplatelink.method = 'time'
            campaigntemplatelink.time_interval = 1
            campaigntemplatelink.send_order = campaigntemplatelink.send_order - 1
            campaigntemplatelink.save()