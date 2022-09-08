from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import GYM_CHOICES, FreeTasterLink, FreeTasterLinkClick  
logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class FreeTasterOverviewView(TemplateView):
    template_name='core/free_taster_overview.html'

    def get_context_data(self, **kwargs):
        context = super(FreeTasterOverviewView, self).get_context_data(**kwargs)
        context['gym_choices'] = GYM_CHOICES
        context['free_taster_links'] = FreeTasterLink.objects.all()
        return context

def free_taster_redirect(request, **kwargs):
    try:
        free_taster_link = FreeTasterLink.objects.get(guid=kwargs.get('guid'))
        FreeTasterLinkClick.objects.create(link=free_taster_link)
    except:
        pass
    return HttpResponseRedirect("https://resultshealthclubs.co.uk/")