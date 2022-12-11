import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from campaign_leads.models import Campaignlead, Campaign
from core.models import Site 
import requests
import random as r
import json
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEMO:
            for campaign in Campaign.objects.all():
                
                lead = Campaignlead()
                refresh_position = True
                lead.campaign = campaign
                lead.first_name = "demoname"
                lead.last_name = "demosurname"
                lead.email = "demo@winser.uk"
                lead.whatsapp_number = f"449832783216"
                lead.product_cost = campaign.product_cost
                lead.save()
                lead.trigger_refresh_websocket(refresh_position=refresh_position)