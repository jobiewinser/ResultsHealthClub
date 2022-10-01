from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
import logging
from django.contrib.auth.decorators import user_passes_test
logger = logging.getLogger(__name__)

def campaign_leads_enabled_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/products/campaign-leads-product-page"):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    print()
    actual_decorator = user_passes_test(
        lambda u: u.profile.get_company.campaign_leads_enabled,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator