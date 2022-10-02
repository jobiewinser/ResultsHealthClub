from django.shortcuts import render

from campaign_leads.models import Campaignlead

def leads_message_window(request, **kwargs):
    lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))
    return render(request, "messaging/message_window_htmx.html", {"lead": lead})