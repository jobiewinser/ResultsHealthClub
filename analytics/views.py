from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from campaign_leads.views import get_campaign_qs, get_campaign_category_qs
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site
from core.user_permission_functions import get_available_sites_for_user
from core.views import get_site_pks_from_request_and_return_sites  
from core.core_decorators import check_core_profile_requirements_fulfilled
# Create your views here.
from core.models import Site, Subscription
logger = logging.getLogger(__name__)

from campaign_leads.models import Call, Campaignlead, Campaign
        

@method_decorator(login_required, name='dispatch')
@method_decorator(check_core_profile_requirements_fulfilled, name='dispatch')
class AnalyticsOverviewView(TemplateView):
    template_name='analytics/analytics_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(AnalyticsOverviewView, self).get_context_data(**kwargs)     
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'analytics/htmx/analytics_overview_htmx.html'
        context.update(get_analytics_context(self.request))
        return context

def get_analytics_context(request):
    request.GET._mutable = True 
    context = {}     
    campaign_pks = request.GET.getlist('campaign_pks', None)
    if campaign_pks:
        try:
            request.GET['campaign_pks'] = campaign_pks
            context['campaign'] = Campaign.objects.filter(pk__in=campaign_pks)
        except:
            pass
    if request.META.get("HTTP_HX_REQUEST", 'false') == 'false' or request.GET.get('use_defaults', None):
        context['use_defaults'] = True
        context['sites'] = Site.objects.filter(pk=request.user.profile.site.pk).exclude(active=False)
    else:
        context['sites'] = get_site_pks_from_request_and_return_sites(request)  
    context['start_date'] = request.GET.get('start_date', None)
    context['end_date'] = request.GET.get('end_date', None)
    context['campaigns'] = get_campaign_qs(request)
    context['campaign_categorys'] = get_campaign_category_qs(request)
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(context['sites'])
    
    return context
    

def refresh_analytics(request):
    return render(request, 'analytics/htmx/analytics_content.html', get_analytics_context(request))

def get_minimum_site_subscription_level_from_site_qs(site_qs):
    if site_qs:
        lowest_subscription_site = site_qs.order_by('subscription__numerical').first()
        if lowest_subscription_site:
            return lowest_subscription_site.subscription
    return Subscription.objects.get(numerical=2)
# def get_minimum_site_subscription_level_from_campaign_qs(campaign_qs):
#     for numerical in [0,1,2]:
#         if campaign_qs.filter(site__subscription__numerical=numerical):
#             return Subscription.objects.get(numerical=numerical)
#     return Subscription.objects.get(numerical=2)
# def get_minimum_site_subscription_level_from_campaign_category_qs(campaign_category_qs):
#     for numerical in [0,1,2]:
#         if campaign_category_qs.filter(site__subscription__numerical=numerical):
#             return Subscription.objects.get(numerical=numerical)
#     return Subscription.objects.get(numerical=2)