#0.9 safe
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth.decorators import login_required
from campaign_leads.models import Campaign, Campaignlead, Booking, Note, ManualCampaign, CampaignCategory, Sale
from active_campaign.models import ActiveCampaign
from core.models import Site, WhatsappNumber,Subscription
from core.views import get_site_pks_from_request_and_return_sites
from django.db.models import Count
from asgiref.sync import async_to_sync
from campaign_leads.views import get_campaign_qs
from whatsapp.models import WhatsappTemplate
from django.conf import settings
logger = logging.getLogger(__name__) 
from active_campaign.api import ActiveCampaignApi
@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        if request.user.is_authenticated:
            context = {}
            template_name = request.GET.get('template_name', '')
            site_pk = request.GET.get('site_pk', None)
            # context['site_list'] = get_available_sites_for_user(request.user)
            param1 = kwargs.get('param1', '')
            if param1:
                context['lead'] = Campaignlead.objects.get(pk=param1)
                
            context['sites'] = get_site_pks_from_request_and_return_sites(request)
            whatsapp_template_pk = request.GET.get('whatsapp_template_pk')
            if whatsapp_template_pk:
                context['template'] = WhatsappTemplate.objects.get(pk=whatsapp_template_pk)

            campaign_pk = request.GET.get('campaign_pk')
            if campaign_pk:
                context['campaign'] = Campaign.objects.get(pk=campaign_pk)

            whatsappnumber_pk = request.GET.get('whatsappnumber_pk')
            if whatsappnumber_pk:
                context['whatsappnumber'] = WhatsappNumber.objects.get(pk=whatsappnumber_pk)

            lead_pk = request.GET.get('lead_pk')
            if template_name == 'edit_lead':
                if lead_pk:
                    context['lead'] = Campaignlead.objects.get(pk=lead_pk)
                    context['site'] = context['lead'].campaign.site
                if not ManualCampaign.objects.filter(site__in=context['sites']).exists():
                    for site in request.user.profile.company.active_sites:
                        ManualCampaign.objects.get_or_create(site=site, name = "Manually Created")
                context['campaigns'] = get_campaign_qs(request)         
            elif template_name == 'mark_sold':
                lead = Campaignlead.objects.get(pk=lead_pk)
                context['lead'] = lead
                # context['users'] = User.objects.filter(profile__sites_allowed=lead.campaign.site)
            # elif template_name == 'import_active_campaign_leads':
                
            elif template_name in ['switch_subscription','choose_attached_profiles']:
                context["site"] = Site.objects.get(pk=site_pk)
                context['switch_subscription'] = Subscription.objects.filter(numerical=request.GET.get('switch_subscription')).exclude(active=False).first()
            elif template_name in ['change_default_payment_method', 'renew_stripe_subscription']:
                context["site"] = Site.objects.get(pk=site_pk)
                context[template_name] = True
                context["invoice_id"] = request.GET.get('invoice_id')
                
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e
        



@login_required
def add_campaign_category(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    # logger.debug(str(request.user))
    # try:        
    name = request.POST.get('category_name')
    if not name:
        return HttpResponse("Please enter a name", status=500)
    campaign_pk = request.POST.get('campaign_pk')
    site_pk = request.POST.get('site_pk')
    if campaign_pk:
        campaign = request.user.profile.campaigns_allowed.get(pk=campaign_pk)
        campaign_category, created = CampaignCategory.objects.get_or_create(site=campaign.site, name=name)
        campaign.campaign_category = campaign_category
        campaign.save()
    else:
        site = Site.objects.get(pk=site_pk)
        campaign_category, created = CampaignCategory.objects.get_or_create(site=site, name=name)
    return HttpResponse( status=200)
    # except Exception as e:
    #     # messages.add_message(request, messages.ERROR, f'Error with creating a campaign lead')
    #     logger.debug("create_campaign_lead Error "+str(e))
    #     # raise Exception
    #     return HttpResponse("Error with creating a campaign lead", status=500)

@login_required
def edit_lead(request, **kwargs):
    if settings.DEMO and not request.user.is_superuser:
        return HttpResponse(status=500)
    # logger.debug(str(request.user))
    # try:        
    campaign_pk = request.POST.get('campaign_pk')
    if not campaign_pk:
        return HttpResponse("Please choose a campaign", status=500)
    campaign = request.user.profile.campaigns_allowed.get(pk=campaign_pk)    
    
    first_name = request.POST.get('first_name')
    if not first_name:
        return HttpResponse("Please provide a first name", status=500)

    last_name = request.POST.get('last_name')

    email = request.POST.get('email')[:50]
    
    phone = request.POST.get('phone')
    if not phone:
        return HttpResponse("Please provide a valid Phone Number", status=500)
    
    country_code = request.POST.get('country_code', "")
    
    disabled_automated_messaging = request.POST.get('enable_automated_messaging', 'on') == 'off'
    product_cost = request.POST.get('product_cost', 0)
    
    lead_pk = request.POST.get('lead_pk')
    if lead_pk:
        lead = Campaignlead.objects.get(pk=lead_pk)
        if not lead.campaign in request.user.profile.campaigns_allowed:
            return HttpResponse("You are not permissted to use this campaign", status=403)
            
        refresh_position = False
    else:
        lead = Campaignlead()
        refresh_position = True
    lead.campaign = campaign
    lead.first_name = first_name
    lead.last_name = last_name
    lead.email = email
    lead.whatsapp_number = f"{country_code}{phone}"
    if product_cost:
        lead.product_cost = product_cost
    lead.disabled_automated_messaging = disabled_automated_messaging
    
    lead.save()
    lead.trigger_refresh_websocket(refresh_position=refresh_position)
    return HttpResponse(str(lead.pk), status=200)
    # except Exception as e:
    #     # messages.add_message(request, messages.ERROR, f'Error with creating a campaign lead')
    #     logger.debug("create_campaign_lead Error "+str(e))
    #     # raise Exception
    #     return HttpResponse("Error with creating a campaign lead", status=500)
# @login_required
# def get_leads_column_meta_data(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         leads = Campaignlead.objects.filter(campaign__site__in=request.user.profile.active_sites_allowed)
#         campaign_pk = request.GET.get('campaign_pk', None)
#             # request.GET['campaign_pk'] = campaign_pk
#         sites = get_site_pks_from_request_and_return_sites(request).filter(archived=False, booking=None)
#         if request.GET['site_pks']:
#             leads = leads.filter(campaign__site__pk__in=request.GET['site_pks'])
            
#         if campaign_pk:
#             leads = leads.filter(campaign=request.user.profile.campaigns_allowed.get(pk=campaign_pk))
#         leads = leads.annotate(calls=Count('call'))
#         querysets = [
#             ('Fresh', leads.filter(calls=0), 0)
#         ]
#         index = 0
#         # if leads.filter(calls__gt=index):
#         while leads.filter(calls__gt=index) or index < 21:
#             index = index + 1
#             querysets.append(
#                 (f"Call {index}", leads.filter(calls=index), index)
#             )
#         # else:
#         #     querysets.append(
#         #         (f"Call 1", leads.none(), 1)
#         #     )
#         return render(request, 'campaign_leads/htmx/column_metadata_htmx.html', {'querysets':querysets})
#     except Exception as e:
#         logger.debug("get_leads_column_meta_data Error "+str(e))
#         #return HttpResponse(e, status=500)
#         raise e
@login_required
def refresh_lead_article(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)       
        return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead, 'max_call_count':0})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e
@login_required
def refresh_booking_row(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)       
        return render(request, 'campaign_leads/htmx/campaign_booking_row_htmx.html', {'lead':lead})
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@login_required
def add_manual_booking(request, **kwargs):
    logger.debug(str(request.user))
    try:        
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        # if (request.POST.get('booking_type', 'off') == 'on'):
        #     booking_type = 'a'
        # else:
        #     booking_type = 'b'
        try:
            booking_datetime = datetime.strptime(f"{booking_date} {booking_time}", '%Y-%m-%d %H:%M')
        except:
            return HttpResponse("Please enter a valid date and time", status=500)
        booking = Booking.objects.create(
            datetime = booking_datetime,
            lead = lead,
            # type = booking_type,
            user=request.user
        )

        note = request.POST.get('note','')
        if note:
            if settings.DEMO and not request.user.is_superuser:
                note = "Demo mode active, note text replaced!"
            Note.objects.create(
                booking=booking,
                lead=lead,
                text=note,
                user=request.user,
                datetime=datetime.now()
                )
                
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
        return HttpResponse( status=200)
    except Exception as e:
        logger.debug("add_manual_booking Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@login_required
def mark_archived(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead_pk = request.POST.get('lead_pk') or kwargs.get('lead_pk')
        lead = Campaignlead.objects.get(pk=lead_pk, campaign__site__in=request.user.profile.active_sites_allowed)
        if lead.active_sales_qs.exists():
            return HttpResponse("Cannot archive a lead with active sales", status=400)
            
        if lead.archived:
            lead.archived = False
            # lead.sold = False
        else:
            lead.archived = True
            # lead.sold = False
        lead.save()
        lead.trigger_refresh_websocket(refresh_position=False)
        return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


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
        #return HttpResponse(e, status=500)
        raise e


@login_required
def delete_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
        lead.delete()

        return HttpResponse( "text", 200)
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e

@login_required
def mark_arrived(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
        lead.arrived = not lead.arrived
        lead.save()
        return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


@login_required
def mark_sold(request, **kwargs):
    logger.debug(str(request.user))
    try:
        user_pk = request.POST.get('user_pk')
        lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
        active_sales = lead.active_sales_qs
        latest_active_sale = active_sales.last()
        active_sales.update(archived=True)
        if latest_active_sale and not user_pk:
            active_sales.update(archived=True)
        else:
            if user_pk:
                user = User.objects.get(pk=user_pk)
            else:
                user = request.user
            Sale.objects.create(
                user = user,
                datetime = datetime.now(),
                lead = lead,
            )
        lead.archived = False
        lead.save()
        return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


# @login_required
# def mark_sales_archived(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'))
#             active_sales = lead.active_sales_qs
#             active_sales.update(archived=True)
#             return render(request, "campaign_leads/htmx/campaign_booking_row.html", {'lead':lead}) 
#     except Exception as e:
#         logger.debug("mark_archived Error "+str(e))
#         #return HttpResponse(e, status=500)
#         raise e

@login_required
def create_lead_note(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            lead = Campaignlead.objects.get(pk=request.POST.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
            note = request.POST.get('note','')
            if note:
                if settings.DEMO and not request.user.is_superuser:
                    note = "Demo mode active, note text replaced!"
                Note.objects.create(                    
                    lead=lead,
                    text=note,
                    user=request.user,
                    datetime=datetime.now()
                    )
            lead.trigger_refresh_websocket(refresh_position=False)

            return HttpResponse(str(lead.pk), status=200)
    except Exception as e:
        logger.debug("mark_archived Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e
        
        
@login_required
def get_contacts_for_campaign(request, **kwargs):
    logger.debug(str(request.user))
    context = {}
    campaign = request.user.profile.active_campaigns_allowed.get(pk=request.GET.get('campaign_pk'))
    active_campaign_api = ActiveCampaignApi(request.user.profile.company.active_campaign_api_key, request.user.profile.company.active_campaign_url)
    contacts = active_campaign_api.list_contacts_by_campaign(campaign.active_campaign_id)
    contact_id_list = []
    for contact in contacts:
        contact_id_list.append(contact.get('id'))
    context['campaign_lead_ids'] = list(Campaignlead.objects.filter(active_campaign_contact_id__in=contact_id_list, campaign=campaign).exclude(archived=True).exclude(sale__archived=False).values_list('active_campaign_contact_id', flat=True))
    context['contacts'] = contacts
    return render(request, "campaign_leads/htmx/import_contact_div_contents.html", context)