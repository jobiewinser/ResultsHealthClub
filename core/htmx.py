import os
from core.models import Profile
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)

@login_required
def switch_user(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_staff:
            user_pk = request.POST.get('user_pk')
            if type(user_pk) == list:
                user_pk = user_pk[0]
            logger.debug(f"TEST {str(user_pk)}")
            login(request, User.objects.get(pk=user_pk, is_superuser=False))
            return render(request, f"academy_leads/htmx/profile_dropdown.html", {})   
    except Exception as e:
        logger.debug("switch_user Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def get_modal_content(request, **kwargs):
    try:
        if request.user.is_staff:
            template_name = request.GET.get('template_name', '')
            context = {}
            if template_name == 'switch_user':
                # context['staff_users'] = User.objects.filter(is_staff=True, is_superuser=False).order_by('first_name')
                context['staff_users'] = User.objects.filter(is_staff=True).order_by('first_name')
            if template_name == 'log_communication':
                context['communication_type'] = kwargs.get('param1')
            return render(request, f"academy_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)

@login_required
def add_user(request, **kwargs):
    try:
        if request.user.is_staff:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            user = User.objects.create(username=f"{first_name}{last_name}", 
                                        first_name=first_name,
                                        last_name=last_name,
                                        password=os.getenv("DEFAULT_USER_PASSWORD"), 
                                        is_staff=True)
            Profile.objects.create(user = user, avatar = request.FILES['profile_picture'])
            login(request, user)
            return render(request, f"academy_leads/htmx/profile_dropdown.html", {})  
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)

        