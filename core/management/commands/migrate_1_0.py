import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Sale
from core.models import Site, Contact, SiteContact
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
from whatsapp.models import WhatsAppMessage
from core.utils import normalize_phone_number
from core.views import get_or_create_contact_for_lead
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        for contact in Contact.objects.all():
            if contact.site_old:
                site_contact, created = SiteContact.objects.get_or_create(site=contact.site_old, contact=contact)
                site_contact.first_name = contact.first_name_old
                site_contact.last_name = contact.last_name_old
        for campaign_lead in Campaignlead.objects.all():
            #this will create contacts for all leads
            campaign_lead.save()
        for sale in Sale.objects.filter(archived=False):
            if not sale.archived and not sale.lead.arrived: #remove. this is to patch existing arrived leads
                sale.lead.arrived = True
                sale.lead.save                
        for whatsapp_message in WhatsAppMessage.objects.all():
            if not whatsapp_message.contact and whatsapp_message.lead:
                contact = get_or_create_contact_for_lead(whatsapp_message.lead, whatsapp_message.customer_number)
                whatsapp_message.contact = contact
                if contact.site_old:
                    site_contact, created = SiteContact.objects.get_or_create(site=contact.site_old, contact=contact)
                    whatsapp_message.site_contact = site_contact
                
        