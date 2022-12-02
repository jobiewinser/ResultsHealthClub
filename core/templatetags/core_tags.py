import os
from django import template
from datetime import datetime, timedelta
import time
import calendar

from dateutil import relativedelta
from django.conf import settings
register = template.Library()
from campaign_leads.views import rgb_to_hex_tuple, hex_to_rgb_tuple

import math

def roundup(x, round_target):
    return int(int(math.ceil(x / round_target)) * round_target)

@register.filter
def month_name(month_number):
    return calendar.month_name[month_number]
@register.filter
def short_month_name(month_number):
    return calendar.month_name[month_number][:3]
@register.filter
def first_x_chars(var,x):
    return str(var)[:x]
@register.filter
def last_x_chars(var,x):
    return str(var)[x:]
@register.simple_tag
def get_env_var(key):
    return os.environ.get(key)    
@register.filter
def settings_value(name):
    return getattr(settings, name, "")

@register.filter
def roundup_tag(number, round_target):
    try:
        return roundup(float(number), float(round_target))
    except:
        return ""
@register.filter
def sum_cost_tag(queryset_or_list):
    total_cost = 0
    try:
        for item in queryset_or_list:
            total_cost = total_cost + float(item.cost)
        return total_cost
    except:
        return "Error"

@register.filter
def percentage_to_colour(percentage, opacity=1):
    try:
        percentage = int(percentage or 0)
        opacity = str(opacity)
        if percentage > 84:
            return f'rgba(96, 248, 61, {opacity})'
        elif percentage > 60:
            return f'rgba(156, 250, 64, {opacity})'
        elif percentage > 36:
            return f'rgba(255, 253, 70, {opacity})'
        elif percentage > 12:
            return f'rgba(239, 131, 44, {opacity})'
        else:
            return f'rgba(231, 36, 29, {opacity})'
    except:
        return f'rgba(231, 36, 29, {opacity})'
    #e7241d for v <= 12%
#ef832c for v > 12% and v <= 36%
#fffd46 for v > 36% and v <= 60%
#9cfa40 for v > 60% and v <= 84%
#60f83d for v > 84%
    
@register.filter
def prefill_date_input_with_now(nothing):
    try:
        return datetime.now().strftime('%Y-%m-%d')
    except:
        return ""

@register.filter
def prefill_time_input_with_now(nothing):
    try:
        return datetime.now().strftime('%H:%M')
    except:
        return ""

@register.filter
def nice_date_tag(date):
    try:
        date = date + datetime.timedelta(hours=1)
        date = (date.date() - date(1970, 1, 1)).total_seconds()
        # just for preview/phrase editing
        date = datetime.strptime(str(date), '%d-%m-%Y')
    except Exception as e:
        pass
    try:
        return str(date.strftime("%-d %B %Y"))
    except Exception as e:
        return str(date)

@register.filter
def nice_datetime_tag(date):
    try:
        if date.date() == datetime.today().date():
            return f"{date.strftime('%H:%M')} - today"
        return str(date.strftime("%H:%M - %-d %B %Y"))
    except Exception as e:
        return str(date)

@register.filter
def nice_message_datetime_tag(date):
    try:
        if date.date() == datetime.today().date():
            return f"{date.strftime('%H:%M')}"
        return str(date.strftime("%-d %B %Y"))
    except Exception as e:
        return str(date)

    
@register.filter
def timestamp(date):
    try:
        return time.mktime(date.timetuple())        
    except Exception as e:
        return 0000000000.0

@register.filter
def get_type(value):
    return type(value)

@register.filter
def str_to_int(value):
    try:
        return int(value)
    except:
        return value

@register.filter
def division_percentage(num, divider):  
    try:
        return (int(num) / int(divider)) * 100
    except Exception as e:
        return 0
@register.filter
def division_percentage_max_100(num, divider):  
    try:
        total = (int(num) / int(divider)) * 100
        if total < 100:
            return total
        return 100
    except Exception as e:
        return 0
        
@register.filter
def division(num, divider):  
    try:
        return int(num) / int(divider)
    except Exception as e:
        return 0
        
@register.filter
def multiplication(num1, num2):  
    try:
        return int(num1) * int(num2)
    except Exception as e:
        return 0
@register.filter
def censor(str):  
    try:
        return "*" * len(str)
    except Exception as e:
        return "Error"

@register.filter
def add_years(date, x):  
    try:
        return date + relativedelta.relativedelta(years=x)
    except Exception as e:
        return "Error"
@register.filter
def add_months(date, x):  
    try:
        return date + relativedelta.relativedelta(months=x)
    except Exception as e:
        return "Error"
@register.filter
def add_days(date, x):  
    try:
        return date + relativedelta.relativedelta(days=x)
    except Exception as e:
        return "Error"

@register.filter
def date_to_date_input_prefill(date):
    try:
        return date.strftime('%Y-%m-%d')
    except:
        return date
        
@register.filter
def today_date_input_tag(anything):
    return datetime.now().strftime('%Y-%m-%d')
@register.filter
def today_date_tag(anything):
    return datetime.now()
@register.filter
def get_key_in_get_or_post(request, key):
    if request.method == 'GET':
        return request.GET.get(key, None)
    if request.method == 'POST':
        return request.POST.get(key, None)
    return None


@register.filter
def company_outstanding_whatsapp_messages_tag(user):
    return user.profile.company.outstanding_whatsapp_messages(user)
@register.filter
def site_outstanding_whatsapp_messages_tag(site, user):
    if site in user.profile.sites_allowed.all():
        return site.outstanding_whatsapp_messages(user)
    return 0
@register.filter
def whatsappnumber_outstanding_whatsapp_messages_tag(whatsappnumber, user):
    if whatsappnumber.whatsapp_business_account.site in user.profile.sites_allowed.all():
        return whatsappnumber.outstanding_whatsapp_messages(user)
    return 0

@register.filter
def active_errors_for_customer_number_tag(whatsappnumber, customer_number):
    return whatsappnumber.active_errors_for_customer_number(customer_number)
    

@register.filter
def hex_to_rgb_tuple_tag(hex):
	return hex_to_rgb_tuple(hex)


@register.filter
def rgb_to_hex_tuple_tag(rgb_string):
    return rgb_to_hex_tuple(rgb_string)

@register.filter
def queryset_last_x(qs, x):
    return qs.order_by('-pk')[:x]
