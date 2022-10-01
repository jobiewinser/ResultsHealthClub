import os
import sys
import traceback
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from core.models import FreeTasterLink, FreeTasterLinkClick, Profile, Site  
from django.contrib.auth import authenticate
from django.contrib.auth import login
logger = logging.getLogger(__name__)
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
                subject='Results Prod - 500 error ',
                message=error_description,
                from_email='jobiewinser@live.co.uk',
                recipient_list=['jobiewinser@live.co.uk'])

    except Exception as e:
            logger.error(   "couldn't send error email", str(e))
    return render(request, '500.html', status=500)