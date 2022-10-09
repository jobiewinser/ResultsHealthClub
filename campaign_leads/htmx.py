from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required

from campaign_leads.models import Campaign, Campaignlead, Booking, Call, Note
from campaign_leads.views import CampaignBookingsOverviewView
from core.models import Site
from core.views import get_site_pk_from_request
from django.db.models import Q, Count
from django.contrib import messages
logger = logging.getLogger(__name__)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            context = {'site_list':Site.objects.all()}
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
                
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)



@login_required
def create_campaign_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        first_name = request.POST.get('first_name')
        if not first_name:
            return HttpResponse("Please provide a first name", status=500)
        
        phone = request.POST.get('phone')
        if not phone:
            return HttpResponse("Please provide a valid Phone Number", status=500)
        
        country_code = request.POST.get('countryCode')
        if not country_code:
            return HttpResponse("Please provide a Country Code", status=500)
        
        site = Site.objects.get(pk=request.POST.get('site_pk'))        
        if not first_name:
            return HttpResponse("Please provide a Choice of Site", status=500)

        lead = site.generate_lead(first_name, f"{country_code}{phone}", request=request)
        
        context = {'lead':lead,'max_call_count':1,'call_count':0, 'site':site}
        return render(request, 'campaign_leads/htmx/lead_article.html', context)
    except Exception as e:
        # messages.add_message(request, messages.ERROR, f'Error with creating a campaign lead')
        logger.debug("create_campaign_lead Error "+str(e))
        # raise Exception
        return HttpResponse("Error with creating a campaign lead", status=500)
@login_required
def get_leads_column_meta_data(request, **kwargs):
    logger.debug(str(request.user))
    try:
        leads = Campaignlead.objects.filter(complete=False, booking=None)
        campaign_pk = request.GET.get('campaign_pk', None)
        if campaign_pk:
            leads = leads.filter(campaign=Campaign.objects.get(pk=campaign_pk))
            # request.GET['campaign_pk'] = campaign_pk
        site_pk = get_site_pk_from_request(request)
        if site_pk and not site_pk == 'all':
            leads = leads.filter(campaign__site__pk=site_pk)
            # request.GET['site_pk'] = site_pk 
            
        leads = leads.annotate(calls=Count('call'))
        querysets = [
            ('Fresh', leads.filter(calls=0), 0)
        ]
        index = 0
        if leads.filter(calls__gt=index):
            while leads.filter(calls__gt=index):
                index = index + 1
                querysets.append(
                    (f"Call {index}", leads.filter(calls=index), index)
                )
        else:
            querysets.append(
                (f"Call 1", leads.none(), 1)
            )
        return render(request, 'campaign_leads/htmx/column_metadata_htmx.html', {'querysets':querysets})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def add_booking(request, **kwargs):
    logger.debug(str(request.user))
    try:        
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        if (request.POST.get('booking_type', 'off') == 'on'):
            booking_type = 'a'
        else:
            booking_type = 'b'
        booking_datetime = datetime.strptime(f"{booking_date} {booking_time}", '%Y-%m-%d %H:%M')
        booking = Booking.objects.create(
            datetime = booking_datetime,
            lead = lead,
            type = booking_type,
            user=request.user
        )

        note = request.POST.get('note','')
        if note:
            Note.objects.create(
                booking=booking,
                lead=lead,
                text=note,
                user=request.user,
                datetime=booking_datetime
                )
                
        context = {
            'lead': lead,
        }
        
        return HttpResponse("<span></span>", status=200) 
    except Exception as e:
        logger.debug("add_booking Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_done(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
            lead.complete = not lead.complete
            lead.save()

            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def new_leads_column(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            max_call_count = int(request.GET.get('max_call_count', 1))+2
            querysets = [
                (f"Call {max_call_count}", Campaignlead.objects.none(), max_call_count)
            ]
            return render(request, 'campaign_leads/htmx/lead_columns.html', {'querysets':querysets, 'max_call_count':max_call_count-1})
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def delete_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
            lead.delete()

            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def mark_arrived(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
            lead.arrived = not lead.arrived
            lead.save()
            return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_sold(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
            lead.sold = not lead.sold
            lead.complete = not lead.complete
            lead.save()
            return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)
        
# @login_required
# def test_whatsapp_message(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
#             lead.send_whatsapp_message('testing api', request.user)
#             return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
#     except Exception as e:
#         logger.debug("mark_done Error "+str(e))
# #         return HttpResponse(e, status=500)
# @login_required
# def template_editor(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             template = WhatsappTemplate.objects.get(pk=request.GET.get('template_pk'))
#             return render(request, "campaign_leads/htmx/template_editor.html", {'template':template}) 
#     except Exception as e:
#         logger.debug("mark_done Error "+str(e))
#         return HttpResponse(e, status=500)

# @login_required
# def template_save(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
#             template.text = request.POST.get('template_text')
#             template.save()
#             return render(request, "campaign_leads/htmx/template_editor.html", {'template':template}) 
#     except Exception as e:
#         logger.debug("mark_done Error "+str(e))
#         return HttpResponse(e, status=500)

        