from django.shortcuts import render

from campaign_leads.models import Campaignlead
from whatsapp.models import WhatsAppMessage

def message_window(request, **kwargs):
    messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), site__pk=kwargs.get('chat_box_site_pk')).order_by('datetime')
    context = {}
    context["messages"] = messages
    context["lead"] = Campaignlead.objects.filter(whatsapp_number=kwargs.get('customer_number')).first()
    context["customer_number"] = kwargs.get('customer_number')
    context["site_pk"] = kwargs.get('chat_box_site_pk')
    return render(request, "messaging/message_window_htmx.html", context)