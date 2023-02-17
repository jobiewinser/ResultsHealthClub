import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Campaign
from core.utils import normalize_phone_number
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
from core.views import get_and_create_contact_for_lead
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEMO or settings.DEBUG:
            rukp = RandomUkPhone()
            for campaign in Campaign.objects.filter():
            # for campaign in Campaign.objects.filter(company__demo=True):
                existing_campaigns = Campaignlead.objects.filter(archived=False).filter(campaign=campaign).exclude(booking__archived=False)
                if existing_campaigns.count() < 5:
                    lead = Campaignlead()
                    refresh_position = True
                    lead.campaign = campaign
                    lead.first_name = names.get_first_name()
                    lead.last_name = names.get_last_name()
                    # lead.last_name = "demosurname"
                    lead.email = "demo@winser.uk"
                    lead.product_cost = campaign.product_cost
                    lead.save()
                    get_and_create_contact_for_lead(lead, rukp.random_mobile())
                    lead.trigger_refresh_websocket(refresh_position=refresh_position)

