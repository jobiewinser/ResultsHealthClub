import json
import os
import uuid
from core.models import FreeTasterLink, Profile, Site
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import logging
from django.contrib.auth import login
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View 
from core.views import get_site_pk_from_request
from django.http import QueryDict

logger = logging.getLogger(__name__)

# @login_required
# def switch_user(request, **kwargs):
#     logger.debug(str(request.user))
#     try:
#         if request.user.is_authenticated:
#             user_pk = request.POST.get('user_pk')
#             if type(user_pk) == list:
#                 user_pk = user_pk[0]
#             logger.debug(f"TEST {str(user_pk)}")
#             login(request, User.objects.get(pk=user_pk))
#             return render(request, f"core/htmx/profile-nav-section.html", {})   
#     except Exception as e:
#         logger.debug("switch_user Error "+str(e))
#         return HttpResponse(e, status=500)

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        site_pk = get_site_pk_from_request(request)
        if site_pk:
            request.GET['site_pk'] = site_pk
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            context = {'site_list':Site.objects.all()}
            # if template_name == 'switch_user':
            #     context['users'] = User.objects.filter(is_authenticated=True).order_by('first_name')
            if template_name == 'edit_user':
                user_pk = request.GET.get('user_pk', None)
                if user_pk:
                    context["edit_user"] = User.objects.get(pk=user_pk)
            return render(request, f"campaign_leads/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        return HttpResponse(e, status=500)


@method_decorator(login_required, name="dispatch")
class ModifyUser(View):
    def post(self, request, **kwargs):
        try:
            if request.user.is_authenticated:
                action = request.POST.get('action', '')
                if action == 'add':
                    first_name = request.POST.get('first_name', '')
                    last_name = request.POST.get('last_name', '')
                    site_pk = request.POST.get('site_pk', '')
                    user = User.objects.create(username=f"{first_name}{last_name}", 
                                                first_name=first_name,
                                                last_name=last_name,
                                                password=os.getenv("DEFAULT_USER_PASSWORD"), 
                                                is_authenticated=True)
                    Profile.objects.create(user = user, 
                                            avatar = request.FILES['profile_picture'], 
                                            site=Site.objects.get(pk=site_pk))
                elif action == 'edit':
                    first_name = request.POST.get('first_name', '')
                    last_name = request.POST.get('last_name', '')
                    site_pk = request.POST.get('site_pk', '')
                    user = User.objects.get(pk=request.POST['user_pk'])
                    # user.username=f"{first_name}{last_name}" 
                    user.first_name=first_name
                    user.last_name=last_name
                    # user.is_authenticated=True
                    user.save()

                    profile = Profile.objects.get_or_create(user = user)[0]
                    profile_picture = request.FILES.get('profile_picture', None)
                    if profile_picture:
                        profile.avatar = profile_picture
                    if site_pk:
                        profile.site=Site.objects.get(pk=site_pk)
                    profile.save()   

                return render(request, "core/htmx/profile-nav-section.html", {'user':User.objects.get(pk=user.pk)})   
        except Exception as e:
            logger.debug("ModifyUser Post Error "+str(e))
            return HttpResponse(e, status=500)


@login_required
def generate_free_taster_link(request, **kwargs):
    try:
        if request.user.is_authenticated:
            customer_name = request.POST.get('customer_name', '')
            site_pk = request.POST.get('site_pk','')
            if customer_name:
                guid = str(uuid.uuid4())[:8]
                while FreeTasterLink.objects.filter(guid=guid):
                    guid = str(uuid.uuid4())[:8]
                generated_link = FreeTasterLink.objects.create(customer_name=customer_name, user=request.user, guid=guid, site=Site.objects.get(pk=site_pk))
                return render(request, f"core/htmx/generated_link_display.html", {'generated_link':generated_link})  
    except Exception as e:
        logger.debug("generate_free_taster_link Error "+str(e))
        return HttpResponse(e, status=500)


@login_required
def delete_free_taster_link(request, **kwargs):
    logger.debug(str(request.user))
    try:
        if request.user.is_authenticated:
            link_pk = request.POST.get('link_pk','')
            if link_pk:
                FreeTasterLink.objects.get(pk=link_pk).delete()
            return HttpResponse("", "text", 200)
    except Exception as e:
        logger.debug("delete_free_taster_link Error "+str(e))
        return HttpResponse(e, status=500)


        