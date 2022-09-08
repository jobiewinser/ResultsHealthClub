from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from academy_leads.models import AcademyLead

from core.models import GYM_CHOICES


@method_decorator(login_required, name='dispatch')
class AcademyLeadsOverviewView(TemplateView):
    template_name='academy_leads/academy_leads_overview.html'

    def get_context_data(self, **kwargs):
        context = super(AcademyLeadsOverviewView, self).get_context_data(**kwargs)#
        print(self.request.META.get("HTTP_HX_REQUEST", 'false'))
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'academy_leads/htmx/academy_leads_table_htmx.html'
        context['gym_choices'] = GYM_CHOICES
        complete_filter = (self.request.GET.get('complete')=='True')
        context['leads'] = AcademyLead.objects.filter(complete=complete_filter)
        return context
        
