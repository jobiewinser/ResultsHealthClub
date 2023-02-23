from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponseRedirect
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site, WhatsappNumber, SiteProfilePermissions, CompanyProfilePermissions

def get_available_sites_for_user(user):
    profile = user.profile
    if profile.role == 'a':
        return Site.objects.filter(company=profile.company).exclude(active=False)
    if profile.active_sites_allowed:
        return profile.active_sites_allowed
    return Site.objects.none()

def get_profile_allowed_to_toggle_active_campaign(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.toggle_active_campaign
    return False
def get_profile_allowed_to_toggle_whatsapp_sending(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.toggle_whatsapp_sending
    return False
def get_profile_allowed_to_change_subscription(profile, site):
    if site in profile.sites_allowed.all():
        permissions, created = SiteProfilePermissions.objects.get_or_create(profile=profile, site=site)
        return permissions.change_subscription
    return False
    
def get_profile_allowed_to_edit_site_configuration(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.edit_site_configuration
    return False
    
def get_profile_allowed_to_edit_site_calendly_configuration(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.edit_site_calendly_configuration
    return False

    
def get_profile_allowed_to_view_site_configuration(profile, site):
    permissions = SiteProfilePermissions.objects.filter(profile=profile, site=site).first()
    if permissions:
        return permissions.view_site_configuration
    return False
def get_profile_allowed_to_edit_other_profile_permissions(profile, company):
    permissions = CompanyProfilePermissions.objects.filter(profile=profile, company=company).first()
    if permissions:
        return permissions.edit_user_permissions
    return False
def get_profile_allowed_to_edit_whatsapp_settings(profile, company):
    permissions = CompanyProfilePermissions.objects.filter(profile=profile, company=company).first()
    if permissions:
        return permissions.edit_whatsapp_settings
    return False
def get_profile_allowed_to_edit_profile_permissions(user_profile, target_profile):
    if check_if_profile_is_higher_authority_than_profile(user_profile, target_profile):
        permissions = CompanyProfilePermissions.objects.filter(profile=user_profile, company=user_profile.company).first()
        if permissions:
            if user_profile.role == 'a':
                permissions.edit_user_permissions = True
                permissions.save()
            return permissions.edit_user_permissions
    return False

def check_if_profile_is_higher_authority_than_profile(user_profile, target_profile):
    user_profile.save()
    target_profile.save()
    # owners have authority over themselves
    if user_profile == target_profile and user_profile.role == 'a':
        return True
    # Nobody has authority over another owner
    if target_profile.role == 'a':
        return False
    # owners have authority to edit anybody except other owners
    if user_profile.role == 'a':
        return True
    # Managers have authority over employees
    if user_profile.role == 'b' and target_profile.role == 'c':
        return True
    return False






# def get_user_allowed_to_edit_whatsappnumber(user, whatsappnumber):
#     #TODO
#     return True

# def get_user_allowed_to_edit_template(user, template):
#     #TODO
#     return True

def get_user_allowed_to_use_site_messaging(user, site):
    #TODO
    return True

# def get_user_allowed_to_use_site_analytics(user, site):
#     #TODO
#     return True

def get_allowed_site_chats_for_user(user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    # return Site.objects.filter(company=user.profile.site.company)
    return user.profile.active_sites_allowed.filter(subscription__whatsapp_enabled=True)

def get_allowed_site_chats_for_company(company):
    return company.active_sites.filter(subscription__whatsapp_enabled=True)

def get_user_allowed_to_send_from_whatsappnumber(user, whatsappnumber):
    #TODO
    return True
def get_allowed_number_chats_for_user(site, user):
    #TODO
    # return Site.objects.filter(pk__in=[user.profile.site.pk])
    return WhatsappNumber.objects.filter(whatsapp_business_account__site=site, whatsapp_business_account__active=True)

def get_profile_allowed_to_edit_other_profile(request_profile, other_profile):
    if request_profile == other_profile:
        return True
    if request_profile.role == 'a' and not other_profile.role == 'a':
        if request_profile.company == other_profile.company:
            return True
    elif request_profile.role == 'b':
        if request_profile.company == other_profile.company:
            if other_profile.role == 'c':
                return True
    return False


def get_user_allowed_to_add_call(request_user, lead):
    return True


def companyprofilepermissions_for_company(profile, company):
    return profile.companyprofilepermissions_set.filter(company=company)
