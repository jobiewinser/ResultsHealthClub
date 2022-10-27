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
    actual_decorator = user_passes_test(
        lambda u: u.profile.company.campaign_leads_enabled,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def check_core_profile_requirements_fulfilled(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/profile-incorrectly-configured"):
    """
    Decorator for views that checks that the user has a profile, a company and at least 1 site allowed
    """
    actual_decorator = user_passes_test(
        lambda u: u.profile and u.profile.company and u.profile.sites_allowed.all() and u.profile.site,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    # actual_decorator_2 = user_passes_test(
    #     lambda u: u.profile.company,
    #     login_url=login_url,
    #     redirect_field_name=redirect_field_name
    # )
    # actual_decorator_3 = user_passes_test(
    #     lambda u: u.profile.sites_allowed.all(),
    #     login_url=login_url,
    #     redirect_field_name=redirect_field_name
    # )
    if function:
        return actual_decorator(function)
        # if actual_decorator_1(function):
        #     if actual_decorator_2(function):
        #         if actual_decorator_3(function):
        #             return False
    return False
    # return actual_decorator