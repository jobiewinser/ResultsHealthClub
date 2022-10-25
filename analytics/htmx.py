from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from campaign_leads.models import Campaign, Campaignlead
from core.models import Site
from dateutil import relativedelta

from core.templatetags.core_tags import short_month_name
from django.db.models import Sum
from django.db.models import Q, Count
def get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, site=None):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(campaign__site__company=user.profile.company, created__gte=index_date, created__lt=index_date + timeframe, campaign__site__in=user.profile.sites_allowed.all())
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
    
def get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, site=None):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(campaign__site__company=user.profile.company, created__gte=index_date, created__lt=index_date + timeframe, campaign__site__in=user.profile.sites_allowed.all())
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
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
     
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
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'bar'
    else:
        context['graph_type'] = 'line'
    return render(request, 'analytics/htmx/leads_to_sale_data.html', context)

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
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
     
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
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'bar'
    else:
        context['graph_type'] = 'line'
    return render(request, 'analytics/htmx/leads_to_booking_data.html', context)

@login_required
def get_base_analytics(request):
    try:
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
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')   
        if campaign:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign=campaign, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        elif site:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        else:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        temp1 = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all())
        temp2 = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date, created__lt=end_date)
        temp3 = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date)
        temp4 = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site)
        temp5 = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company)
        temp6 = Campaignlead.objects.filter()
        live_opportunities = opportunities.filter(complete=False, sold=False)
        closed_opportunities = opportunities.filter(complete=True, sold=True)
        lost_opportunities = opportunities.filter(complete=True, sold=False)

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
        index = 0
        call_counts_tuples = []
        if opportunities.filter(calls__gt=index):
            while opportunities.filter(calls__gte=index):
                if opportunities.exclude(calls=index).count():
                    queryset_conversion_rate = (opportunities.filter(calls=index).count() / opportunities.count())*100
                elif opportunities.filter(calls=index).count():
                    queryset_conversion_rate = 100
                else:
                    queryset_conversion_rate = 0
                call_counts_tuples.append((index, opportunities.filter(calls=index).count(), live_opportunities.filter(calls=index).aggregate(Sum('campaign__product_cost')), queryset_conversion_rate))
                index = index + 1
        else:
            pass
        context['call_counts_tuples'] = call_counts_tuples
        # context['data_set'] = data_set
        # context['time_label_set'] = time_label_set
        # if request.GET.get('graph_type', 'off') == 'on':
        #     context['graph_type'] = 'bar'
        # else:
        #     context['graph_type'] = 'line'
        return render(request, 'analytics/htmx/base_analytics.html', context)
    except Exception as e:
        pass