from django.shortcuts import render

from datetime import datetime, timezone
import logging
from django.conf import settings
from django.http import HttpResponse, QueryDict
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pytz
from calendly.api import Calendly
from calendly.models import CalendlyWebhookRequest
from campaign_leads.models import Booking, Campaignlead
from whatsapp.api import Whatsapp
from django.views.generic import TemplateView
from whatsapp.models import WHATSAPP_ORDER_CHOICES, WhatsAppMessage, WhatsAppMessageStatus, WhatsAppWebhookRequest, WhatsappTemplate, template_variables
from django.template import loader
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
import time
@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        return HttpResponse("", status = 200)

    def post(self, request, *args, **kwargs):
        time.sleep(5)
        try:
            body = json.loads(request.body)
            # meta = request.META
            # print(str(body))
            logger.debug(str(body))
            
            webhook = CalendlyWebhookRequest.objects.create(
                json_data=body,
                # meta_data=meta,
                request_type='a',
            )
            if body.get('event') == "invitee.created":
                try:
                    event_url = body.get('payload').get('event')
                    event_uuid = event_url.split('/')[-1]
                    booking = Booking.objects.get(calendly_event_uri__icontains=event_uuid)
                    calendly = Calendly(booking.lead.campaign.site.calendly_token)
                    updated_booking_details = calendly.get_from_uri(event_url)
                    print("CALENDLY Webhooks updated_booking_details", str(updated_booking_details))
                    start_time = datetime.strptime(updated_booking_details['resource']['start_time'][0:19], '%Y-%m-%dT%H:%M:%S')
                    
                    timezone = pytz.timezone('Europe/London')
                    start_time = timezone.localize(start_time)

                    booking.datetime = start_time
                    booking.save()            
                    
                    return HttpResponse("", status=200)
                except Exception as e:            
                    print("CALENDLY Webhooks post except Exception as e", str(e)) 
                    error = ErrorModel.objects.create(json_data={'error':str(e)})
                    webhook.errors.add(error)
                    webhook.save()
                    # raise Exception     
            elif body.get('event') == "invitee.canceled":
                try:
                    event_url = body.get('payload').get('event')
                    booking = Booking.objects.get(calendly_event_uri=event_url)                    
                    booking.archived = True
                    booking.save()     
                    # TODO Notification here                           
                    return HttpResponse("", status=200)
                except Exception as e:            
                    print("CALENDLY Webhooks post except Exception as e", str(e)) 
                    error = ErrorModel.objects.create(json_data={'error':str(e)})
                    webhook.errors.add(error)
                    webhook.save()
                    # raise Exception                
            return HttpResponse("", status=400)
            
        except ObjectDoesNotExist:               
            print("CALENDLY Webhooks post ObjectDoesNotExist body", str(body)) 
            return HttpResponse("", status=400)

@login_required
def calendly_booking_success(request):
    lead = Campaignlead.objects.get(pk = request.POST['lead_pk'])
    uri = request.POST['uri']
    # if lead.campaign.site.company == request.user.profile.company:
    booking = Booking.objects.create(user=request.user, calendly_event_uri=uri, lead=lead)
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()          
    lead = booking.lead
    company_pk = lead.campaign.site.company.pk   
    rendered_html = f"<span hx-swap-oob='delete' id='lead-{lead.pk}'></span> <span hx-swap-oob='outerHTML:.booking-lead-{lead.pk}'><span hx-get='/refresh-booking-row/{lead.pk}/' hx-swap='innerHTML' hx-target='#row_{lead.pk}' hx-indicator='#top-htmx-indicator' hx-trigger='load'></span></span>"
    async_to_sync(channel_layer.group_send)(
        f"lead_{company_pk}",
        {
            'type': 'lead_update',
            'data':{
                # 'company_pk':campaign_pk,
                'rendered_html': rendered_html,
            }
        }
    )
    return HttpResponse("", status=200)