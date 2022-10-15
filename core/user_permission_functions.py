from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site

def get_available_sites_for_user(user):
    profile = user.profile
    if profile.role == 'a':
        return Site.objects.filter(company=profile.company)
    if profile.sites_allowed.all():
        return profile.sites_allowed.all()
    return Site.objects.filter(pk=profile.site.pk)