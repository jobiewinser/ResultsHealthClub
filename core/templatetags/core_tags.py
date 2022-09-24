import os
from django import template
from datetime import datetime, timedelta
import time
import calendar

from dateutil import relativedelta
register = template.Library()

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
def percentage_to_colour(percentage, opacity=1):
    if percentage > 84:
        return f'rgba(96, 248, 61, {str(opacity)})'
    elif percentage > 60:
        return f'rgba(156, 250, 64, {str(opacity)})'
    elif percentage > 36:
        return f'rgba(255, 253, 70, {str(opacity)})'
    elif percentage > 12:
        return f'rgba(239, 131, 44, {str(opacity)})'
    else:
        return f'rgba(231, 36, 29, {str(opacity)})'

    #e7241d for v <= 12%
#ef832c for v > 12% and v <= 36%
#fffd46 for v > 36% and v <= 60%
#9cfa40 for v > 60% and v <= 84%
#60f83d for v > 84%
    
@register.simple_tag
def prefill_date_input_with_now(nothing):
    try:
        return datetime.now().strftime('%Y-%m-%d')
    except:
        return ""

@register.simple_tag
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
def add_year(date, x):  
    try:
        return date + relativedelta.relativedelta(years=x)
    except Exception as e:
        return "Error"
@register.filter
def add_month(date, x):  
    try:
        return date + relativedelta.relativedelta(months=x)
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