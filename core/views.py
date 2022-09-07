from sys import version
from django.views.generic import TemplateView
from django.views import View
from django.http import HttpResponse
import os

import asyncio
# from kasa import SmartPlug
from asgiref.sync import sync_to_async
import datetime
from django.shortcuts import render
from django.db.models import Sum
from django.http import JsonResponse
import logging
from django.db.models import F  
logger = logging.getLogger(__name__)

