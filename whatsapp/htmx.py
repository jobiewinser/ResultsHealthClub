from datetime import datetime, timedelta
import logging
from django.http import HttpResponse
from django.shortcuts import render

from core.views import get_site_pks_from_request_and_return_sites
from whatsapp.api import Whatsapp
logger = logging.getLogger(__name__)
from core.models import Site
from django.contrib.auth.decorators import login_required
from core.core_decorators import *
from core.user_permission_functions import *
from core.models import Site, WhatsappBusinessAccount
from django.contrib.auth.models import User

@login_required
def get_modal_content(request, **kwargs):
    try:
        request.GET._mutable = True
        context = {}
        site_pk = None
        context['sites'] = get_site_pks_from_request_and_return_sites(request)
        if request.user.is_authenticated:
            template_name = request.GET.get('template_name', '')
            # if template_name == 'add_phone_number':
            site_pk = request.GET.get('site_pk', None)
            if site_pk:
                context["site"] = Site.objects.get(pk=site_pk)
            
            return render(request, f"whatsapp/htmx/{template_name}.html", context)   
    except Exception as e:
        logger.debug("get_modal_content Error "+str(e))
        #return HttpResponse(e, status=500)
        raise e


from core.views import get_site_configuration_context
@login_required
@not_demo_or_superuser_check
def deactivate_whatsapp_business_account(request):
    whatsapp_business_account = WhatsappBusinessAccount.objects.get(pk = request.POST.get('whatsapp_business_account_pk'))
    if get_profile_allowed_to_edit_site_configuration(request.user.profile, whatsapp_business_account.site):  
        whatsapp_business_account.active = False
        whatsapp_business_account.save()
        context = {}
        context.update(get_site_configuration_context(request))
        context['hx_swap_oob'] = True
        return render(request, 'core/site_configuration/site_configuration_table_htmx.html', context)
    return HttpResponse(status=403)

@login_required
@not_demo_or_superuser_check
def add_whatsapp_business_account(request):
    # try: 
        site_pk = request.POST.get('site_pk', None)
        whatsapp_business_account_id = request.POST.get('whatsapp_business_account_id', None)
        if site_pk and whatsapp_business_account_id:
            site = request.user.profile.active_sites_allowed.get(pk=site_pk)
            whatsapp = Whatsapp(site.company.whatsapp_access_token) 
            if get_profile_allowed_to_edit_site_configuration(request.user.profile, site):      
                phone_numbers = whatsapp.get_phone_numbers(whatsapp_business_account_id).get('data',[])
                if phone_numbers:   
                    context = {}
                    whatsapp_business_account, created = WhatsappBusinessAccount.objects.get_or_create(whatsapp_business_account_id=whatsapp_business_account_id)
                    phone_number_instances = site.get_live_whatsapp_phone_numbers()
                    if not created:
                        if whatsapp_business_account.active:
                            if whatsapp_business_account.site == site:
                                return HttpResponse(f"This Whatsapp Business Account already belongs to this Site: {site.name}.",status=500)
                            elif whatsapp_business_account.site:
                                return HttpResponse(f"This Whatsapp Business Account already belongs to another Site, please contact Winser Systems.",status=500)
                        else:
                            whatsapp_business_account.site = site
                            whatsapp_business_account.active = True
                            whatsapp_business_account.save()
                            return render(request, 'core/site_configuration/site_configuration_table_htmx.html', {'whatsapp_numbers':site.get_live_whatsapp_phone_numbers(), 'site': site, })
                        # else:
                        #     whatsapp_business_account.delete()
                    whatsapp_business_account.save()
                    whatsapp_business_account.site = site
                    whatsapp_business_account.save()
                    context.update(get_site_configuration_context(request))
                    context['hx_swap_oob'] = True
                    return render(request, 'core/site_configuration/site_configuration_table_htmx.html', context)
                else:
                    return HttpResponse("There are no phone numbers assosciated with that Whatsapp Business Account ID (for your whatsapp credentials).",status=500)
            return HttpResponse("You are not allowed to edit this, please contact your manager.",status=500)
        return HttpResponse("Please enter a whatsapp_business_account_id.",status=500)
    # except Exception as e:
    #     return HttpResponse("Server Error, please try again later.",status=500)