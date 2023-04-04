import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Campaign, Booking
from core.utils import normalize_phone_number
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
from datetime import datetime 
from core.views import get_and_create_contact_and_site_contact_for_lead
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEMO or settings.DEBUG:
            rukp = RandomUkPhone()
            for campaign in Campaign.objects.exclude(site=None):
            # for campaign in Campaign.objects.filter(company__demo=True):
                existing_campaigns = Campaignlead.objects.filter(archived=False, campaign=campaign, booking__isnull=True)
                # if existing_campaigns.count() < 5:
                lead = Campaignlead()
                refresh_position = True
                lead.campaign = campaign
                lead.first_name = names.get_first_name()
                lead.last_name = names.get_last_name()
                # lead.last_name = "demosurname"
                lead.email = "demo@winser.uk"
                lead.product_cost = campaign.product_cost
                lead.save()
                booking = Booking.objects.create(
                    datetime = datetime.now(),
                    lead = lead,
                    # type = booking_type,
                    user=campaign.company.profile_set.first().user
                )

                get_and_create_contact_and_site_contact_for_lead(lead, rukp.random_mobile())
                lead.trigger_refresh_websocket(refresh_position=refresh_position)
                lead.contact.company.get_company_cache().clear()
