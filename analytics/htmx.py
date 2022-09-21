from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from academy_leads.models import AcademyLead
from core.models import Site
from dateutil import relativedelta

def get_leads_created_in_month_and_year_all_sites(date):
    return AcademyLead.objects.filter(created__month=date.month, created__year=date.year)

@login_required
def get_leads_to_sales(request):
    context = {}
    data_set = []
    month_year_set = []

    site_pk = request.GET.get('site_pk', 'all')
    if not site_pk == 'all':
        site = Site.objects.get(pk=site_pk)
    else:
        site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
    index_date = start_date
    while index_date < end_date + relativedelta.relativedelta(months=1):
        if site:
            qs = site.get_leads_created_in_month_and_year(index_date)
        else:
            qs = get_leads_created_in_month_and_year_all_sites(index_date)
        leads = qs.count()
        sales = qs.filter(sold=True).count()
        if leads:
            percentage = sales/leads*100
        else:
            percentage = 0
        data_set.append({
            'leads':leads,
            'sales':sales,
            'percentage':percentage,
        })
        month_year_set.append((index_date.month, index_date.year))
        index_date = index_date + relativedelta.relativedelta(months=1)
    # querysets = get_leads_created_between_dates(start_date, end_date)  
    # date_tuples = [(1, 9, 2022)]
    # context['date_tuples'] = date_tuples
    # querysets = get_leads_created_in_months(date_tuples)
    # for queryset in querysets:
    #     leads = queryset.count()
    #     sold = queryset.filter(sold=True).count()
    #     if leads:
    #         percentage = sold/leads*100
    #     else:
    #         percentage = 0
    #     data_set.append({
    #         'leads':leads,
    #         'sold':sold,
    #         'percentage':percentage,  
    #         })
    context['data_set'] = data_set
    context['month_year_set'] = month_year_set
    # context['data_points'] = [1, 2, 3, 4]
    # context['labels'] = [1, 2, 3, 4]
    # context['data_points1'] = [10, 20, 30, 40]
    return render(request, 'analytics/htmx/leads_to_sale_data.html', context)