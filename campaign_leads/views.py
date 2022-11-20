from datetime import datetime
import logging
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from calendly.api import Calendly
from campaign_leads.models import Call, Campaign, Campaignlead
from active_campaign.api import ActiveCampaignApi
from active_campaign.models import ActiveCampaign
from core.core_decorators import campaign_leads_enabled_required
from core.models import Profile, Site, WhatsappBusinessAccount
from core.user_permission_functions import get_available_sites_for_user, get_user_allowed_to_add_call
from core.views import get_site_pk_from_request
from django.db.models import Q, Count
from django.db.models import OuterRef, Subquery, Count
from django.db.models import F
from whatsapp.api import Whatsapp
from whatsapp.models import WhatsappTemplate
from django.template import loader
logger = logging.getLogger(__name__)
from core.templatetags.core_tags import hex_to_rgb_tuple

def get_campaign_qs(request):
    first_model_query = (Campaignlead.objects
        .filter(campaign=OuterRef('pk'), complete=False)
        .values('campaign')
        .annotate(cnt=Count('pk'))
        .values('cnt')
    )    
    campaign_qs = Campaign.objects.annotate(
        first_model_count=Subquery(first_model_query)
    )
    site_pk = get_site_pk_from_request(request)
    if site_pk and not site_pk == 'all':
        campaign_qs = campaign_qs.filter(site__pk=site_pk)
    return campaign_qs.order_by('first_model_count')

@method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CampaignleadsOverviewView(TemplateView):
    template_name='campaign_leads/campaign_leads_overview.html'
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:        
            logger.error(f"get_campaigns {str(e)}")
            return HttpResponse("Couldn't complete Campaign Leads Overview request", status=500)

    def get_context_data(self, **kwargs):    
        context = super(CampaignleadsOverviewView, self).get_context_data(**kwargs)  
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/htmx/campaign_leads_overview_htmx.html'   
        context.update(get_leads_board_context(self.request))
            
        # whatsapp = Whatsapp()
        return context
        
def get_leads_board_context(request):
    request.GET._mutable = True 
    context = {}   
    context['campaigns'] = get_campaign_qs(request)
    leads = Campaignlead.objects.filter(complete=False, campaign__site__in=request.user.profile.sites_allowed.all()).exclude(booking__archived=False)
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        try:
            leads = leads.filter(campaign=Campaign.objects.get(pk=campaign_pk))
            request.GET['campaign_pk'] = campaign_pk
            context['campaign'] = Campaign.objects.get(pk=campaign_pk)
            request.GET['site_pk'] = context['campaign'].site.pk
        except:
            pass
    site_pk = get_site_pk_from_request(request)
    if site_pk and not site_pk == 'all':
        try:
            leads = leads.filter(campaign__site__pk=site_pk)
            request.GET['site_pk'] = site_pk    
            context['site'] = Site.objects.get(pk=site_pk)
        except:
            pass
    leads = leads.annotate(calls=Count('call')).order_by('-last_dragged')
    
    context['querysets'] = [
        ('Fresh', leads.filter(calls=0), 0)
    ]
    index = 0
    # if leads.filter(calls__gt=index):
    while leads.filter(calls__gt=index) or index < 21:
        index = index + 1
        context['querysets'].append(
            (f"Call {index}", leads.filter(calls=index), index)
        )
    context['querysets'].append(
        (f"Call {index+1}", leads.none(), index+1)
    )
    # else:
    #     context['querysets'].append(
    #         (f"Call 1", leads.none(), 1)
    #     )
    context['max_call_count'] = index
    context['company'] = request.user.profile.company
    return context

def refresh_leads_board(request):
    return render(request, 'campaign_leads/htmx/leads_board.html', get_leads_board_context(request))
@method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CampaignBookingsOverviewView(TemplateView):
    template_name='campaign_leads/campaign_bookings_overview.html'
    def get_context_data(self, **kwargs):
        context = super(CampaignBookingsOverviewView, self).get_context_data(**kwargs)    
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/htmx/campaign_bookings_overview_htmx.html'   
            context['campaigns'] = get_campaign_qs(self.request)
        context.update(get_booking_table_context(self.request))
        return context
def get_booking_table_context(request):
    request.GET._mutable = True     
    context = {}
    leads = Campaignlead.objects.all()
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        leads = leads.filter(campaign=Campaign.objects.get(pk=campaign_pk))
        request.GET['campaign_pk'] = campaign_pk
    site_pk = get_site_pk_from_request(request)
    if site_pk and not site_pk == 'all':
        leads = leads.filter(campaign__site__pk=site_pk)
        request.GET['site_pk'] = site_pk 
        context['site'] = Site.objects.get(pk=site_pk)            
    context['complete_count'] = leads.filter(complete=True).count()
    complete_filter = (request.GET.get('complete', '').lower() =='true')
    if not complete_filter:
        leads = leads.exclude(booking__created=None)
    leads = leads.filter(complete=complete_filter)   
    context['complete'] = complete_filter
    context['booking_needed_count'] = leads.filter(booking=None).count()
    context['leads'] = leads
    context['company'] = request.user.profile.company
    return context
def refresh_booking_table_htmx(request):
    return render(request, 'campaign_leads/htmx/campaign_bookings_table.html', get_booking_table_context(request))
@method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CampaignConfigurationView(TemplateView):
    template_name='campaign_leads/campaign_configuration.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True
        context = super(CampaignConfigurationView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/campaign_configuration_htmx.html'  
        company = self.request.user.profile.company
        for campaign_dict in ActiveCampaignApi(company.active_campaign_api_key, company.active_campaign_url).get_lists(company.active_campaign_url).get('lists',[]):
            campaign, created = ActiveCampaign.objects.get_or_create(
                active_campaign_id = campaign_dict.pop('id'),
                name = campaign_dict.pop('name'),
                company = company,
            )
            campaign.json_data = campaign_dict
            campaign.save()
        if company:
            campaigns = company.get_and_generate_campaign_objects()

        site_pk = get_site_pk_from_request(self.request)
        if site_pk and not site_pk == 'all':
            try:
                campaigns = campaigns.filter(site__pk=site_pk)
                self.request.GET['site_pk'] = site_pk    
                context['site'] = Site.objects.get(pk=site_pk)
            except Exception as e:
                pass

        context['campaigns'] = campaigns
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        return context

        
@login_required
def get_campaigns(request, **kwargs):
    # try:
    if request.user.profile.company:
        request.user.profile.company.get_and_generate_campaign_objects()
    return render(request, f"campaign_leads/htmx/campaign_select.html", 
    {'campaigns':get_campaign_qs(request)})
    # except Exception as e:        
    #     logger.error(f"get_campaigns {str(e)}")
    #     return HttpResponse("Couldn't get Campaigns", status=500)

@login_required
def new_call(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            log_datetime = datetime.now()
            call_count = int(kwargs.get('call_count'))
            lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
            if get_user_allowed_to_add_call(request.user, lead):
                if lead.calls < call_count:
                    while lead.calls < call_count:
                        call = Call.objects.create(
                            datetime=log_datetime,
                            lead = lead,                        
                            user=request.user
                        )
                        lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
                elif lead.calls > call_count:
                    while lead.calls > call_count:
                        Call.objects.filter(
                            lead = lead,
                        ).order_by('-datetime').first().delete()
                        lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
                lead.last_dragged = datetime.now()
                lead.save()

                
                lead.trigger_refresh_websocket(refresh_position=True)
                
                return HttpResponse("", status=200)
            return HttpResponse("", status=500)
            # return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead,'max_call_count':kwargs.get('max_call_count', 1), 'call_count':call_count})
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        return HttpResponse(e, status=500)



@login_required
def campaign_assign_auto_send_template_htmx(request):
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'))
    first_template_pk = request.POST.get('first_template_pk')
    second_template_pk = request.POST.get('second_template_pk')
    third_template_pk = request.POST.get('third_template_pk')
    if not first_template_pk == None:
        campaign.first_send_template = WhatsappTemplate.objects.filter(pk=(first_template_pk or 0)).first()
    if not second_template_pk == None:
        campaign.second_send_template = WhatsappTemplate.objects.filter(pk=(second_template_pk or 0)).first()
    if not third_template_pk == None:
        campaign.third_send_template = WhatsappTemplate.objects.filter(pk=(third_template_pk or 0)).first()
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign})

@login_required
def campaign_assign_whatsapp_business_account_htmx(request):
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'))
    whatsapp_business_account_pk = request.POST.get('whatsapp_business_account_pk') or 0
    
    campaign.whatsapp_business_account = WhatsappBusinessAccount.objects.filter(pk=whatsapp_business_account_pk).first()
    campaign.first_send_template = None
    campaign.second_send_template = None
    campaign.third_send_template = None
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign})

@login_required
def campaign_assign_color_htmx(request):
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'))
    campaign.color = hex_to_rgb_tuple(request.POST.get('color', "60F83D"))
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign})
    

@login_required
def campaign_assign_product_cost_htmx(request):
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'))
    product_cost = request.POST.get('product_cost')
    if product_cost:
        campaign.product_cost = product_cost
        campaign.save()
    return render(request, 'campaign_leads/campaign_configuration_row.html', {'campaign':campaign,})
                                                                            # 'site_list': get_available_sites_for_user(request.user)})

@login_required
def toggle_claim_lead(request, **kwargs):
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'))
        if get_user_allowed_to_add_call(request.user, lead):
            if lead.assigned_user == request.user:
                lead.assigned_user = None
            else:
                lead.assigned_user = request.user
            lead.save()
            lead.trigger_refresh_websocket()
        
            return HttpResponse("", status=200)
            # return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead, 'max_call_count':0})
        return HttpResponse("", status=500)
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        return HttpResponse(e, status=500)