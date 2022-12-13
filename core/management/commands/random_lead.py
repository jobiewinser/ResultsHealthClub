import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Campaign
from core.models import Site 
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEMO:
            rukp = RandomUkPhone()
            for campaign in Campaign.objects.all():
                existing_campaigns = Campaignlead.objects.filter(archived=False).filter(campaign=campaign).exclude(booking__archived=False)
                if existing_campaigns.count() < 20:
                    lead = Campaignlead()
                    refresh_position = True
                    lead.campaign = campaign
                    lead.first_name = names.get_first_name()
                    # lead.last_name = "demosurname"
                    lead.email = "demo@winser.uk"
                    lead.whatsapp_number = rukp.random_mobile()
                    lead.product_cost = campaign.product_cost
                    lead.save()
                    lead.trigger_refresh_websocket(refresh_position=refresh_position)

