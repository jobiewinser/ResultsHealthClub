from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site, WhatsappNumber

def get_available_sites_for_user(user):
    profile = user.profile
    if profile.role == 'a':
        return Site.objects.filter(company=profile.company)
    if profile.sites_allowed.all():
        return profile.sites_allowed.all()
    return Site.objects.filter(pk=profile.site.pk)

def get_user_allowed_to_edit_whatsappnumber(user, whatsappnumber):
    #TODO
    return True

def get_user_allowed_to_edit_template(user, template):
    #TODO
    return True

def get_allowed_site_chats_for_user(user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    return Site.objects.filter(company=user.profile.site.company)

def get_allowed_number_chats_for_user(site, user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    return WhatsappNumber.objects.filter(site=site, archived=False)

