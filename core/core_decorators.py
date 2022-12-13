from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
import logging
from django.contrib.auth.decorators import user_passes_test
logger = logging.getLogger(__name__)


def check_core_profile_requirements_fulfilled(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/profile-incorrectly-configured"):
    """
    Decorator for views that checks that the user has a profile, a company and at least 1 site allowed
    """
    actual_decorator = user_passes_test(
        lambda u: u.profile and u.profile.company and u.profile.sites_allowed.all() and u.profile.site,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return False