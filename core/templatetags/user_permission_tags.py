import os
from django import template
from datetime import datetime, timedelta
import time
import calendar
from dateutil import relativedelta
from django.conf import settings
register = template.Library()
import math
from core.user_permission_functions import *

    
@register.filter
def get_allowed_site_chats_for_user_tag(user):
    return get_allowed_site_chats_for_user(user)
    
@register.filter
def get_allowed_number_chats_for_user_tag(site, user):
    return get_allowed_number_chats_for_user(site, user)
    
@register.filter
def get_available_sites_for_user_tag(user):
    return get_available_sites_for_user(user)
    
@register.filter
def get_user_allowed_to_edit_whatsappnumber_tag(user, whatsappnumber):
    return get_user_allowed_to_edit_whatsappnumber(user, whatsappnumber)
    
@register.filter
def get_user_allowed_to_edit_template_tag(user, template):
    return get_user_allowed_to_edit_template(user, template)
    
@register.filter
def get_user_allowed_to_use_site_messaging_tag(user, site):
    return get_user_allowed_to_use_site_messaging(user, site)
    
@register.filter
def get_user_allowed_to_use_site_analytics_tag(user, site):
    return get_user_allowed_to_use_site_analytics(user, site)
    
@register.filter
def get_user_allowed_to_toggle_active_campaign_tag(profile, site):
    return get_user_allowed_to_toggle_active_campaign(profile, site)
    
@register.filter
def get_user_allowed_to_edit_whatsapp_settings_tag(profile, site):
    return get_user_allowed_to_edit_whatsapp_settings(profile, site)
    
@register.filter
def get_user_allowed_to_edit_site_configuration_tag(profile, site):
    return get_user_allowed_to_edit_site_configuration(profile, site)
    
@register.filter
def get_user_allowed_to_view_site_configuration_tag(profile, site):
    return get_user_allowed_to_view_site_configuration(profile, site)
    
@register.filter
def get_allowed_site_chats_for_user_tag(user):
    return get_allowed_site_chats_for_user(user)
    
@register.filter
def get_user_allowed_to_send_from_whatsappnumber_tag(user, whatsappnumber):
    return get_user_allowed_to_send_from_whatsappnumber(user, whatsappnumber)
    
@register.filter
def get_allowed_number_chats_for_user_tag(site, user):
    return get_allowed_number_chats_for_user(site, user)
    
@register.filter
def get_user_allowed_to_edit_other_user_tag(request_user, other_user):
    return get_user_allowed_to_edit_other_user(request_user, other_user)
        
@register.filter
def get_user_allowed_to_add_call_tag(request_user, lead):
    return get_user_allowed_to_add_call(request_user, lead)