from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from academy_leads.models import AcademyLead

def get_leads_created_in_months(month_year_tuples_list):
    list_of_return_querysets = []
    for month, year in month_year_tuples_list:
        list_of_return_querysets.append(AcademyLead.objects.filter(created__month=month, created__year=year))
    return list_of_return_querysets
@login_required
def get_leads_to_sales(request):
    context = {}
    date_tuples = [(9,2022)]
    context['date_tuples'] = date_tuples
    querysets = get_leads_created_in_months(date_tuples)
    data_set = []
    for queryset in querysets:
        leads = queryset.count()
        sold = queryset.filter(sold=True).count()
        if leads:
            percentage = sold/leads*100
        else:
            percentage = 0
        data_set.append({
            'leads':leads,
            'sold':sold,
            'percentage':percentage,  
            })
    context['dataset'] = data_set
    return render(request, 'analytics/htmx/leads_to_sale.html', context)