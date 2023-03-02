from datetime import datetime
import logging
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from campaign_leads.models import Call, Campaignlead, CampaignTemplateLink, CampaignCategory, Campaign, ManualCampaign
from active_campaign.api import ActiveCampaignApi
from active_campaign.models import ActiveCampaign
from core.models import Profile, Site, WhatsappBusinessAccount
from core.user_permission_functions import get_user_allowed_to_add_call
from core.views import get_site_pks_from_request_and_return_sites, get_campaign_category_pks_from_request, get_single_site_pk_from_request_or_default_profile_site
from django.db.models import Q, Count
from django.db.models import OuterRef, Subquery, Count
from whatsapp.models import WhatsappTemplate
from core.core_decorators import check_core_profile_requirements_fulfilled
from core.user_permission_functions import get_profile_allowed_to_edit_other_profile
from core.core_decorators import *
from core.utils import get_object_or_403
logger = logging.getLogger(__name__)
def hex_to_rgb_tuple(hex):
    # this function takes a hex string and returns a string of rgb values
	hex = hex.replace('#','')
	return f"{int(hex[0:2], 16)},{int(hex[2:4], 16)},{int(hex[4:6], 16)}"

def rgb_to_hex_tuple(rgb_string):
    # this function takes a string of rgb values and returns a hex string
    try:
        r,g,b = rgb_string.split(',')
        r = ('{:X}').format(int(r)).zfill(2)
        g = ('{:X}').format(int(g)).zfill(2)
        b = ('{:X}').format(int(b)).zfill(2)
        return f"{r}{g}{b}"
    except Exception as e:
        return "FFFFFF"

#this doesn't needs a method decorator because it is not directly used by urls.py
def get_campaign_qs(request):
    # this function is used to get the campaigns for the campaign leads overview
    # it returns a queryset of campaigns that are filtered by the request
    first_model_query = (Campaignlead.objects
        .filter(campaign=OuterRef('pk'), archived=False)
        .values('campaign')
        .annotate(cnt=Count('pk'))
        .values('cnt')
    )    
    campaign_qs = Campaign.objects.annotate(
        first_model_count=Subquery(first_model_query)
    )
    sites = get_site_pks_from_request_and_return_sites(request)
    if sites:
        campaign_qs = campaign_qs.filter(site__in=sites)
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    if campaign_category_pks:
        campaign_qs = campaign_qs.filter(campaign_category__pk__in=campaign_category_pks)
    return campaign_qs.filter(site__company=request.user.profile.company, site__in=request.user.profile.active_sites_allowed).order_by('first_model_count')
#this doesn't needs a method decorator because it is not directly used by urls.py
def get_campaign_category_qs(request):
    sites = get_site_pks_from_request_and_return_sites(request)
    return CampaignCategory.objects.filter(site__in=sites)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class CampaignleadsOverviewView(TemplateView):
    # this class is used to render the campaign leads overview
    template_name='campaign_leads/leads_overview/campaign_leads_overview.html'
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:        
            logger.error(f"get_campaigns {str(e)}")
            if request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
                return HttpResponse("Couldn't access Campaign Leads Overview request", status=500)
            raise e

    def get_context_data(self, **kwargs):    
        context = super(CampaignleadsOverviewView, self).get_context_data(**kwargs)  
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/leads_overview/campaign_leads_overview_htmx.html'   
        context.update(get_leads_board_context(self.request))
        return context
#this doesn't needs a method decorator because it is not directly used by urls.py
def get_leads_board_context(request):
    # this function is used to get the context for the campaign leads overview and refresh_leads_board
    request.GET._mutable = True 
    context = {}   
    context['sites'] = get_site_pks_from_request_and_return_sites(request)
    campaigns = get_campaign_qs(request)
    leads = Campaignlead.objects.filter(archived=False, campaign__site__company=request.user.profile.company, campaign__site__in=request.user.profile.active_sites_allowed).exclude(booking__archived=False)
    campaign_pks = request.GET.getlist('campaign_pks', None)
    filtered = False
    
    if campaign_pks:
        try:
            leads = leads.filter(campaign__in=Campaign.objects.filter(pk__in=campaign_pks))
            filtered = True
            request.GET['campaign_pks'] = campaign_pks
            context['campaigns'] = Campaign.objects.filter(pk__in=campaign_pks, site__company=request.user.profile.company)
            # request.GET['site_pks'] = [context['campaign'].site.pk]
        except Exception as e:
            pass
    campaign_category_pks = get_campaign_category_pks_from_request(request)

    if request.META.get("HTTP_HX_REQUEST", 'false') == 'false' or request.GET.get('use_defaults', None):
        context['use_defaults'] = True
        if request.user.profile.campaign_category:
            campaign_category_pks = [request.user.profile.campaign_category.pk]

    if campaign_category_pks:
        try:
            context['campaign_categorys'] = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
            if not filtered:
                leads = leads.filter(campaign__campaign_category__in=context['campaign_categorys'])
                campaigns = campaigns.filter(campaign_category__in=context['campaign_categorys'])
                filtered = True
                # request.GET['site_pk'] = context['campaign_category'].site.pk
            request.GET['campaign_category_pks'] = campaign_category_pks
        except Exception as e:
            pass
    if request.GET['site_pks']:
        try:
            if not filtered:
                leads = leads.filter(campaign__site__in=context['sites'])
                filtered = True    
        except:
            pass
    leads = leads.annotate(calls=Count('call')).order_by('last_dragged')
    
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
    context['campaigns'] = campaigns
    context['campaign_categorys'] = get_campaign_category_qs(request)
    return context
@login_required
def refresh_leads_board(request):
    return render(request, 'campaign_leads/htmx/leads_board.html', get_leads_board_context(request))


@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class BookingsOverviewView(TemplateView):
    # this class is used to display the campaign bookings overview
    template_name='campaign_leads/bookings_overview/bookings_overview.html'
    def get_context_data(self, **kwargs):
        context = super(BookingsOverviewView, self).get_context_data(**kwargs)    
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/bookings_overview/bookings_overview_htmx.html'   
            context['campaigns'] = get_campaign_qs(self.request)
            context['campaign_categorys'] = get_campaign_category_qs(self.request)
        context.update(get_booking_table_context(self.request))
        return context
def get_booking_table_context(request):
    #this function is used to get the context for the booking table and refresh_booking_table_htmx
    request.GET._mutable = True     
    context = {}
    # This need further testing. You can archive then sell and it won't show anywhere in the whole ui
    leads = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site__in=request.user.profile.active_sites_allowed).exclude(booking__archived=True)
    campaign_pks = request.GET.getlist('campaign_pks', None)

    campaign_category_pks = request.GET.getlist('campaign_category_pks', None)
    if request.META.get("HTTP_HX_REQUEST", 'false') == 'false' or request.GET.get('use_defaults', None):
        context['use_defaults'] = True
        if request.user.profile.campaign_category:
            campaign_category_pks = [request.user.profile.campaign_category.pk]

    context['sites'] = list(get_site_pks_from_request_and_return_sites(request))
    campaigns = get_campaign_qs(request)
    if campaign_pks:
        leads = leads.filter(campaign__pk__in=campaign_pks)
        request.GET['campaign_pks'] = campaign_pks       

    elif campaign_category_pks:
        try:
            context['campaign_categorys'] = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
            leads = leads.filter(campaign__campaign_category__in=context['campaign_categorys'])
            campaigns = campaigns.filter(campaign_category__in=context['campaign_categorys'])
            # request.GET['site_pks'] = context['campaign_category'].site.pk
            # request.GET['campaign_category_pks'] = campaign_category_pks
        except Exception as e:
            pass
    elif context['sites']:
        for item in leads:
            print(item.campaign.site)
        leads = leads.filter(campaign__site__in=context['sites'])

    # context['archived_count'] = leads.filter(archived=True).count()
    archived_filter = (request.GET.get('archived', '').lower() =='true')
    if not archived_filter:
        leads = leads.exclude(booking__created=None)
    leads = leads.filter(archived=archived_filter)   
    context['archived'] = archived_filter
    
    sold_filter = (request.GET.get('sold', '').lower() =='true')
    if sold_filter:        
        leads = leads.filter(sale__archived=False)   
    else:
        leads = leads.exclude(sale__archived=False)   
    context['sold'] = sold_filter

    context['booking_needed_count'] = leads.filter(booking=None).count()
    context['leads'] = leads
    context['company'] = request.user.profile.company
    context['campaigns'] = campaigns
    context['campaign_categorys'] = get_campaign_category_qs(request)
    return context
@login_required
def refresh_booking_table_htmx(request):
    return render(request, 'campaign_leads/bookings_overview/bookings_table.html', get_booking_table_context(request))


@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class CampaignConfigurationView(TemplateView):
    #this view is used to configure the campaigns
    template_name='campaign_leads/campaign_configuration/campaign_configuration.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True
        context = super(CampaignConfigurationView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/campaign_configuration/campaign_configuration_htmx.html'  
        company = self.request.user.profile.company
        for site in company.active_sites:
            manual_campaign, created = ManualCampaign.objects.get_or_create(site=site, company=site.company, name = "Manually Created")
            manual_campaign.company = site.company
            manual_campaign.save()
        try:
            for campaign_dict in ActiveCampaignApi(company.active_campaign_api_key, company.active_campaign_url).get_lists(company.active_campaign_url).get('lists',[]):
                campaign, created = ActiveCampaign.objects.get_or_create(
                    active_campaign_id = campaign_dict.pop('id'),
                    name = campaign_dict.pop('name'),
                    company = company,
                )
                campaign.json_data = campaign_dict
                campaign.save()
        except Exception as e:
            pass
        if company:
            campaigns = company.get_and_generate_campaign_objects()

        # campaign_category_pk = self.request.GET.get('campaign_category_pk', None)
        # if campaign_category_pk and not campaign_category_pk == 'all':
        #     try:
        #         context['campaign_category'] = CampaignCategory.objects.get(pk=campaign_category_pk)
        #         campaigns = campaigns.filter(campaign_category=context['campaign_category'])
        #         self.request.GET['site_pk'] = context['campaign_category'].site.pk
        #         self.request.GET['campaign_category_pk'] = campaign_category_pk
        #     except Exception as e:
        #         pass
        site_pk = get_single_site_pk_from_request_or_default_profile_site(self.request)
        if site_pk and not site_pk == 'all':
            try:
                campaigns = campaigns.filter(Q(site=None)|Q(site__pk=site_pk))
                self.request.GET['site_pk'] = site_pk    
                context['site'] = Site.objects.get(pk=site_pk)
            except Exception as e:
                pass

        context['campaigns'] = campaigns
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        return context

        
@login_required
def get_campaigns(request, **kwargs):
    #this function is used to get the campaigns from active campaign
    # try:
    if request.user.profile.company:
        request.user.profile.company.get_and_generate_campaign_objects()
    return render(request, f"campaign_leads/filters/campaign_select.html", 
    {'campaigns':get_campaign_qs(request)})
    # except Exception as e:        
    #     logger.error(f"get_campaigns {str(e)}")
    #     return HttpResponse("Couldn't get Campaigns", status=500)

@login_required
def new_call(request, **kwargs):
    #this function is used to add a new call to a lead and refresh the lead article
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            log_datetime = datetime.now()
            call_count = int(kwargs.get('call_count'))
            lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed).annotate(calls=Count('call')).first()
            if get_user_allowed_to_add_call(request.user, lead):
                if lead.calls < call_count:
                    while lead.calls < call_count:
                        call = Call.objects.create(
                            datetime=log_datetime,
                            lead = lead,                        
                            user=request.user
                        )
                        lead = Campaignlead.objects.filter(pk= kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
                elif lead.calls > call_count:
                    while lead.calls > call_count:
                        Call.objects.filter(
                            lead = lead,
                        ).order_by('-datetime').first().delete()
                        lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
                lead.last_dragged = datetime.now()
                lead.save()                
                lead.trigger_refresh_websocket(refresh_position=True)                
                return HttpResponse( status=200)
            return HttpResponse( status=500)
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        raise e



@login_required
@not_demo_or_superuser_check
def campaign_assign_auto_send_template_htmx(request):
    #this function is used to assign a template to a campaign to be auto sent
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'), site__in=request.user.profile.active_sites_allowed)
    send_order = send_order = request.POST['send_order']
    template_pk = request.POST.get('template_pk')
    if not template_pk:
        if not CampaignTemplateLink.objects.filter(send_order__gt=send_order).exclude(template=None):
            CampaignTemplateLink.objects.filter(send_order__gte=send_order).delete()
        else:
            CampaignTemplateLink.objects.filter(send_order=send_order).delete()

    else:
        template = WhatsappTemplate.objects.filter(pk=template_pk).first()
        campaign_template_link, created = CampaignTemplateLink.objects.get_or_create(
            campaign = campaign,
            send_order = send_order,
        )
        campaign_template_link.template = template
        campaign_template_link.save()
    return render(request, 'campaign_leads/htmx/choose_auto_templates.html', {'campaign':campaign})
    
@login_required
@not_demo_or_superuser_check
def campaign_assign_whatsapp_business_account_htmx(request):    
    #this function is used to assign a whatsapp business account to a campaign and refresh the campaign config row
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'), site__in=request.user.profile.active_sites_allowed)
    whatsapp_business_account_pk = request.POST.get('whatsapp_business_account_pk') or 0
    
    campaign.whatsapp_business_account = WhatsappBusinessAccount.objects.filter(pk=whatsapp_business_account_pk).first()
    campaign.campaigntemplatelink_set.all().delete()
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign})
@login_required
@not_demo_or_superuser_check
def campaign_assign_campaign_category_htmx(request):
    #this function is used to assign a campaign category to a campaign and refresh the campaign config row
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'), site__in=request.user.profile.active_sites_allowed)
    campaign_category_pk = request.POST.get('campaign_category_pk') or 0    
    campaign.campaign_category = CampaignCategory.objects.filter(pk=campaign_category_pk).first()
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign})
@login_required
@not_demo_or_superuser_check
def profile_assign_campaign_category_htmx(request):
    #this function is used to assign a campaign category to a profile and refresh the profile config row
    context= {}
    profile = Profile.objects.get(pk=request.POST.get('profile_pk'))
    if get_profile_allowed_to_edit_other_profile(request.user.profile, profile):
        campaign_category_pk = request.POST.get('campaign_category_pk') or 0    
        profile.campaign_category = CampaignCategory.objects.filter(pk=campaign_category_pk).first()
        profile.save()
        context['profile'] = profile
        return render(request, 'core/company_configuration/company_configuration_row.html', context)
    return HttpResponse(status=403)
@login_required
def refresh_campaign_configuration_row(request):
    #this function is used to refresh the campaign config row
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'), site__in=request.user.profile.active_sites_allowed)
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign})
    
@login_required
def campaign_assign_color_htmx(request):
    #this function is used to assign a color to a campaign and refresh the campaign config row    
    campaign = get_object_or_403(Campaign.objects.filter(Q(site=None)|Q(site__in=request.user.profile.active_sites_allowed)), pk=request.POST.get('campaign_pk'))
    campaign.color = hex_to_rgb_tuple(request.POST.get('color', "60F83D"))
    campaign.save()
    return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign})
    

@login_required
@not_demo_or_superuser_check
def campaign_assign_product_cost_htmx(request):
    #this function is used to assign a product cost to a campaign and refresh the campaign config row
    campaign = Campaign.objects.get(pk=request.POST.get('campaign_pk'), site__in=request.user.profile.active_sites_allowed)
    product_cost = request.POST.get('product_cost')
    if product_cost:
        campaign.product_cost = product_cost
        campaign.save()
    return render(request, 'campaign_leads/campaign_configuration/campaign_configuration_row.html', {'campaign':campaign,})

@login_required
def toggle_claim_lead(request, **kwargs):
    #this function is used to toggle the claim of a lead to the request user or toggle it off if there is already a claim
    logger.debug(str(request.user))
    try:
        lead = Campaignlead.objects.get(pk=kwargs.get('lead_pk'), campaign__site__in=request.user.profile.active_sites_allowed)
        if get_user_allowed_to_add_call(request.user, lead):
            if lead.assigned_user == request.user:
                lead.assigned_user = None
            else:
                lead.assigned_user = request.user
            lead.save()
            lead.trigger_refresh_websocket()
        
            return HttpResponse( status=200)
            # return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead, 'max_call_count':0})
        return HttpResponse( status=500)
    except Exception as e:
        logger.debug("get_leads_column_meta_data Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e