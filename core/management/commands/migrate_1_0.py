import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Sale
from core.models import Site, Contact, SiteContact, WhatsAppNumber
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
        for contact in Contact.objects.all():
            contact.save()
        for customer_number in Contact.objects.all().values_list('customer_number', flat=True).distinct(): 
            if Contact.objects.filter(customer_number=customer_number).count() > 1:
                Contact.objects.filter(customer_number=customer_number).exclude(pk=Contact.objects.filter(customer_number=customer_number).first().pk).delete()
            
        for contact in Contact.objects.all():
            if contact.site_old:
                site_contact, created = SiteContact.objects.get_or_create(site=contact.site_old, contact=contact)
                site_contact.first_name = contact.first_name_old
                site_contact.last_name = contact.last_name_old
                site_contact.save()
                if not contact.company:
                    contact.company = contact.site_old.company
                    contact.save()
        for campaign_lead in Campaignlead.objects.all():
            #this will create contacts for all leads
            campaign_lead.save()
        for sale in Sale.objects.filter(archived=False):
            if not sale.archived and not sale.lead.arrived: #remove. this is to patch existing arrived leads
                sale.lead.arrived = True
                sale.lead.save                
        for whatsapp_message in WhatsAppMessage.objects.all():
            if not whatsapp_message.contact and whatsapp_message.lead:
                contact, site_contact = get_and_create_contact_and_site_contact_for_lead(whatsapp_message.lead, whatsapp_message.customer_number)
                whatsapp_message.contact = contact
                site_contact, created = SiteContact.objects.get_or_create(site=whatsapp_message.whatsappnumber.site, contact=contact)
                whatsapp_message.site_contact = site_contact
                whatsapp_message.save()
        for campaign_lead in Campaignlead.objects.all():
            if not campaign_lead.contact and campaign_lead.campaign and campaign_lead.whatsapp_number_old:
                contact, site_contact = get_and_create_contact_and_site_contact_for_lead(campaign_lead, campaign_lead.whatsapp_number_old)
                campaign_lead.contact = contact
            campaign_lead.save()
        for number in WhatsAppNumber.objects.all():
            number.save()