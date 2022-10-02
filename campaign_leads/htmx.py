from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required

from campaign_leads.models import Campaignlead, Booking, Communication, Note, WhatsappTemplate, communication_choices_dict
from campaign_leads.views import CampaignBookingsOverviewView
from active_campaign.models import ActiveCampaignList
from core.models import Site
from core.views import get_site_pk_from_request
from django.db.models import Q, Count

logger = logging.getLogger(__name__)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
        if request.user.is_staff:
            template_name = request.GET.get('template_name', '')
            context = {'site_list':Site.objects.all()}
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
            
            # if template_name == 'switch_user':
            #     context['users'] = User.objects.filter(is_staff=True).order_by('first_name')
            if template_name == 'log_communication':
                context['communication_type'] = kwargs.get('param2')
                context['communication_type_display'] = communication_choices_dict[kwargs.get('param2')]
                
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def create_campaign_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        first_name = request.POST.get('first_name')
        # last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        country_code = request.POST.get('countryCode')
        site = Site.objects.get(pk=request.POST.get('site_pk'))
        manually_created_list = ActiveCampaignList.objects.get(site=site, manual=True)
        lead = Campaignlead.objects.create(
            first_name=first_name,
            # last_name=last_name,
            whatsapp_number=f"whatsapp:+{country_code}{phone}",
            # country_code=country_code,
            active_campaign_list=manually_created_list
        )
        return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead,'max_call_count':1,'call_count':0})
    except Exception as e:
        logger.debug("create_campaign_lead Error "+str(e))
        return HttpResponse(e, status=500)
@login_required
def get_leads_column_meta_data(request, **kwargs):
    logger.debug(str(request.user))
    try:
        leads = Campaignlead.objects.filter(complete=False, booking=None)
        active_campaign_list_pk = request.GET.get('active_campaign_list_pk', None)
        if active_campaign_list_pk:
            leads = leads.filter(active_campaign_list=ActiveCampaignList.objects.get(pk=active_campaign_list_pk))
            # request.GET['active_campaign_list_pk'] = active_campaign_list_pk
        site_pk = get_site_pk_from_request(request)
        if site_pk and not site_pk == 'all':
            leads = leads.filter(active_campaign_list__site__pk=site_pk)
            # request.GET['site_pk'] = site_pk 
            
        leads = leads.annotate(calls=Count('communication', filter=Q(communication__type='a')))
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
def log_communication(request, **kwargs):
    logger.debug(str(request.user))
    try:        
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
        date_occurred = request.POST.get('date_occurred')
        time_occurred = request.POST.get('time_occurred')
        communication_type = request.POST.get('communication_type')
        if communication_type == 'a':
            successful = (request.POST.get('customer_answered', 'off') == 'on')
        else:
            successful = None
        log_datetime = datetime.strptime(f"{date_occurred} {time_occurred}", '%Y-%m-%d %H:%M')
        communication = Communication.objects.create(
            datetime=log_datetime,
            lead = lead,
            type = communication_type,
            successful = successful,
            staff_user=request.user
        )

        note = request.POST.get('note','')
        if note:
            Note.objects.create(
                communication=communication,
                lead=lead,
                text=note,
                staff_user=request.user,
                datetime=log_datetime
                )
                
        context = {
            'lead': lead,
        }
        
        return render(request, "campaign_leads/htmx/campaign_booking_row.html", context)   
    except Exception as e:
        logger.debug("log_communication Error "+str(e))
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
            staff_user=request.user
        )

        note = request.POST.get('note','')
        if note:
            Note.objects.create(
                booking=booking,
                lead=lead,
                text=note,
                staff_user=request.user,
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
        if request.user.is_staff:
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
        if request.user.is_staff:
            max_call_count = int(request.GET.get('max_call_count', 1))+2
            querysets = [
                (f"Call {max_call_count}", Campaignlead.objects.none(), max_call_count)
            ]
            return render(request, 'campaign_leads/htmx/lead_columns.html', {'querysets':querysets, 'max_call_count':max_call_count-1})
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def new_call(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            log_datetime = datetime.now()
            call_count = int(kwargs.get('call_count'))
            lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('communication', filter=Q(communication__type='a'))).first()
            if lead.calls < call_count:
                while lead.calls < call_count:
                    communication = Communication.objects.create(
                        datetime=log_datetime,
                        lead = lead,
                        type = 'a',
                        successful = False,
                        staff_user=request.user
                    )
                    lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('communication', filter=Q(communication__type='a'))).first()
            elif lead.calls > call_count:
                while lead.calls > call_count:
                    Communication.objects.filter(
                        lead = lead,
                        type = 'a'
                    ).order_by('-datetime').first().delete()
                    lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('communication', filter=Q(communication__type='a'))).first()
           
            lead.save()

            return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead,'max_call_count':kwargs.get('max_call_count', 1), 'call_count':call_count})
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        return HttpResponse(e, status=500)



@login_required
def delete_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
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
        if request.user.is_staff:
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
        if request.user.is_staff:
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
#         if request.user.is_staff:
#             lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
#             lead.send_whatsapp_message('testing api', request.user)
#             return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
#     except Exception as e:
#         logger.debug("mark_done Error "+str(e))
#         return HttpResponse(e, status=500)
@login_required
def template_editor(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            template = WhatsappTemplate.objects.get(pk=request.GET.get('template_pk'))
            return render(request, "campaign_leads/htmx/template_editor.html", {'template':template}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def template_save(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
            template.text = request.POST.get('template_text')
            template.save()
            return render(request, "campaign_leads/htmx/template_editor.html", {'template':template}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

        