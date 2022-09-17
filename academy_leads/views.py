import logging
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from academy_leads.models import AcademyLead, WhatsappTemplate
from active_campaign.api import ActiveCampaign
from active_campaign.models import ActiveCampaignList
from active_campaign.views import get_and_generate_active_campaign_list_objects
from core.models import Site

from whatsapp.api import Whatsapp
logger = logging.getLogger(__name__)
@method_decorator(login_required, name='dispatch')
class AcademyLeadsOverviewView(TemplateView):
    template_name='academy_leads/academy_leads_overview.html'

    def get_context_data(self, **kwargs):
        context = super(AcademyLeadsOverviewView, self).get_context_data(**kwargs)#
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'academy_leads/htmx/academy_leads_table_htmx.html'
        context['site_choices'] = Site.objects.all()
        complete_filter = (self.request.GET.get('complete')=='True')
        leads = AcademyLead.objects.filter(complete=complete_filter)
        active_campaign_list_pk = self.request.GET.get('active_campaign_list_pk', None)
        if active_campaign_list_pk:
            leads = leads.filter(active_campaign_list=ActiveCampaignList.objects.get(pk=active_campaign_list_pk))
        context['leads'] = leads

        # whatsapp = Whatsapp()
        return context
        
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesView(TemplateView):
    template_name='academy_leads/whatsapp_templates.html'

    def get_context_data(self, **kwargs):
        context = super(WhatsappTemplatesView, self).get_context_data(**kwargs)
        context['templates'] = WhatsappTemplate.objects.all()
        return context
        
@method_decorator(login_required, name='dispatch')
class LeadConfigurationView(TemplateView):
    template_name='active_campaign/leads_configuration.html'

    def get_context_data(self, **kwargs):
        context = super(LeadConfigurationView, self).get_context_data(**kwargs)
        context['active_campaign_lists'] = get_and_generate_active_campaign_list_objects()
        context['sites'] = Site.objects.all()
        return context
    


    