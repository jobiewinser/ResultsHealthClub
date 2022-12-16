from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from campaign_leads.models import Call, Campaign, Campaignlead, CampaignCategory
from core.models import Site
from dateutil import relativedelta
from django.contrib.auth.models import User
from core.templatetags.core_tags import short_month_name
from django.db.models import Sum
from django.db.models import Q, Count
# def get_sales_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, campaign_category=None, site=None):
#     if start_date + relativedelta.relativedelta(years=3) > end_date:
#         index_date = start_date
#         time_label_set = []
#         data_set = []
#         while index_date < end_date + timeframe:
#             qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
#             if campaign:
#                 qs = qs.filter(campaign=campaign)
#             elif site:
#                 qs = qs.filter(campaign__site=site)
#             leads = qs.count()
#             sales = qs.filter(sold=True).count()
#             if leads:
#                 percentage = sales/leads*100
#             else:
#                 percentage = 0
#             data_set.append({
#                 'leads':leads,
#                 'sales':sales,
#                 'percentage':percentage,
#             })
#             time_label_set.append(f"{index_date}")
#             index_date = index_date + timeframe
#         return data_set, time_label_set    
#     return [],[]
def get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, campaign=None, campaign_category=None, site=None):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if campaign:
                qs = qs.filter(campaign=campaign)
            elif campaign_category:
                qs = qs.filter(campaign__campaign_category=campaign_category)
            elif site:
                qs = qs.filter(campaign__site=site)
            leads = qs.count()
            # Bookings
            bookings = qs.exclude(booking=None).count()
            # if leads:
            #     bookings_percentage = bookings/leads*100
            # else:
            #     bookings_percentage = 0
            # Sales
            sales = qs.filter(sold=True).count()
            # if leads:
            #     sales_percentage = sales/leads*100
            # else:
            #     sales_percentage = 0

            data_set.append({
                'leads':leads,
                'bookings':bookings,
                # 'bookings_percentage':bookings_percentage,
                'sales':sales,
                # 'sales_percentage':sales_percentage,
            })
            time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
    
# def get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, timeframe_label_string='month', campaign=None, campaign_category=None, site=None):
#     if start_date + relativedelta.relativedelta(years=3) > end_date:
#         index_date = start_date
#         time_label_set = []
#         data_set = []
#         while index_date < end_date + timeframe:
#             qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
#             if campaign:
#                 qs = qs.filter(campaign=campaign)
#             elif site:
#                 qs = qs.filter(campaign__site=site)
#             leads = qs.count()
#             booked_leads_count = qs.exclude(booking=None).count()
#             if leads:
#                 percentage = booked_leads_count/leads*100
#             else:
#                 percentage = 0
#             data_set.append({
#                 'leads':leads,
#                 'bookings':booked_leads_count,
#                 'percentage':percentage,
#             })            
#             time_label_set.append(f"{index_date}")
#             index_date = index_date + timeframe
#         return data_set, time_label_set    
#     return [],[]
    
def get_calls_made_per_day_between_dates(start_date, end_date, user, campaign=None, campaign_category=None, site=None, get_user_totals=False):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        
        while index_date < end_date + relativedelta.relativedelta(days=1):
            qs = Call.objects.filter(datetime__gte=index_date, datetime__lt=index_date + relativedelta.relativedelta(days=1))
            if campaign:
                qs = qs.filter(lead__campaign=campaign)
            elif campaign_category:
                qs = qs.filter(lead__campaign__campaign_category=campaign_category)
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

def get_calls_today_dataset(campaign=None, campaign_category=None, site=None):
    data_set = []
    qs = Call.objects.filter(datetime__gte= datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))
    if campaign:
        qs = qs.filter(lead__campaign=campaign)
    elif campaign_category:
        qs = qs.filter(lead__campaign__campaign_category=campaign_category)
    elif site:
        qs = qs.filter(lead__campaign__site=site)
    unique_users = list(qs.order_by('user').distinct('user').values_list('user', flat=True))
    if unique_users:
        for user_pk in unique_users:
            if user_pk:
                user = User.objects.get(pk=user_pk)
                data_set.append((user.profile.name, qs.filter(user=user).count()))
    return data_set, qs

def get_sales_today_dataset(campaign=None, campaign_category=None, site=None):
    data_set = []
    qs = Campaignlead.objects.filter(marked_sold__gte= datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))
    if campaign:
        qs = qs.filter(campaign=campaign)
    elif campaign_category:
        qs = qs.filter(campaign__campaign_category=campaign_category)
    elif site:
        qs = qs.filter(campaign__site=site)
    unique_users = list(qs.order_by('sold_by').distinct('sold_by').values_list('sold_by', flat=True))
    if unique_users:
        for user_pk in unique_users:
            if user_pk:
                user = User.objects.get(pk=user_pk)
                data_set.append((user.profile.name, qs.filter(sold_by=user).count()))
    return data_set, qs
    
@login_required
def get_leads_to_bookings_and_sales(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
    campaign = None
    campaign_category = None
    site = None
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    elif campaign_category_pk and not campaign_category_pk == 'all':
        campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
        site = campaign_category.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    if not request.user.profile.company.check_if_allowed_to_get_analytics(start_date):
        start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1) 
     
    # date_diff = end_date - start_date
    # if date_diff > timedelta(days=364):
    #     # 3 month chunks, 
    #     data_set, time_label_set = get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), request.user, campaign=campaign, campaign_category=campaign_category, site=site)
    # elif date_diff > timedelta(days=83):
    #     # 1 month chunks, 
    #     data_set, time_label_set = get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), request.user, campaign=campaign, campaign_category=campaign_category, site=site)
    # elif date_diff > timedelta(days=13):
    #     # 1 week chunks, 
    #     data_set, time_label_set = get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), request.user, campaign=campaign, campaign_category=campaign_category, site=site)
    # else:
    #     # 1 day chunks,
    data_set, time_label_set = get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), request.user, campaign=campaign, campaign_category=campaign_category, site=site)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    return render(request, 'analytics/htmx/leads_to_bookings_and_sales_data.html', context)

# @login_required
# def get_leads_to_bookings(request):
#     context = {}
#     campaign_pk = request.GET.get('campaign_pk', None)
#     if campaign_pk:
#         campaign = Campaign.objects.get(pk=campaign_pk)
#         site = campaign.site
#     else:
#         site_pk = request.GET.get('site_pk', 'all')
#         campaign = None
#         if not site_pk == 'all':
#             site = Site.objects.get(pk=site_pk)
#         else:
#             site = None
#     start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
#     end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
     
#     date_diff = end_date - start_date
#     if date_diff > timedelta(days=364):
#         # 3 month chunks, 
#         data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=3), request.user, timeframe_label_string='months', campaign=campaign, campaign_category=campaign_category, site=site)
#     elif date_diff > timedelta(days=83):
#         # 1 month chunks, 
#         data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(months=1), request.user, timeframe_label_string='month', campaign=campaign, campaign_category=campaign_category, site=site)
#     elif date_diff > timedelta(days=13):
#         # 1 week chunks, 
#         data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(weeks=1), request.user, timeframe_label_string='week', campaign=campaign, campaign_category=campaign_category, site=site)
#     else:
#         # 1 day chunks,
#         data_set, time_label_set = get_bookings_to_leads_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), request.user, timeframe_label_string='day', campaign=campaign, campaign_category=campaign_category, site=site)
        
#     context['data_set'] = data_set
#     context['time_label_set'] = time_label_set
#     context['start_date'] = start_date
#     context['end_date'] = end_date
#     if request.GET.get('graph_type', 'off') == 'on':
#         context['graph_type'] = 'line'
#     else:
#         context['graph_type'] = 'bar'
#     return render(request, 'analytics/htmx/leads_to_bookings_data.html', context)
@login_required()
def get_calls_today(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
    campaign = None
    campaign_category = None
    site = None
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    elif campaign_category_pk and not campaign_category_pk == 'all':
        campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
        site = campaign_category.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)

    data_set, raw_qs = get_calls_today_dataset(campaign=campaign, campaign_category=campaign_category, site=site)
        
    context['data_set'] = data_set
    context['raw_qs'] = raw_qs
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'polarArea'
    else:
        context['graph_type'] = 'doughnut'
    return render(request, 'analytics/htmx/calls_today_data.html', context)

@login_required()
def get_sales_today(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
    campaign = None
    campaign_category = None
    site = None
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    elif campaign_category_pk and not campaign_category_pk == 'all':
        campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
        site = campaign_category.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
    data_set, raw_qs = get_sales_today_dataset(campaign=campaign, campaign_category=campaign_category, site=site)
        
    context['data_set'] = data_set
    context['raw_qs'] = raw_qs
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'polarArea'
    else:
        context['graph_type'] = 'doughnut'
    return render(request, 'analytics/htmx/sales_today_data.html', context)
    
@login_required
def get_calls_made_per_day(request):
    context = {}
    campaign_pk = request.GET.get('campaign_pk', None)
    campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
    campaign = None
    campaign_category = None
    site = None
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    elif campaign_category_pk and not campaign_category_pk == 'all':
        campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
        site = campaign_category.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    if not request.user.profile.company.check_if_allowed_to_get_analytics(start_date):
        start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
    
    data_set, time_label_set = get_calls_made_per_day_between_dates(start_date, end_date, request.user, campaign=campaign, campaign_category=campaign_category, site=site)
        
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
    campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
    campaign = None
    campaign_category = None
    site = None
    if campaign_pk:
        campaign = Campaign.objects.get(pk=campaign_pk)
        site = campaign.site
    elif campaign_category_pk and not campaign_category_pk == 'all':
        campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
        site = campaign_category.site
    else:
        site_pk = request.GET.get('site_pk', 'all')
        if not site_pk == 'all':
            site = Site.objects.get(pk=site_pk)
    if campaign:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign=campaign, archived = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    if campaign_category:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__campaign_category__site__company=request.user.profile.company, booking = None, campaign__campaign_category=campaign_category, archived = False, sold = False, campaign__campaign_category__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    elif site:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign__site=site, archived = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    else:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, archived = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))

    non_time_filtered_live_opportunities = non_time_filtered_opportunities.filter(archived=False, sold=False)

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
def get_pipeline(request):
    # try:
        context = {}
        campaign_pk = request.GET.get('campaign_pk', None)
        campaign_category_pk = request.GET.get('campaign_category_pk', 'all')
        campaign = None
        campaign_category = None
        site = None
        if campaign_pk:
            campaign = Campaign.objects.get(pk=campaign_pk)
            site = campaign.site
        elif campaign_category_pk and not campaign_category_pk == 'all':
            campaign_category = CampaignCategory.objects.get(pk=campaign_category_pk)
            site = campaign_category.site
        else:
            site_pk = request.GET.get('site_pk', 'all')
            if not site_pk == 'all':
                site = Site.objects.get(pk=site_pk)
                
        context['start_date'] = request.GET.get('start_date')
        context['end_date'] = request.GET.get('end_date')
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        if not request.user.profile.company.check_if_allowed_to_get_analytics(start_date):
            start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
        if campaign:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign=campaign, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        if campaign_category:
            opportunities = Campaignlead.objects.filter(campaign__campaign_category__site__company=request.user.profile.company, campaign__campaign_category=campaign_category, created__gte=start_date, created__lt=end_date, campaign__campaign_category__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        elif site:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site=site, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
        else:
            opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))

        live_opportunities = opportunities.exclude(archived=True).exclude(sold=True)
        closed_opportunities = opportunities.filter(sold=True)
        lost_opportunities = opportunities.filter(archived=True).exclude(sold=True)

        context['opportunities'] = opportunities.count()
        context['live_opportunities'] = live_opportunities.count()
        context['closed_opportunities'] = closed_opportunities.count()
        context['lost_opportunities'] = lost_opportunities.count()
        
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

        if context['live_opportunities'] or context['lost_opportunities']:
            context['conversion_rate'] = (context['closed_opportunities'] / (context['live_opportunities'] + context['lost_opportunities'])) * 100
        elif context['live_opportunities']:
            context['conversion_rate'] = 100
        else:
            context['conversion_rate'] = 0
        context['start_date'] = start_date
        context['end_date'] = end_date
        # context['call_distribution'] = 
        return render(request, 'analytics/htmx/pipeline_data.html', context)
    # except Exception as e:
    #     pass

