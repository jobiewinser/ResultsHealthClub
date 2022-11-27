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
from core.models import Site, WhatsappNumber
from core.user_permission_functions import get_available_sites_for_user, get_user_allowed_to_add_call
from core.views import get_site_pk_from_request
from django.db.models import Q, Count
from django.contrib import messages
from asgiref.sync import async_to_sync

from whatsapp.models import WhatsappTemplate
logger = logging.getLogger(__name__) 

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        site_pk = get_site_pk_from_request(request)
        context = {}
        if site_pk:
            request.GET['site_pk'] = site_pk
        whatsapp_template_pk = request.GET.get('whatsapp_template_pk')
        if whatsapp_template_pk:
            context['template'] = WhatsappTemplate.objects.get(pk=whatsapp_template_pk)

        whatsappnumber_pk = request.GET.get('whatsappnumber_pk')
        if whatsappnumber_pk:
            context['whatsappnumber'] = WhatsappNumber.objects.get(pk=whatsappnumber_pk)
        
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            # context['site_list'] = get_available_sites_for_user(request.user)
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
                
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)



@login_required
def create_campaign_lead(request, **kwargs):
    # logger.debug(str(request.user))
    # try:
        first_name = request.POST.get('first_name')
        if not first_name:
            return HttpResponse("Please provide a first name", status=500)

        email = request.POST.get('email')
        # if not email:
        #     return HttpResponse("Please provide a email", status=500)
        
        phone = request.POST.get('phone')
        if not phone:
            return HttpResponse("Please provide a valid Phone Number", status=500)
        
        country_code = request.POST.get('country_code')
        if not country_code:
            return HttpResponse("Please provide a Country Code", status=500)
        
        site = Site.objects.get(pk=request.POST.get('site_pk'))        
        if not first_name:
            return HttpResponse("Please provide a Choice of Site", status=500)

        lead = site.generate_lead(first_name, email, f"{country_code}{phone}", request=request)
        
        context = {'lead':lead,'max_call_count':1,'call_count':0, 'site':site}
        return render(request, 'campaign_leads/htmx/lead_article.html', context)
    # except Exception as e:
    #     # messages.add_message(request, messages.ERROR, f'Error with creating a campaign lead')
    #     logger.debug("create_campaign_lead Error "+str(e))
    #     # raise Exception
    #     return HttpResponse("Error with creating a campaign lead", status=500)
@login_required
def get_leads_column_meta_data(request, **kwargs):
    logger.debug(str(request.user))
    try:
        leads = Campaignlead.objects.filter(archived=False, booking=None, campaign__site__in=request.user.profile.sites_allowed.all())
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
        # if leads.filter(calls__gt=index):
        while leads.filter(calls__gt=index) or index < 21:
            index = index + 1
            querysets.append(
                (f"Call {index}", leads.filter(calls=index), index)
            )
        # else:
        #     querysets.append(
        #         (f"Call 1", leads.none(), 1)
        #     )
        return render(request, 'campaign_leads/htmx/column_metadata_htmx.html', {'querysets':querysets})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        return HttpResponse(e, status=500)
@login_required
def refresh_lead_article(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))       
        return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead, 'max_call_count':0})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        return HttpResponse(e, status=500)
@login_required
def refresh_booking_row(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))       
        return render(request, 'campaign_leads/htmx/campaign_booking_row_htmx.html', {'lead':lead})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def add_manual_booking(request, **kwargs):
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
                
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()          
        lead = booking.lead
        company_pk = lead.campaign.site.company.pk   
        rendered_html = f"<span hx-swap-oob='delete' id='lead-{lead.pk}'></span> <span hx-swap-oob='outerHTML:.booking-lead-{lead.pk}'><span hx-get='/campaign-leads/refresh-booking-row/{lead.pk}/' hx-swap='innerHTML' hx-target='#row_{lead.pk}' hx-indicator='#top-htmx-indicator' hx-trigger='load'></span></span>"
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
    except Exception as e:
        logger.debug("add_manual_booking Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_archived(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead_pk = request.POST.get('lead_pk') or kwargs.get('lead_pk')
            lead = Campaignlead.objects.get(pk=lead_pk)
            if lead.archived:
                lead.archived = False
                lead.sold = False
            else:
                lead.archived = True
                lead.sold = False
            lead.save()
            lead.trigger_refresh_websocket(refresh_position=False)
            return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
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
        logger.debug("mark_archived Error "+str(e))
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
        logger.debug("mark_archived Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_sold(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
            if lead.sold:
                lead.archived = False
                lead.sold = False
                lead.marked_sold = None
                lead.sold_by = None
            else:
                lead.archived = False
                lead.sold = True
                lead.marked_sold = datetime.now()
                lead.sold_by = request.user
            lead.save()
            return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
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
#         logger.debug("mark_archived Error "+str(e))
# #         return HttpResponse(e, status=500)
# @login_required
# def template_editor(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             template = WhatsappTemplate.objects.get(pk=request.GET.get('template_pk'))
#             return render(request, "campaign_leads/htmx/template_editor.html", {'template':template}) 
#     except Exception as e:
#         logger.debug("mark_archived Error "+str(e))
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
#         logger.debug("mark_archived Error "+str(e))
#         return HttpResponse(e, status=500)

        