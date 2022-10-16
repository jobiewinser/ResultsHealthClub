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
    sites = get_allowed_site_chats_for_user(user)
    return sites
@register.filter
def get_allowed_number_chats_for_user_tag(site, user):
    chats = get_allowed_number_chats_for_user(site, user)
    return chats

