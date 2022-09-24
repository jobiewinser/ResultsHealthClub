from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from academy_leads.models import AcademyLead
from core.models import Site
from dateutil import relativedelta

from core.templatetags.core_tags import short_month_name

def get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, timeframe_label_string='month', site=None):
    if timeframe < relativedelta.relativedelta(years=3):
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = AcademyLead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if site:
                qs = qs.filter(active_campaign_list__site=site)
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
            if timeframe_label_string == 'months':
                time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]} - {short_month_name((index_date + timeframe).month)} {str((index_date + timeframe).year)[2:]}")
            elif timeframe_label_string == 'month':
                time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]}")
            elif timeframe_label_string == 'week':
                time_label_set.append(f"{index_date} - {index_date + timeframe}")
            elif timeframe_label_string == 'day':
                time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
    
def get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, timeframe_label_string='month', site=None):
    if timeframe < relativedelta.relativedelta(years=3):
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = AcademyLead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if site:
                qs = qs.filter(active_campaign_list__site=site)
            leads = qs.count()
            booked_leads_count = qs.exclude(booking=None).count()
            if leads:
                percentage = booked_leads_count/leads*100
            else:
                percentage = 0
            data_set.append({
                'leads':leads,
                'bookings':booked_leads_count,
                'percentage':percentage,
            })
            if timeframe_label_string == 'months':
                time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]} - {short_month_name((index_date + timeframe).month)} {str((index_date + timeframe).year)[2:]}")
            elif timeframe_label_string == 'month':
                time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]}")
            elif timeframe_label_string == 'week':
                time_label_set.append(f"{index_date} - {index_date + timeframe}")
            elif timeframe_label_string == 'day':
                time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
@login_required
def get_leads_to_sales(request):
    context = {}

    site_pk = request.GET.get('site_pk', 'all')
    if not site_pk == 'all':
        site = Site.objects.get(pk=site_pk)
    else:
        site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
     
    date_diff = end_date - start_date
    if date_diff > timedelta(days=364):
        # 3 month chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), timeframe_label_string='months', site=site)
    elif date_diff > timedelta(days=83):
        # 1 month chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), timeframe_label_string='month', site=site)
    elif date_diff > timedelta(days=13):
        # 1 week chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), timeframe_label_string='week', site=site)
    else:
        # 1 day chunks,
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), timeframe_label_string='day', site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'bar'
    else:
        context['graph_type'] = 'line'
    return render(request, 'analytics/htmx/leads_to_sale_data.html', context)

@login_required
def get_leads_to_bookings(request):
    context = {}

    site_pk = request.GET.get('site_pk', 'all')
    if not site_pk == 'all':
        site = Site.objects.get(pk=site_pk)
    else:
        site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
     
    date_diff = end_date - start_date
    if date_diff > timedelta(days=364):
        # 3 month chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), timeframe_label_string='months', site=site)
    elif date_diff > timedelta(days=83):
        # 1 month chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), timeframe_label_string='month', site=site)
    elif date_diff > timedelta(days=13):
        # 1 week chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), timeframe_label_string='week', site=site)
    else:
        # 1 day chunks,
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), timeframe_label_string='day', site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'bar'
    else:
        context['graph_type'] = 'line'
    return render(request, 'analytics/htmx/leads_to_booking_data.html', context)