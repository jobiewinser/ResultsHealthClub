import os
from django import template
import datetime
register = template.Library()

@register.simple_tag
def get_env_var(key):
    return os.environ.get(key)
    
@register.simple_tag
def prefill_date_input_with_now(nothing):
    try:
        return datetime.datetime.now().strftime('%Y-%m-%d')
    except:
        return ""

@register.simple_tag
def prefill_time_input_with_now(nothing):
    try:
        return datetime.datetime.now().strftime('%H:%M')
    except:
        return ""


    
