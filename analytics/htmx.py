from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from campaign_leads.models import Call, Campaign, Campaignlead
from core.models import Site
from dateutil import relativedelta
from django.contrib.auth.models import User
from core.templatetags.core_tags import short_month_name
from django.db.models import Sum
from django.db.models import Q, Count
def get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, site=None):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if campaign:
                qs = qs.filter(campaign=campaign)
            elif site:
                qs = qs.filter(campaign__site=site)
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
            # if timeframe_label_string == 'months':
            #     time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]} - {short_month_name((index_date + timeframe).month)} {str((index_date + timeframe).year)[2:]}")
            # elif timeframe_label_string == 'month':
            #     time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]}")
            # elif timeframe_label_string == 'week':
            #     time_label_set.append(f"{index_date} - {index_date + timeframe}")
            # elif timeframe_label_string == 'day':
            #     time_label_set.append(f"{index_date}")
            time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
    
def get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, site=None):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if campaign:
                qs = qs.filter(campaign=campaign)
            elif site:
                qs = qs.filter(campaign__site=site)
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
            # if timeframe_label_string == 'months':
            #     time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]} - {short_month_name((index_date + timeframe).month)} {str((index_date + timeframe).year)[2:]}")
            # elif timeframe_label_string == 'month':
            #     time_label_set.append(f"{short_month_name(index_date.month)} {str(index_date.year)[2:]}")
            # elif timeframe_label_string == 'week':
            #     time_label_set.append(f"{index_date} - {index_date + timeframe}")
            # elif timeframe_label_string == 'day':
            #     time_label_set.append(f"{index_date}")
            time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
    
def get_calls_made_per_day_between_dates(start_date, end_date, user, campaign=None, site=None, get_user_totals=False):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        
        while index_date < end_date + relativedelta.relativedelta(days=1):
            qs = Call.objects.filter(created__gte=index_date, created__lt=index_date + relativedelta.relativedelta(days=1))
            if campaign:
                qs = qs.filter(lead__campaign=campaign)
            elif site:
                qs = qs.filter(lead__campaign__site=site)
                
            unique_callers = qs.order_by('user').values('user').distinct()
            if get_user_totals:
                user_calls_list = []
                for user in unique_callers:
                    user_calls_list.append({
                        'user':user,
                        'calls':qs.filter(user=user).count()
                    })
                data_set.append({
                    'total_calls':qs.count(),
                    'user_calls_list':user_calls_list
                })
            else:
                data_set.append({
                    'total_calls':qs.count(),
                })
            time_label_set.append(f"{index_date}")
            index_date = index_date + relativedelta.relativedelta(days=1)
        return data_set, time_label_set    
    return [],[]

def get_calls_today_dataset(campaign=None, site=None):
    data_set = []
    qs = Call.objects.filter(created__gte= datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))
    if campaign:
        qs = qs.filter(lead__campaign=campaign)
    elif site:
        qs = qs.filter(lead__campaign__site=site)
    unique_users = list(qs.order_by('user').distinct('user').values_list('user', flat=True))
    for user_pk in unique_users:
        user = User.objects.get(pk=user_pk)
        data_set.append((user.profile.name, qs.filter(user=user).count()))
    return data_set, qs

@login_required
def get_leads_to_sales(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        campaign = None
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
        else:
            site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1) 
     
    date_diff = end_date - start_date
    if date_diff > timedelta(days=364):
        # 3 month chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), request.user, timeframe_label_string='months', campaign=campaign, site=site)
    elif date_diff > timedelta(days=83):
        # 1 month chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), request.user, timeframe_label_string='month', campaign=campaign, site=site)
    elif date_diff > timedelta(days=13):
        # 1 week chunks, 
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), request.user, timeframe_label_string='week', campaign=campaign, site=site)
    else:
        # 1 day chunks,
        data_set, time_label_set = get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), request.user, timeframe_label_string='day', campaign=campaign, site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    return render(request, 'analytics/htmx/leads_to_sales_data.html', context)

@login_required
def get_leads_to_bookings(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        campaign = None
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
        else:
            site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
     
    date_diff = end_date - start_date
    if date_diff > timedelta(days=364):
        # 3 month chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), request.user, timeframe_label_string='months', campaign=campaign, site=site)
    elif date_diff > timedelta(days=83):
        # 1 month chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), request.user, timeframe_label_string='month', campaign=campaign, site=site)
    elif date_diff > timedelta(days=13):
        # 1 week chunks, 
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), request.user, timeframe_label_string='week', campaign=campaign, site=site)
    else:
        # 1 day chunks,
        data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), request.user, timeframe_label_string='day', campaign=campaign, site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    return render(request, 'analytics/htmx/leads_to_bookings_data.html', context)

@login_required()
def get_calls_today(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        campaign = None
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
        else:
            site = None

    data_set, raw_qs = get_calls_today_dataset(campaign=campaign, site=site)
        
    context['data_set'] = data_set
    context['raw_qs'] = raw_qs
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'doughnut'
    else:
        context['graph_type'] = 'pie'
    return render(request, 'analytics/htmx/calls_today_data.html', context)
    
@login_required
def get_calls_made_per_day(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        campaign = None
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
        else:
            site = None
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
    
    data_set, time_label_set = get_calls_made_per_day_between_dates(start_date, end_date, request.user, campaign=campaign, site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    return render(request, 'analytics/htmx/calls_made_per_day_data.html', context)

@login_required
def get_current_call_count_distribution(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        campaign = None
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
        else:
            site = None
    if campaign:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign=campaign, complete = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    elif site:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign__site=site, complete = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    else:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, complete = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))

    non_time_filtered_live_opportunities = non_time_filtered_opportunities.filter(complete=False, sold=False)

    call_counts_tuples = []
    index = 0
    if non_time_filtered_opportunities.filter(calls__gte=index):
        while non_time_filtered_opportunities.filter(calls__gte=index):
            if non_time_filtered_opportunities.exclude(calls=index).count():
                queryset_percentage_portion = (non_time_filtered_opportunities.filter(calls=index).count() / non_time_filtered_opportunities.count())*100
            elif non_time_filtered_opportunities.filter(calls=index).count():
                queryset_percentage_portion = 100
            else:
                queryset_percentage_portion = 0
            call_counts_tuples.append((index, non_time_filtered_opportunities.filter(calls=index).count(), non_time_filtered_live_opportunities.filter(calls=index).aggregate(Sum('campaign__product_cost')), queryset_percentage_portion))
            index = index + 1
    else:
        pass
    context['call_counts_tuples'] = call_counts_tuples
    return render(request, 'analytics/htmx/current_call_count_distribution_data.html', context)
@login_required
def get_base_analytics(request):
    # try:
        context = {}
        campaign_pk = request.GET.get('campaign_pk', None)
        if campaign_pk:
            campaign = Campaign.objects.get(pk=campaign_pk)
            site = campaign.site
        else:
            site_pk = request.GET.get('site_pk', 'all')
            campaign = None
            if not site_pk == 'all':
                site = Site.objects.get(pk=site_pk)
            else:
                site = None
        context['start_date'] = request.GET.get('start_date')
        context['end_date'] = request.GET.get('end_date')
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
        if campaign:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign=campaign, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        elif site:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        else:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))

        live_opportunities = opportunities.exclude(complete=True).exclude(sold=True)
        closed_opportunities = opportunities.filter(sold=True)
        lost_opportunities = opportunities.filter(complete=True).exclude(sold=True)

        context['opportunities_count'] = opportunities.count()
        context['live_opportunities_count'] = live_opportunities.count()
        context['closed_opportunities_count'] = closed_opportunities.count()
        context['lost_opportunities_count'] = lost_opportunities.count()
        
        if live_opportunities:
            context['live_value'] = float(live_opportunities.aggregate(Sum('campaign__product_cost')).get('campaign__product_cost__sum', 0))
        else:
            context['live_value'] = 0

        if closed_opportunities:
            context['closed_value'] = float(closed_opportunities.aggregate(Sum('campaign__product_cost')).get('campaign__product_cost__sum', 0))
        else:
            context['closed_value'] = 0

        if lost_opportunities:
            context['lost_value'] = float(lost_opportunities.aggregate(Sum('campaign__product_cost')).get('campaign__product_cost__sum', 0))
        else:
            context['lost_value'] = 0

        if opportunities:
            context['opportunities_value'] = float(opportunities.aggregate(Sum('campaign__product_cost')).get('campaign__product_cost__sum', 0))
        else:
            context['opportunities_value'] = 0

        if context['live_opportunities_count'] or context['lost_opportunities_count']:
            context['conversion_rate'] = (context['closed_opportunities_count'] / (context['live_opportunities_count'] + context['lost_opportunities_count'])) * 100
        elif context['live_opportunities_count']:
            context['conversion_rate'] = 100
        else:
            context['conversion_rate'] = 0
        context['start_date'] = start_date
        context['end_date'] = end_date
        # context['call_distribution'] = 
        return render(request, 'analytics/htmx/base_analytics.html', context)
    # except Exception as e:
    #     pass