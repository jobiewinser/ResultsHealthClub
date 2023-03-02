import re
from django.core.exceptions import PermissionDenied
from django.shortcuts import _get_queryset
def normalize_phone_number(number):
    number = re.sub('[^0-9]','', str(number))
    if number[:3] == '440':
        return number[2:]
    elif number[:2] == '44':
        return '0' + number[2:]
    elif number[:2] == '00':
        return number[1:]
    return number
def get_object_or_403(klass, *args, **kwargs):
    """
    Use get() to return an object, or raise a Http404 exception if the object
    does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Like with QuerySet.get(), MultipleObjectsReturned is raised if more than
    one object is found.
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_403() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise PermissionDenied()