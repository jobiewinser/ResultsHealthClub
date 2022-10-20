from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render

from campaign_leads.models import Campaignlead
from core.models import Site, WhatsappNumber
from core.user_permission_functions import get_allowed_site_chats_for_user, get_user_allowed_to_use_site_messaging
from core.views import get_site_pk_from_request
from whatsapp.models import WhatsAppMessage
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger(__name__)


@login_required
def message_list(request, **kwargs):
    site = Site.objects.get(pk=request.GET.get('site_pk'))
    whatsappnumber = WhatsappNumber.objects.get(pk=request.GET.get('whatsappnumber_pk'))
    if get_user_allowed_to_use_site_messaging(request.user, site):
        context = {'chat_site':site, "whatsappnumber":whatsappnumber}
        return render(request, "messaging/messaging.html", context)

@login_required
def message_window(request, **kwargs):
    whatsappnumber = WhatsappNumber.objects.get(pk=kwargs.get('whatsappnumber_pk'))
    messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), whatsappnumber=whatsappnumber).order_by('datetime')[:20:-1]
    context = {}
    context["messages"] = messages
    context["lead"] = Campaignlead.objects.filter(whatsapp_number=kwargs.get('customer_number')).first()
    context["customer_number"] = kwargs.get('customer_number')
    context['whatsappnumber'] = whatsappnumber
    # messaging_phone_number = kwargs.get('messaging_phone_number')
    # if messaging_phone_number:
    #     context["system_phone_number"] = messaging_phone_number
    # else:
    #     numbers = request.user.profile.site.watsappnumber_set.all().value_list('number')
    #     latest_message = WhatsAppMessage.objects.filter

    return render(request, "messaging/message_window_htmx.html", context)

@login_required
def get_messaging_section(request, **kwargs):
    try:
        # request.GET._mutable = True
        # site = Site.objects.get(pk=request.GET.get('site_pk'))
        return render(request, f"messaging/messaging.html", {})   
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
        messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), whatsappnumber__number=kwargs.get('messaging_phone_number')).order_by('datetime')
        context = {}
        context["messages"] = messages
        context["lead"] = lead
        context["customer_number"] = lead.whatsapp_number
        context["site_pk"] = lead.campaign.site
        context['max_call_count'] = request.POST.get('max_call_count')
        return render(request, "campaign_leads/htmx/lead_article.html", context)
    except Exception as e:
        logger.debug("send_first_template_whatsapp_htmx Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        site_pk = get_site_pk_from_request(request)
        context = {}
        if site_pk:
            request.GET['site_pk'] = site_pk

        lead_pk = request.GET.get('lead_pk')
        if lead_pk:
            lead = Campaignlead.objects.get(pk=lead_pk)
            context['lead'] = lead
            if request.GET.get('template_name', None) == "message_window_modal":
                whatsappnumber = lead.campaign.site.default_number
                customer_number = lead.whatsapp_number
                context['customer_number'] = customer_number
                context['whatsappnumber'] = whatsappnumber
                context['messages'] = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber=whatsappnumber).order_by('-datetime')[:20:-1]
        
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            # context['site_list'] = get_available_sites_for_user(request.user)
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
                
            return render(request, f"messaging/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def get_more_messages(request, **kwargs):
    try:
        context = {}
        rendered_html = ""
        whatsappnumber = WhatsappNumber.objects.get(pk=request.GET.get('whatsappnumber_pk'))
        customer_number = request.GET.get('customer_number')
        created_before_date = datetime.fromtimestamp(float(request.GET.get('created_before_date')))
        context['customer_number'] = customer_number
        context['whatsappnumber'] = whatsappnumber
        context['created_before_date'] = created_before_date
        
        context['messages'] = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber=whatsappnumber, datetime__lt=created_before_date).order_by('-datetime')[:10:-1]   
        return render(request, "messaging/message_window_message_rows.html", context)   
    except Exception as e:
        logger.debug("get_more_messages Error "+str(e))
        return HttpResponse(e, status=500)
