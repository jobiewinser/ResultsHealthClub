from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)

@login_required
def mark_done(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("mark_done Error "+str(e))
        return HttpResponse(e, status=500)

