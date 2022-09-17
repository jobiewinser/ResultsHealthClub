from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required

from academy_leads.models import AcademyLead, Booking, Communication, Note, WhatsappTemplate, communication_choices_dict
from active_campaign.models import ActiveCampaignList
from core.models import Site
logger = logging.getLogger(__name__)

@login_required
def get_modal_content(request, **kwargs):
    try:
        if request.user.is_staff:
            template_name = request.GET.get('template_name', '')
            context = {'site_list':Site.objects.all()}
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = AcademyLead.objects.get(pk=param1)
            
            if template_name == 'switch_user':
                # context['staff_users'] = User.objects.filter(is_staff=True, is_superuser=False).order_by('first_name')
                context['staff_users'] = User.objects.filter(is_staff=True).order_by('first_name')
            if template_name == 'log_communication':
                context['communication_type'] = kwargs.get('param2')
                context['communication_type_display'] = communication_choices_dict[kwargs.get('param2')]
                
            return render(request, f"academy_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def create_academy_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        first_name = request.POST.get('first_name')
        # last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        country_code = request.POST.get('countryCode')
        AcademyLead.objects.create(
            first_name=first_name,
            # last_name=last_name,
            phone=phone,
            country_code=country_code,
            active_campaign_list=ActiveCampaignList.objects.get_or_create(name='Manually Created')[0]
        )
        context = {
            'site_choices': Site.objects.all(),
            'leads': AcademyLead.objects.filter(complete=False),
        }
        
        return render(request, "academy_leads/htmx/academy_leads_table_htmx.html", context)   
    except Exception as e:
        logger.debug("create_academy_lead Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def log_communication(request, **kwargs):
    logger.debug(str(request.user))
    try:        
        lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
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
        
        return render(request, "academy_leads/htmx/academy_lead_row.html", context)   
    except Exception as e:
        logger.debug("create_academy_lead Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def add_booking(request, **kwargs):
    logger.debug(str(request.user))
    try:        
        lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
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
        
        return render(request, "academy_leads/htmx/academy_lead_row.html", context)   
    except Exception as e:
        logger.debug("create_academy_lead Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_done(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
            lead.complete = not lead.complete
            lead.save()

            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def mark_arrived(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
            lead.arrived = not lead.arrived
            lead.save()
            return render(request, "academy_leads/htmx/academy_lead_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def mark_sold(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
            lead.sold = not lead.sold
            lead.save()
            return render(request, "academy_leads/htmx/academy_lead_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)
        
# @login_required
# def test_whatsapp_message(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_staff:
#             lead = AcademyLead.objects.get(pk=request.POST.get('lead_pk'))
#             lead.send_whatsapp_message('testing api', request.user)
#             return render(request, "academy_leads/htmx/academy_lead_row.html", {'lead':lead}) 
#     except Exception as e:
#         logger.debug("mark_done Error "+str(e))
#         return HttpResponse(e, status=500)
@login_required
def template_editor(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            template = WhatsappTemplate.objects.get(pk=request.GET.get('template_pk'))
            return render(request, "academy_leads/htmx/template_editor.html", {'template':template}) 
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
            return render(request, "academy_leads/htmx/template_editor.html", {'template':template}) 
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

        