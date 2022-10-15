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
    messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), system_user_number=kwargs.get('messaging_phone_number')).order_by('datetime')
    context = {}
    context["messages"] = messages
    context["lead"] = Campaignlead.objects.filter(whatsapp_number=kwargs.get('customer_number')).first()
    context["customer_number"] = kwargs.get('customer_number')
    messaging_phone_number = kwargs.get('messaging_phone_number')
    if messaging_phone_number:
        context["system_phone_number"] = messaging_phone_number
    else:
        numbers = request.user.profile.site.watsappnumber_set.all().value_list('number')
        latest_message = WhatsAppMessage.objects.filter

    return render(request, "messaging/message_window_htmx.html", context)

@login_required
def get_messaging_section(request, **kwargs):
    try:
        # request.GET._mutable = True
        site = Site.objects.get(pk=request.GET.get('site_pk'))
        return render(request, f"messaging/messaging.html", {'site':site})   
    except Exception as e:
        logger.debug("get_messaging_section Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def get_messaging_list_row(request, **kwargs):
    try:
    #     request.GET._mutable = True
        site = Site.objects.get(pk=request.GET.get('site_pk'))
        message = WhatsAppMessage.objects.filter(site=site, customer_number=request.GET.get('whatsapp_number')).last()
        return render(request, "messaging/htmx/message_list_row.html", {'site':site, 'message':message})   
    except Exception as e:
        logger.debug("get_messaging_list_row Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def send_first_template_whatsapp_htmx(request, **kwargs):
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))
        if not lead.message_set.all():
            lead.send_template_whatsapp_message(1, communication_method='a')
        messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), system_user_number=kwargs.get('messaging_phone_number')).order_by('datetime')
        context = {}
        context["messages"] = messages
        context["lead"] = lead
        context["customer_number"] = lead.whatsapp_number
        context["site_pk"] = lead.campaign.site
        return render(request, "messaging/message_window_htmx.html", context)
    except Exception as e:
        logger.debug("send_first_template_whatsapp_htmx Error "+str(e))
        return HttpResponse(e, status=500)

