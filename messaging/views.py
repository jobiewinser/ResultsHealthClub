from django.http import HttpResponse
from django.shortcuts import render

from campaign_leads.models import Campaignlead
from core.models import Site
from whatsapp.models import WhatsAppMessage
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger(__name__)

@login_required
def message_window(request, **kwargs):
    messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), site__pk=kwargs.get('chat_box_site_pk')).order_by('datetime')
    context = {}
    context["messages"] = messages
    context["lead"] = Campaignlead.objects.filter(whatsapp_number=kwargs.get('customer_number')).first()
    context["customer_number"] = kwargs.get('customer_number')
    context["site_pk"] = kwargs.get('chat_box_site_pk')
    return render(request, "messaging/message_window_htmx.html", context)

@login_required
def get_messaging_section(request, **kwargs):
    try:
        request.GET._mutable = True
        site = Site.objects.get(pk=request.GET.get('site_pk'))
        return render(request, f"messaging/messaging.html", {'site':site})   
    except Exception as e:
        logger.debug("get_messaging_section Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def get_messaging_list_row(request, **kwargs):
    try:
        request.GET._mutable = True
        site = Site.objects.get(pk=request.GET.get('site_pk'))
        message = WhatsAppMessage.objects.filter(site=site, customer_number=request.GET.get('whatsapp_number')).last()
        return render(request, "messaging/htmx/message_list_row.html", {'site':site, 'message':message})   
    except Exception as e:
        logger.debug("get_messaging_list_row Error "+str(e))
        return HttpResponse(e, status=500)

