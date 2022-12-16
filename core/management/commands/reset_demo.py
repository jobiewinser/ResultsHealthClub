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
            Campaignlead.objects.filter(campaign__company__demo=True).delete()
