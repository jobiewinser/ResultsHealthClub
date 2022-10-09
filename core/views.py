import os
import sys
import traceback
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from core.models import Company, FreeTasterLink, FreeTasterLinkClick, Profile, Site  
from django.contrib.auth import authenticate
from django.contrib.auth import login
logger = logging.getLogger(__name__)

super_users = User.objects.filter(email="jobiewinser@gmail.com")
if not super_users:
    super_user = User.objects.create_superuser(username="jobiewinser@gmail.com", password=os.getenv('SUPERUSER_PASS'), email="jobiewinser@gmail.com")
else:
    super_user = super_users[0]

companies = Company.objects.filter(company_name="Winser Systems")
if not companies:
    company = Company.objects.create(
        company_name="Winser Systems",
        campaign_leads_enabled=True,
        free_taster_enabled=True,
        )
else:
    company = companies[0]
    
sites = Site.objects.filter(name="Daisy Bank")
if not sites:
    site = Site.objects.create(
        name="Daisy Bank",    
        whatsapp_number = os.getenv('default_whatsapp_number'),
        whatsapp_business_phone_number_id = os.getenv('default_whatsapp_business_phone_number_id'),
        whatsapp_access_token = os.getenv('default_whatsapp_access_token'),
        whatsapp_business_account_id = os.getenv('default_whatsapp_business_account_id'),
        )
    site.company.set([company])
else:
    site = sites[0]

if not Profile.objects.filter(user=super_user):
    profile = Profile.objects.create(
        user = super_user,
        site = site,
    )
    profile.company.set([company])



@method_decorator(login_required, name='dispatch')
class CustomerHomeView(TemplateView):
    template_name='core/customer_home.html'


class HomeView(TemplateView):
    template_name='core/home.html'
class CampaignLeadsProductPageView(TemplateView):
    template_name='core/campaign_leads_product_page.html'

def custom_login_post(request):    
    user = authenticate(username=request.POST.get('username', ''), email=request.POST.get('email', ''), password=request.POST.get('password', ''))
    if user:
        login(request, user)
        return HttpResponse(status=200)
    return HttpResponse(status=404)

@method_decorator(login_required, name='dispatch')
class FreeTasterOverviewView(TemplateView):
    template_name='core/free_taster_overview.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True       
        context = super(FreeTasterOverviewView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'core/htmx/free_taster_table_htmx.html'
        context['site_list'] = Site.objects.all()
        free_taster_links = FreeTasterLink.objects.all()

        site_pk = get_site_pk_from_request(self.request)
        if site_pk:
            free_taster_links = free_taster_links.filter(site__pk=site_pk)
            self.request.GET['site_pk'] = site_pk                    
        context['free_taster_links'] = free_taster_links

        return context
        
@method_decorator(login_required, name='dispatch')
class ConfigurationView(TemplateView):
    template_name='core/configuration.html'

    def get_context_data(self, **kwargs):
        context = super(ConfigurationView, self).get_context_data(**kwargs)        
        return context

def free_taster_redirect(request, **kwargs):
    try:
        free_taster_link = FreeTasterLink.objects.get(guid=kwargs.get('guid'))
        FreeTasterLinkClick.objects.create(link=free_taster_link)
    except:
        pass
    return HttpResponseRedirect("https://WinserSystemss.co.uk/book-free-taster-sessions-abingdon/")

def get_site_pk_from_request(request):    
    site_pk = request.GET.get('site_pk', None)
    if site_pk:
        return site_pk
    profiles = Profile.objects.filter(user=request.user)
    if profiles:
        if profiles.first().site:
            return request.user.profile.site.pk
    

from django.core.mail import send_mail
from django.shortcuts import render
def handler500(request):
    known_errors = []
    try:
        type_, value, tb = sys.exc_info()
        
        if str(value) not in known_errors:
            if request.user.id:
                id = str(request.user.id)
            else:
                id = "None"

            if request.user.username:
                name = str(request.user.username)
            else:
                name = "None"

            if request.META['PATH_INFO']:
                path = os.getenv('SITE_URL')+str(request.META['PATH_INFO'])
            else:
                path = "None"

            body = "None"
            try:
                if request.body:
                    body = str(request.body)
            except:
                pass

            if request.headers:
                headers = str(request.headers)
            else:
                headers = "None"
                
            error_description = f"<p>user id: {str(id)} <br> user name: {str(name)} <br> url: {str(path)}  <br> Error type: {str(value)}  <br> Request Body: {str(body)}  <br> Request Headers: {str(headers)} <br><br><br> Traceback: {str(traceback.format_exception(type, value, tb))}</p>"
            send_mail(
                subject='Winser Systems Prod - 500 error ',
                message=error_description,
                from_email='jobiewinser@gmail.com',
                recipient_list=['jobiewinser@gmail.com'])

    except Exception as e:
        logger.error(   "couldn't send error email", str(e))
    return render(request, '500.html', status=500)