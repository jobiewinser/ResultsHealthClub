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

def get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, timeframe, user, campaigns=[], campaign_categorys=[], sites=[]):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        while index_date < end_date + timeframe:
            qs = Campaignlead.objects.filter(created__gte=index_date, created__lt=index_date + timeframe)
            if campaigns:
                qs = qs.filter(campaign__in=campaigns)
            elif campaign_categorys:
                qs = qs.filter(campaign__campaign_category__in=campaign_categorys)
            elif sites:
                qs = qs.filter(campaign__site__in=sites)
            leads = qs.count()

            # Bookings
            bookings = qs.exclude(booking=None).count()
            
            # Sales
            sales = qs.filter(sold=True).count()
            
            data_set.append({
                'leads':leads,
                'bookings':bookings,
                'sales':sales,
            })
            time_label_set.append(f"{index_date}")
            index_date = index_date + timeframe
        return data_set, time_label_set    
    return [],[]
    
def get_calls_made_per_day_between_dates(start_date, end_date, user, campaigns=[], campaign_categorys=[], sites=[], get_user_totals=False):
    if start_date + relativedelta.relativedelta(years=3) > end_date:
        index_date = start_date
        time_label_set = []
        data_set = []
        
        while index_date < end_date + relativedelta.relativedelta(days=1):
            qs = Call.objects.filter(datetime__gte=index_date, datetime__lt=index_date + relativedelta.relativedelta(days=1))
            if campaigns:
                qs = qs.filter(lead__campaign__in=campaigns)
            elif campaign_categorys:
                qs = qs.filter(lead__campaign__campaign_category__in=campaign_categorys)
            elif sites:
                qs = qs.filter(lead__campaign__site__in=sites)
                
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

def get_calls_today_dataset(campaigns=[], campaign_categorys=[], sites=[]):
    data_set = []
    qs = Call.objects.filter(datetime__gte= datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))
    if campaigns:
        qs = qs.filter(lead__campaign__in=campaigns)
    elif campaign_categorys:
        qs = qs.filter(lead__campaign__campaign_category__in=campaign_categorys)
    elif sites:
        qs = qs.filter(lead__campaign__site__in=sites)
    unique_users = list(qs.order_by('user').distinct('user').values_list('user', flat=True))
    if unique_users:
        for user_pk in unique_users:
            if user_pk:
                user = User.objects.get(pk=user_pk)
                data_set.append((user.profile.name, qs.filter(user=user).count()))
    return data_set, qs

def get_sales_today_dataset(campaigns=[], campaign_categorys=[], sites=[]):
    data_set = []
    qs = Campaignlead.objects.filter(marked_sold__gte= datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))
    if campaigns:
        qs = qs.filter(campaign__in=campaigns)
    elif campaign_categorys:
        qs = qs.filter(campaign__campaign_category__in=campaign_categorys)
    elif sites:
        qs = qs.filter(campaign__site__in=sites)
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
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)

    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1) 

    data_set, time_label_set = get_leads_to_bookings_and_sales_between_dates_with_timeframe_differences(start_date, end_date, relativedelta.relativedelta(days=1), request.user, campaigns=campaigns, campaign_categorys=campaign_categorys, sites=sites)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/leads_to_bookings_and_sales_data.html', context)
    
@login_required()
def get_calls_today(request):
    context = {}
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)

    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)

    data_set, raw_qs = get_calls_today_dataset(campaigns=campaigns, campaign_categorys=campaign_categorys, sites=sites)
        
    context['data_set'] = data_set
    context['raw_qs'] = raw_qs
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'polarArea'
    else:
        context['graph_type'] = 'doughnut'
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/calls_today_data.html', context)

@login_required()
def get_sales_today(request):
    context = {}
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)

    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)
    data_set, raw_qs = get_sales_today_dataset(campaigns=campaigns, campaign_categorys=campaign_categorys, sites=sites)
        
    context['data_set'] = data_set
    context['raw_qs'] = raw_qs
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'polarArea'
    else:
        context['graph_type'] = 'doughnut'
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/sales_today_data.html', context)
    
@login_required
def get_calls_made_per_day(request):
    context = {}
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)

    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    # if not request.user.profile.company.check_if_allowed_to_get_analytics(start_date):
    #     start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
    
    data_set, time_label_set = get_calls_made_per_day_between_dates(start_date, end_date, request.user, campaigns=campaigns, campaign_categorys=campaign_categorys, sites=sites)
        
    context['data_set'] = data_set
    context['time_label_set'] = time_label_set
    context['start_date'] = start_date
    context['end_date'] = end_date
    if request.GET.get('graph_type', 'off') == 'on':
        context['graph_type'] = 'line'
    else:
        context['graph_type'] = 'bar'
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/calls_made_per_day_data.html', context)

@login_required
def get_current_call_count_distribution(request):
    context = {}
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)
        
    if campaigns:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign__in=campaigns, archived = False, sold = False, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    if campaign_categorys:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__campaign_category__site__company=request.user.profile.company, booking = None, campaign__campaign_category__in=campaign_categorys, archived = False, sold = False, campaign__campaign_category__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    elif sites:
        non_time_filtered_opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, booking = None, campaign__site__in=sites, archived = False, sold = False).filter(campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
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
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/current_call_count_distribution_data.html', context)
@login_required
def get_pipeline(request):
    context = {}
    campaign_pks = request.GET.getlist('campaign_pks', [])
    campaign_category_pks = request.GET.getlist('campaign_category_pks', [])
    campaigns = None
    campaign_categorys = None
    sites = []
    if campaign_pks:
        campaigns = Campaign.objects.filter(pk__in=campaign_pks)
        sites = Site.objects.filter(campaign__in=campaigns)
    elif campaign_category_pks:
        campaign_categorys = CampaignCategory.objects.filter(pk__in=campaign_category_pks)
        sites = Site.objects.filter(campaigncategory__in=campaign_categorys)
    else:
        site_pks = request.GET.getlist('site_pks', request.user.profile.sites_allowed.all())
        sites = Site.objects.filter(pk__in=site_pks)

    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)
            
    context['start_date'] = request.GET.get('start_date')
    context['end_date'] = request.GET.get('end_date')
    start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    # if not request.user.profile.company.check_if_allowed_to_get_analytics(start_date):
    #     start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + relativedelta.relativedelta(days=1)   
    if campaigns:
        opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__in=campaigns, created__gte=start_date, created__lt=end_date, campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    if campaign_categorys:
        opportunities = Campaignlead.objects.filter(campaign__campaign_category__site__company=request.user.profile.company, campaign__campaign_category__in=campaign_categorys, created__gte=start_date, created__lt=end_date, campaign__campaign_category__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
    elif sites:
        opportunities = Campaignlead.objects.filter(campaign__site__company=request.user.profile.company, campaign__site__in=sites, created__gte=start_date, created__lt=end_date).filter(campaign__site__in=request.user.profile.sites_allowed.all()).annotate(calls=Count('call'))
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
    context['minimum_site_subscription_level_in_query'] = get_minimum_site_subscription_level_from_site_qs(sites)
    return render(request, 'analytics/htmx/pipeline_data.html', context)

def get_minimum_site_subscription_level_from_site_qs(site_qs):
    if site_qs.filter(subscription='free'):
        return 'free'
    if site_qs.filter(subscription='basic'):
        return 'basic'
    if site_qs.filter(subscription='pro'):
        return 'pro'