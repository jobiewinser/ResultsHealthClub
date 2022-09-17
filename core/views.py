from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Gym  
logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class FreeTasterOverviewView(TemplateView):
    template_name='core/free_taster_overview.html'

    def get_context_data(self, **kwargs):
        context = super(FreeTasterOverviewView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/free_taster_table_htmx.html'
        context['gym_choices'] = Gym.objects.all()
        context['free_taster_links'] = FreeTasterLink.objects.all()
        return context
        
@method_decorator(login_required, name='dispatch')
class ConfigurationView(TemplateView):
    template_name='core/configuration.html'

    def get_context_data(self, **kwargs):
        context = super(ConfigurationView, self).get_context_data(**kwargs)        
        return context

def free_taster_redirect(request, **kwargs):
    try:
        free_taster_link = FreeTasterLink.objects.get(guid=kwargs.get('guid'))
        FreeTasterLinkClick.objects.create(link=free_taster_link)
    except:
        pass
    return HttpResponseRedirect("https://resultshealthclubs.co.uk/book-free-taster-sessions-abingdon/")