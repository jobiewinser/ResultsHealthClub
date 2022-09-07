from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


@method_decorator(login_required, name='dispatch')
class AcademyLeadsOverviewView(TemplateView):
    template_name='academy_leads/academy_leads_overview.html'

    def get_context_data(self, **kwargs):
        context = super(AcademyLeadsOverviewView, self).get_context_data(**kwargs)
        return context
