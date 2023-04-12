from datetime import datetime
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render

from campaign_leads.models import Campaignlead
from core.models import Site, WhatsappNumber, Contact, AttachedError, SiteContact
from core.user_permission_functions import get_allowed_site_chats_for_user, get_user_allowed_to_use_site_messaging
from core.views import get_site_pks_from_request_and_return_sites
from whatsapp.models import WhatsAppMessage, WhatsappMessageImage
from django.contrib.auth.decorators import login_required
from core.templatetags.core_tags import seconds_until_hours_passed
from django.utils.decorators import method_decorator
from core.core_decorators import check_core_profile_requirements_fulfilled
import logging
from django.conf import settings
logger = logging.getLogger(__name__)

@login_required
def message_list(request, **kwargs):
    context = {}
    whatsappnumber = None
    customer_number = request.GET.get('customer_number') 
    site = Site.objects.filter(pk=request.GET.get('site_pk')).exclude(active=False).first()
    context['chat_site'] = [site]    
    whatsappnumber_pk = request.GET.get('whatsappnumber_pk')
    if whatsappnumber_pk:
        whatsappnumber = WhatsappNumber.objects.get(pk=whatsappnumber_pk, whatsapp_business_account__active=True)
    elif customer_number and site:
        context['customer_numbers'] = [customer_number]    
        latest_message = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber__whatsapp_business_account__site=site).order_by('datetime').last()
        if latest_message:
            whatsappnumber = latest_message.whatsappnumber
    if whatsappnumber:
        context['whatsappnumber'] = whatsappnumber
        context['messages'] = whatsappnumber.get_latest_messages(query={"hide_auto":True})
    # if get_user_allowed_to_use_site_messaging(request.user, site):
    return render(request, "messaging/messaging_list.html", context)

@login_required
def message_window(request, **kwargs):
    whatsappnumber = WhatsappNumber.objects.get(pk=kwargs.get('whatsappnumber_pk'), whatsapp_business_account__active=True)
    all_messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), whatsappnumber=whatsappnumber).order_by('-datetime')
    # messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), whatsappnumber=whatsappnumber).order_by('-datetime')[:20:-1]
    context = {}
    context["messages"] = all_messages[:10:-1]
    last_customer_message = all_messages.filter(inbound=True).first()
    if last_customer_message:
        seconds_until_send_disabled = seconds_until_hours_passed(last_customer_message.datetime, 24)
            
        if seconds_until_send_disabled:
            if seconds_until_send_disabled > 3:
                context["seconds_until_send_disabled"] = seconds_until_send_disabled
    if settings.DEBUG:
        if not kwargs.get('refresh') == 'refresh':
            context["seconds_until_send_disabled"] = 5
        else:
            try:
                del context["seconds_until_send_disabled"]
            except:
                pass
    # temp = SiteContact.objects.filter(site=whatsappnumber.site, contact__customer_number=kwargs.get('customer_number'))
    contact, created = Contact.objects.get_or_create(company=request.user.profile.company, customer_number=kwargs.get('customer_number'))
    context["site_contact"], created = SiteContact.objects.get_or_create(site=whatsappnumber.site, contact=contact)
    if get_user_allowed_to_use_site_messaging(request.user, whatsappnumber.site):
        lead = Campaignlead.objects.filter(contact__customer_number=kwargs.get('customer_number')).last()
        context["lead"] = lead
        context["customer_number"] = kwargs.get('customer_number')
        context['whatsappnumber'] = whatsappnumber
        return render(request, "messaging/message_window_htmx.html", context)
    return HttpResponse( status=500)

@login_required
def get_messaging_list_row(request, **kwargs):
    try:
    #     request.GET._mutable = True
        site = request.user.profile.active_sites_allowed.get(pk=request.GET.get('site_pk'))
        message = WhatsAppMessage.objects.filter(site=site, customer_number=request.GET.get('whatsapp_number')).last()
        return render(request, "messaging/htmx/message_list_row.html", {'site':site, 'message':message})   
    except Exception as e:
        logger.debug("get_messaging_list_row Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e

@login_required
def send_first_template_whatsapp_lead_article_htmx(request, **kwargs):
    # try:
    send_first_template_whatsapp(request, kwargs)
    return HttpResponse('', status=200)
    # except Exception as e:
    #     logger.debug("send_first_template_whatsapp_htmx Error "+str(e))
    #     #return HttpResponse(e, status=500)

@login_required
def send_first_template_whatsapp_booking_row_htmx(request, **kwargs):
    try:
        return render(request, "campaign_leads/bookings_overview/booking_row_htmx.html", send_first_template_whatsapp(request, kwargs))
    except Exception as e:
        logger.debug("send_first_template_whatsapp_htmx Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e

@login_required
def send_first_template_whatsapp(request, kwargs):
    lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))
    if not lead.message_set.all():
        if not lead.campaign.whatsapp_business_account:
            AttachedError.objects.get_or_create(
                    type = '1230',
                    attached_field = "campaign_lead",
                    campaign_lead = lead,
                )
        elif not lead.campaign.whatsapp_business_account.whatsappnumber:
            AttachedError.objects.get_or_create(
                    type = '1230',
                    attached_field = "campaign_lead",
                    campaign_lead = lead,
                )
        else:
            AttachedError.objects.filter(
                    type = '1230', 
                    attached_field = "campaign_lead",
                    campaign_lead = lead,
                    archived = False,
                ).update(archived = True) 
            lead.send_template_whatsapp_message(whatsappnumber=lead.campaign.whatsapp_business_account.whatsappnumber, send_order=0)
    messages = WhatsAppMessage.objects.filter(customer_number=kwargs.get('customer_number'), whatsappnumber__number=kwargs.get('messaging_phone_number')).order_by('-datetime')
    context = {}
    context["messages"] = messages
    context["lead"] = lead
    context["customer_number"] = lead.contact.customer_number
    context["site_pk"] = lead.campaign.site
    context['max_call_count'] = request.POST.get('max_call_count')
    lead.trigger_refresh_websocket(refresh_position=False)
    return context
@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        context['sites'] = get_site_pks_from_request_and_return_sites(request)


        whatsapp_message_image_pk = request.GET.get('whatsapp_message_image_pk')
        if whatsapp_message_image_pk:
            context['whatsapp_message_image'] = WhatsappMessageImage.objects.get(pk=whatsapp_message_image_pk)

        lead_pk = request.GET.get('lead_pk')
        if lead_pk:
            lead = Campaignlead.objects.get(pk=lead_pk)
            context['lead'] = lead
            # if request.GET.get('template_name', None) == "message_window_modal":
                # whatsappnumber = lead.campaign.site.default_number
                # customer_number = lead.contact.customer_number
                # context['customer_number'] = customer_number
                # context['whatsappnumber'] = whatsappnumber
                # context['messages'] = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber=whatsappnumber).order_by('datetime')
                # context['messages'] = WhatsAppMessage.objects.filter(customer_number=customer_number, whatsappnumber=whatsappnumber).order_by('-datetime')[:20:-1]
        
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            # context['site_list'] = get_available_sites_for_user(request.user)
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
                
            return render(request, f"messaging/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@login_required
def update_message_counts(request, **kwargs):
    return render(request, "messaging/htmx/update_message_counts.html", {})

@login_required
def get_message_list_body(request, **kwargs):
    try:
        context = {}
        whatsappnumber = WhatsappNumber.objects.get(pk=request.GET.get('whatsappnumber_pk'), whatsapp_business_account__active=True) 
        context['whatsappnumber'] = whatsappnumber
        context['messages'] = whatsappnumber.get_latest_messages(query={"search_string":request.GET.get('search_string'), "received":request.GET.get('received'), "hide_auto":request.GET.get('hide_auto', 'off') == 'on'})
        return render(request, "messaging/htmx/message_list_body.html", context)   
    except Exception as e:
        logger.debug("get_more_messages Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e

@login_required
def get_more_message_list_rows(request, **kwargs):
    try:
        context = {}
        whatsappnumber = WhatsappNumber.objects.get(pk=request.GET.get('whatsappnumber_pk'), whatsapp_business_account__active=True)
        earliest_datetime_timestamp = request.GET.get('earliest_datetime_timestamp')        
        context['whatsappnumber'] = whatsappnumber
        context['messages'] = whatsappnumber.get_latest_messages(after_datetime_timestamp=earliest_datetime_timestamp,query={"search_string":request.GET.get('search_string'), "received":request.GET.get('received'), "hide_auto":request.GET.get('hide_auto', 'off') == 'on'})
        return render(request, "messaging/htmx/message_list_rows.html", context)   
    except Exception as e:
        logger.debug("get_more_messages Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e

@login_required
def get_more_message_chat_rows(request):
    try:
        context = {}
        whatsappnumber = WhatsappNumber.objects.get(pk=request.GET.get('whatsappnumber_pk'), whatsapp_business_account__active=True)
        earliest_datetime_timestamp = request.GET.get('earliest_datetime_timestamp')        
        context['whatsappnumber'] = whatsappnumber
        messages = WhatsAppMessage.objects.filter(customer_number=request.GET.get('customer_number'), whatsappnumber=whatsappnumber).order_by('-datetime')
        after_datetime = datetime.fromtimestamp(int(float(earliest_datetime_timestamp)))
        messages = messages.filter(datetime__lt=after_datetime)
        context['messages'] = messages[:10:-1]
        return render(request, "messaging/message_window_message_rows.html", context)   
    except Exception as e:
        logger.debug("get_more_messages Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e
@login_required
def mark_read(request):
    try:
        WhatsAppMessage.objects.filter(pk=request.POST.get('message_pk')).update(read=True)
        return HttpResponse("", status=200) 
    except Exception as e:
        logger.debug("mark_read Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e
        

# @login_required
# def clear_chat_from_session(request):
#     try:
#         request.session['open_chat_conversation_customer_number'] = request.session.get('open_chat_conversation_customer_number', []).remove(request.POST.get('customer_number'))
#     except Exception as e:
#         print("clear_chat_from_session error", str(e))
#     return HttpResponse( "text", 200)
    



@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class MessagingView(TemplateView):
    template_name='messaging/messaging.html'
    def get(self, request, *args, **kwargs):        
        if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'messaging/messaging_htmx.html'
        return super(MessagingView, self).get(request, args, kwargs)
    