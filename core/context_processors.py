"""
A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the 'context_processors' option of the configuration
of a DjangoTemplates backend and used by RequestContext.
"""

import itertools

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.functional import SimpleLazyObject, lazy
from core.models import Subscription

def demo(request):
    """
    Return context variables helpful for debugging.
    """
    context_extras = {}
    if settings.DEMO:
        context_extras['demo'] = True
        from django.db import connections

        # Return a lazy reference that computes connection.queries on access,
        # to ensure it contains queries triggered after this function runs.
        context_extras['sql_queries'] = lazy(
            lambda: list(itertools.chain.from_iterable(connections[x].queries for x in connections)),
            list
        )
    return context_extras

def subscription_options(request):
    """
    Shows all currently subscriptions on offer
    """
    context_extras = {}
    context_extras['subscription_options'] = Subscription.objects.filter(visible_to_all=True)
    from django.db import connections
    # Return a lazy reference that computes connection.queries on access,
    # to ensure it contains queries triggered after this function runs.
    context_extras['sql_queries'] = lazy(
        lambda: list(itertools.chain.from_iterable(connections[x].queries for x in connections)),
        list
    )
    return context_extras
    
