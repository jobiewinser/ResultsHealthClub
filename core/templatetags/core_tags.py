import os
from django import template
from datetime import datetime
import time
register = template.Library()

@register.simple_tag
def get_env_var(key):
    return os.environ.get(key)
    
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