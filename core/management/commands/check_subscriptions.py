import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.models import Site 
import requests
import random as r
import json
from random_phone import RandomUkPhone
import names
from stripe_integration.api import *
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        temp1 = retrieve_subscription_list()
        print()

