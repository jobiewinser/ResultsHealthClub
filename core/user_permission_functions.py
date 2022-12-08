from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site, WhatsappNumber, SiteProfilePermissions

def get_available_sites_for_user(user):
    profile = user.profile
    if profile.role == 'a':
        return Site.objects.filter(company=profile.company)
    if profile.sites_allowed.all():
        return profile.sites_allowed.all()
    return Site.objects.none()

def get_user_allowed_to_toggle_active_campaign(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.toggle_active_campaign
    return False
def get_user_allowed_to_edit_whatsapp_settings(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.edit_whatsapp_settings
    return False
def get_user_allowed_to_edit_site_configuration(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.edit_site_configuration
    return False
def get_user_allowed_to_edit_other_user_permissions(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.edit_user_permissions
    return False






def get_user_allowed_to_edit_whatsappnumber(user, whatsappnumber):
    #TODO
    return True

def get_user_allowed_to_edit_template(user, template):
    #TODO
    return True

def get_user_allowed_to_use_site_messaging(user, site):
    #TODO
    return True

def get_user_allowed_to_use_site_analytics(user, site):
    #TODO
    return True

def get_allowed_site_chats_for_user(user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    # return Site.objects.filter(company=user.profile.site.company)
    return user.profile.sites_allowed.all()

def get_user_allowed_to_send_from_whatsappnumber(user, whatsappnumber):
    #TODO
    return True
def get_allowed_number_chats_for_user(site, user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    return WhatsappNumber.objects.filter(whatsapp_business_account__site=site, archived=False)

def get_user_allowed_to_edit_other_user(request_user, other_user):
    if request_user == other_user:
        return True
    if request_user.profile.role == 'a' and not other_user.profile.role == 'a':
        if request_user.profile.company == other_user.profile.company:
            return True
    elif request_user.profile.role == 'b':
        if request_user.profile.company == other_user.profile.company:
            if other_user.profile.role == 'c':
                return True
    return False


def get_user_allowed_to_add_call(request_user, lead):
    return True

