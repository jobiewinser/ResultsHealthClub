from datetime import datetime, timedelta
import logging
from django.conf import settings
from django.http import HttpResponse, QueryDict
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaign, Campaignlead, Call

from core.views import get_site_pk_from_request
from messaging.models import Message
from whatsapp.api import Whatsapp
from django.views.generic import TemplateView
from whatsapp.models import WHATSAPP_ORDER_CHOICES, WhatsAppMessage, WhatsAppMessageStatus, WhatsAppWebhookRequest, WhatsappMessageImage, WhatsappTemplate, template_variables
from django.template import loader
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel, Site, WhatsappNumber
from random import randrange
from django.contrib.auth.decorators import login_required

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            if template_name == 'add_phone_number':
                site_pk = request.GET.get('site_pk', None)
            if site_pk:
                context["site"] = Site.objects.get(pk=site_pk)
            
            return render(request, f"whatsapp/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)