from datetime import datetime
import logging
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from campaign_leads.models import Call, Campaign, Campaignlead
from active_campaign.api import ActiveCampaign
from active_campaign.models import ActiveCampaignList
from core.core_decorators import campaign_leads_enabled_required
from core.models import Profile, Site
from core.views import get_site_pk_from_request
from django.db.models import Q, Count
from django.db.models import OuterRef, Subquery, Count
from django.db.models import F
from whatsapp.api import Whatsapp
logger = logging.getLogger(__name__)

    

# try:
#     for site in Site.objects.all():
#         WhatsappTemplate.objects.get_or_create(site=site, send_order=1)
#         WhatsappTemplate.objects.get_or_create(site=site, send_order=2)
#         WhatsappTemplate.objects.get_or_create(site=site, send_order=3)
#         if not ActiveCampaignList.objects.filter(site=site, manual=True):
#             ActiveCampaignList.objects.create(
#                 name=f"Manually Created ({site.name})",
#                 site=site,
#                 manual=True,
#             )
# except Exception as e:
#     pass

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
        self.request.GET._mutable = True       
        context = super(CampaignleadsOverviewView, self).get_context_data(**kwargs)  
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/htmx/leads_board_htmx.html'   
            context['campaigns'] = get_campaign_qs(self.request)
        leads = Campaignlead.objects.filter(complete=False, booking=None)
        campaign_pk = self.request.GET.get('campaign_pk', None)
        if campaign_pk:
            try:
                leads = leads.filter(campaign=Campaign.objects.get(pk=campaign_pk))
                self.request.GET['campaign_pk'] = campaign_pk
                context['campaign'] = Campaign.objects.get(pk=campaign_pk)
                self.request.GET['site_pk'] = context['campaign'].site.pk
            except:
                pass
        site_pk = get_site_pk_from_request(self.request)
        if site_pk and not site_pk == 'all':
            try:
                leads = leads.filter(campaign__site__pk=site_pk)
                self.request.GET['site_pk'] = site_pk    
                context['site'] = Site.objects.get(pk=site_pk)
            except:
                pass
        
        context['site_list'] = Site.objects.all()
        leads = leads.annotate(calls=Count('call'), cost=F('campaign__product_cost'))
        
        context['querysets'] = [
            ('Fresh', leads.filter(calls=0), 0)
        ]
        index = 0
        if leads.filter(calls__gt=index):
            while leads.filter(calls__gt=index):
                index = index + 1
                context['querysets'].append(
                    (f"Call {index}", leads.filter(calls=index), index)
                )
            context['querysets'].append(
                (f"Call {index+1}", leads.none(), index+1)
            )
        else:
            context['querysets'].append(
                (f"Call 1", leads.none(), 1)
            )
        context['max_call_count'] = index
            
        # whatsapp = Whatsapp()
        return context
        

@method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CampaignBookingsOverviewView(TemplateView):
    template_name='campaign_leads/campaign_bookings_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(CampaignBookingsOverviewView, self).get_context_data(**kwargs)    
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'campaign_leads/htmx/campaign_bookings_table_htmx.html'   
            context['campaigns'] = get_campaign_qs(self.request)
        leads = Campaignlead.objects.exclude(booking=None)
        campaign_pk = self.request.GET.get('campaign_pk', None)
        if campaign_pk:

            leads = leads.filter(campaign=Campaign.objects.get(pk=campaign_pk))
            self.request.GET['campaign_pk'] = campaign_pk
        site_pk = get_site_pk_from_request(self.request)
        if site_pk and not site_pk == 'all':
            leads = leads.filter(campaign__site__pk=site_pk)
            self.request.GET['site_pk'] = site_pk 
            
        context['complete_count'] = leads.filter(complete=True).count()
        complete_filter = (self.request.GET.get('complete', '').lower() =='true')
        leads = leads.filter(complete=complete_filter)   
        # booking_needed_filter = (self.request.GET.get('booking_needed', '').lower() =='true')
        # if booking_needed_filter:
        #     leads = leads.filter(booking=None)
        context['booking_needed_count'] = leads.filter(booking=None).count()




        context['site_list'] = Site.objects.all()
        context['leads'] = leads
        # whatsapp = Whatsapp()
        return context
        
@method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LeadConfigurationView(TemplateView):
    template_name='campaign_leads/leads_configuration.html'

    def get_context_data(self, **kwargs):
        context = super(LeadConfigurationView, self).get_context_data(**kwargs)
        context['campaigns'] = []
        if self.request.user.profile.company.all():
            context['campaigns'] = self.request.user.profile.company.all().first().get_and_generate_campaign_objects()
        context['site_list'] = Site.objects.all()
        return context

        
@login_required
def get_campaigns(request, **kwargs):
    try:
        if not settings.DEBUG:
            if request.user.profile.company.all():
                request.user.profile.company.all().first().get_and_generate_active_campaign_list_objects()
            return render(request, f"campaign_leads/htmx/campaign_select.html", 
            {'campaigns':get_campaign_qs(request)})
        return render(request, f"campaign_leads/htmx/campaign_select.html", 
        {'campaigns':get_campaign_qs(request)})
    except Exception as e:        
        logger.error(f"get_campaigns {str(e)}")
        return HttpResponse("Couldn't get Campaigns", status=500)

@login_required
def new_call(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            log_datetime = datetime.now()
            call_count = int(kwargs.get('call_count'))
            lead = Campaignlead.objects.filter(pk=kwargs.get('lead_pk')).annotate(calls=Count('call')).first()
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
           
            lead.save()
            return HttpResponse("", status="200")
            # return render(request, 'campaign_leads/htmx/lead_article.html', {'lead':lead,'max_call_count':kwargs.get('max_call_count', 1), 'call_count':call_count})
    except Exception as e:
        logger.debug("new_call Error "+str(e))
        return HttpResponse(e, status=500)
