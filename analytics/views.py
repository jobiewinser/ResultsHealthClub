from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site  
# Create your views here.
logger = logging.getLogger(__name__)


        
@method_decorator(login_required, name='dispatch')
class AnalyticsOverviewView(TemplateView):
    template_name='analytics/analytics_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(AnalyticsOverviewView, self).get_context_data(**kwargs)    
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'analytics/htmx/analytics_overview_content.html'
        site_pk = self.request.GET.get('site_pk')
        if not site_pk:
            self.request.GET['site_pk'] = self.request.user.profile.site.pk       
        context['site_list'] = Site.objects.all()   
        return context
