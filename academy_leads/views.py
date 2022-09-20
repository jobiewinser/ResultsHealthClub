import logging
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from academy_leads.models import AcademyLead, WhatsappTemplate
from active_campaign.api import ActiveCampaign
from active_campaign.models import ActiveCampaignList
from active_campaign.views import get_active_campaign_list_qs, get_and_generate_active_campaign_list_objects
from core.models import Profile, Site
from core.views import get_site_pk_from_request

from whatsapp.api import Whatsapp
logger = logging.getLogger(__name__)

    

try:
    for site in Site.objects.all():
        WhatsappTemplate.objects.get_or_create(site=site, send_order=1)
        WhatsappTemplate.objects.get_or_create(site=site, send_order=2)
        WhatsappTemplate.objects.get_or_create(site=site, send_order=3)
        if not ActiveCampaignList.objects.filter(site=site, manual=True):
            ActiveCampaignList.objects.create(
                name=f"Manually Created ({site.name})",
                site=site,
                manual=True,
            )
except Exception as e:
    pass


@method_decorator(login_required, name='dispatch')
class AcademyLeadsOverviewView(TemplateView):
    template_name='academy_leads/academy_leads_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True       
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'academy_leads/htmx/academy_leads_table_htmx.html'   
        context = super(AcademyLeadsOverviewView, self).get_context_data(**kwargs)      
            
        complete_filter = (self.request.GET.get('complete', '').lower() =='true')
        leads = AcademyLead.objects.filter(complete=complete_filter)
        context['site_list'] = Site.objects.all()
        active_campaign_list_pk = self.request.GET.get('active_campaign_list_pk', None)
        if active_campaign_list_pk:
            leads = leads.filter(active_campaign_list=ActiveCampaignList.objects.get(pk=active_campaign_list_pk))
            self.request.GET['active_campaign_list_pk'] = active_campaign_list_pk
        site_pk = get_site_pk_from_request(self.request)
        if site_pk and not site_pk == 'all':
            leads = leads.filter(active_campaign_list__site__pk=site_pk)
            self.request.GET['site_pk'] = site_pk
        context['leads'] = leads
        # whatsapp = Whatsapp()
        return context
        
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesView(TemplateView):
    template_name='academy_leads/whatsapp_templates.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(WhatsappTemplatesView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'academy_leads/htmx/whatsapp_templates_content.html'   
        site_pk = self.request.GET.get('site_pk')
        if site_pk:
            context['templates'] = WhatsappTemplate.objects.filter(site=Site.objects.get(pk=site_pk))
        else:
            context['templates'] = WhatsappTemplate.objects.filter(site=self.request.user.profile.site)
            self.request.GET['site_pk'] = self.request.user.profile.site.pk
        context['site_list'] = Site.objects.all()
        context['hide_show_all'] = True
        return context
        
@method_decorator(login_required, name='dispatch')
class LeadConfigurationView(TemplateView):
    template_name='active_campaign/leads_configuration.html'

    def get_context_data(self, **kwargs):
        context = super(LeadConfigurationView, self).get_context_data(**kwargs)
        context['active_campaign_lists'] = get_and_generate_active_campaign_list_objects()
        context['site_list'] = Site.objects.all()
        return context