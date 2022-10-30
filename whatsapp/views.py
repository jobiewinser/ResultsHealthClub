from datetime import datetime, timedelta
import logging
from django.conf import settings
from django.http import HttpResponse, QueryDict
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaign, Campaignlead, Call
from core.user_permission_functions import get_available_sites_for_user, get_user_allowed_to_edit_site, get_user_allowed_to_edit_template, get_user_allowed_to_edit_whatsappnumber
from core.views import get_site_pk_from_request
from messaging.models import Message
from whatsapp.api import Whatsapp
from django.views.generic import TemplateView
from whatsapp.models import WHATSAPP_ORDER_CHOICES, WhatsAppMessage, WhatsAppMessageStatus, WhatsAppWebhookRequest, WhatsappMessageImage, WhatsappTemplate, template_variables
from django.template import loader
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel, Site, WhatsappNumber
from random import randrange
from django.contrib.auth.decorators import login_required

# def random_date(start,l):
#     current = start
#     while l >= 0:
#         current = current + timedelta(minutes=randrange(10))
#         l-=1
#     return current

# startDate = datetime(2013, 9, 20,13,00)
# temp1 = random_date(startDate,10)


@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(str(request.GET))
        challenge = request.GET.get('hub.challenge',{})
        response = HttpResponse(challenge)
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        print(str(body))
        logger.debug(str(body))
           
        webhook_object = WhatsAppWebhookRequest.objects.create(
            json_data=body,
            request_type='a',
        )
        for entry in body.get('entry'):
            for change in entry.get('changes'):
                field = change.get('field')
                value = change.get('value')
                if field == 'messages':
                    for message_json in value.get('messages', []):
                        wamid = message_json.get('id')
                        existing_messages = WhatsAppMessage.objects.filter( wamid=wamid ).exclude(wamid="ABGGFlA5Fpa1")
                        if not existing_messages or settings.DEBUG:
                            print("REACHED past if not existing_messages or settings.DEBUG")
                            # Likely a message from a customer     
                            if message_json.get('type') == 'text':
                                handle_received_whatsapp_text_message(message_json, value.get('metadata'), webhook_object) 
                            elif message_json.get('type') == 'image':  
                                handle_received_whatsapp_image_message(message_json, value.get('metadata'), webhook_object) 
                                            

                elif field == 'statuses':
                    for status_dict in value.get('statuses', []):
                        print("STATUS", str(status_dict))
                        whatsapp_messages = WhatsAppMessage.objects.filter(wamid=status_dict.get('id'))
                        if whatsapp_messages:
                            whatsapp_message_status = WhatsAppMessageStatus.objects.get_or_create(
                                whatsapp_message=whatsapp_messages[0],
                                datetime = datetime.fromtimestamp(int(status_dict.get('timestamp'))),
                                status = status_dict.get('status'),
                                raw_webhook = webhook_object,
                            )[0]                

                elif field == 'message_template_status_update':                    
                    templates = WhatsappTemplate.objects.filter(message_template_id=value.get('message_template_id'))
                    if templates:
                        template = templates[0]
                        template.status=value.get('event')
                        reason = value.get('reason', None)
                        print("TEMPLATE REASON", str(reason))
                        # if reason and not reason.lower() == 'none':
                        #     template.latest_reason=value.get('reason')
                        # else:
                        #     template.latest_reason=None
                        template.name=value.get('message_template_name')
                        template.language=value.get('message_template_language')
                        whatsapp = Whatsapp(template.site.whatsapp_access_token)
                        template_live = whatsapp.get_template(template.site.whatsapp_business_account_id, template.message_template_id)
                        # if value.get('event', "") == 'APPROVED':
                        template.name = template_live.get('name')
                        template.pending_name = ""

                        template.category = template_live.get('category')
                        template.pending_category = ""

                        template.language = template_live.get('language')
                        template.pending_language = ""
                        print("template.pending_components", str(template.pending_components))
                        template.components = template.pending_components
                        template.pending_components = []

                        template.last_approval = datetime.now()
                        template.save()
        response = HttpResponse("")
        response.status_code = 200     
        
        return response
        

def handle_received_whatsapp_image_message(message_json, metadata, webhook_object):
    wamid = message_json.get('id')
    to_number = metadata.get('display_phone_number')
    from_number = message_json.get('from')
    
                            # try:
                            #     lead = Campaignlead.objects.get(whatsapp_number__icontains=from_number[-10:])
                            #     # name = lead.name
                            # except Exception as e:
                            #     lead = None
    lead = Campaignlead.objects.filter(whatsapp_number=from_number).last()
    whatsappnumber = WhatsappNumber.objects.get(number=to_number)
    site = Site.objects.get(phonenumber=whatsappnumber)
    datetime_from_request = datetime.fromtimestamp(int(message_json.get('timestamp')))
    whatsapp = Whatsapp(site.whatsapp_access_token)
    media_id = message_json.get('image').get('id')
    from django.core.files import File
    image = whatsapp.get_media_file_from_media_id(media_id)
    print("str(image)", str(image))
    image_object, created = WhatsappMessageImage.objects.get_or_create(
        media_id = media_id
    )       
    image_object.image =  image
    image_object.save()
    whatsapp_message = WhatsAppMessage.objects.create(
        wamid=wamid,
        type='image',
        datetime = datetime_from_request,
        customer_number = from_number,
        inbound=True,
        site=site,
        lead=lead,
        raw_webhook=webhook_object,
        whatsappnumber=whatsappnumber,
    )
    whatsapp_message.image.set([image_object])
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()                            
    message_context = {
        "message": whatsapp_message,
        "site": site,
        "whatsappnumber": whatsappnumber,
    }
    rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
    rendered_html = f"""

    <span id='latest_message_row_{from_number}' hx-swap-oob='delete'></span>
    <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin'>{rendered_message_list_row}</span>

    <span id='messageWindowInnerBody_{from_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>
    
    <span id="chat_notification_{lead.whatsapp_number}" hx-swap-oob='innerHTML'>
        <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                <span class="visually-hidden">New alerts</span>
        </span>
    </span>
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()  
    async_to_sync(channel_layer.group_send)(
        f"messaging_{whatsappnumber.pk}",
        {
            'type': 'chatbox_message',
            "message": rendered_html,
        }
    )

    
    async_to_sync(channel_layer.group_send)(
        f"message_count_{whatsappnumber.site.company.pk}",
        {
            'type': 'messsages_count_update',
            'data':{
                'rendered_html':f"""<span hx-swap-oob="afterbegin:.company_message_count"><span hx-trigger="load" hx-swap="none" hx-get="/update-message-counts/"></span>""",
            }
        }
    )
    logger.debug("webhook sending image to chat end")     


def handle_received_whatsapp_text_message(message_json, metadata, webhook_object):
    wamid = message_json.get('id')
    to_number = metadata.get('display_phone_number')
    from_number = message_json.get('from')
    
                            # try:
                            #     lead = Campaignlead.objects.get(whatsapp_number__icontains=from_number[-10:])
                            #     # name = lead.name
                            # except Exception as e:
                            #     lead = None
    lead = Campaignlead.objects.filter(whatsapp_number=from_number).last()
    whatsappnumber = WhatsappNumber.objects.get(number=to_number)
    site = Site.objects.get(phonenumber=whatsappnumber)
    datetime_from_request = datetime.fromtimestamp(int(message_json.get('timestamp')))
    whatsapp_message = WhatsAppMessage.objects.create(
        wamid=wamid,
        type='text',
        message = message_json.get('text').get('body',''),
        datetime = datetime_from_request,
        customer_number = from_number,
        inbound=True,
        site=site,
        lead=lead,
        raw_webhook=webhook_object,
        whatsappnumber=whatsappnumber,
    )
    # whatsapp_message.save()
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()                            
    message_context = {
        "message": whatsapp_message,
        "site": site,
        "whatsappnumber": whatsappnumber,
    }
    rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
    rendered_html = f"""

    <span id='latest_message_row_{from_number}' hx-swap-oob='delete'></span>
    <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin'>{rendered_message_list_row}</span>

    <span id='messageWindowInnerBody_{from_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>
    
    <span id="chat_notification_{lead.whatsapp_number}" hx-swap-oob='innerHTML'>
        <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                <span class="visually-hidden">New alerts</span>
        </span>
    </span>
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()  
    async_to_sync(channel_layer.group_send)(
        f"messaging_{whatsappnumber.pk}",
        {
            'type': 'chatbox_message',
            "message": rendered_html,
        }
    )

    
    async_to_sync(channel_layer.group_send)(
        f"message_count_{whatsappnumber.site.company.pk}",
        {
            'type': 'messsages_count_update',
            'data':{
                'rendered_html':f"""<span hx-swap-oob="afterbegin:.company_message_count"><span hx-trigger="load" hx-swap="none" hx-get="/update-message-counts/"></span>""",
            }
        }
    )
    logger.debug("webhook sending text to chat end")     
        
# @method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesView(TemplateView):
    template_name='whatsapp/whatsapp_templates.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(WhatsappTemplatesView, self).get_context_data(**kwargs)
        if self.request.META.get("HTTP_HX_REQUEST", 'false') == 'true':
            self.template_name = 'whatsapp/whatsapp_templates_content.html'   
        site_pk = self.request.GET.get('site_pk')
        site = None
        if site_pk:
            if not site_pk == 'all':
                site = Site.objects.get(pk=site_pk)
        if not site:
            if self.request.user.profile.site:
                self.request.GET['site_pk'] = self.request.user.profile.site.pk
                site = self.request.user.profile.site
            else:
                site = Site.objects.filter(company=self.request.user.profile.company.first()).first()
        refresh_template_data(site)
        context['templates'] = WhatsappTemplate.objects.filter(site=site).exclude(archived=True)
        # context['site_list'] = get_available_sites_for_user(self.request.user)
        context['site'] = site
        context['WHATSAPP_ORDER_CHOICES'] = WHATSAPP_ORDER_CHOICES
        return context
def refresh_template_data(site):
    whatsapp = Whatsapp(site.whatsapp_access_token)
    templates = whatsapp.get_templates(site.whatsapp_business_account_id)
    if templates:
        for api_template in templates.get('data', []):
            if not api_template.get('status') == "PENDING_DELETION":
                template, created = WhatsappTemplate.objects.get_or_create(
                    message_template_id = api_template.get('id')
                )                
                if created:
                    template.site = site
                template.company = site.company
                template.status = api_template.get('status')
                template.name = api_template.get('name')
                template.language = api_template.get('language')
                template.category = api_template.get('category')
                # if created:
                # # if not template.components and not template.pending_components:
                #     components = []
                #     for dict in api_template.get('components', []):
                #         json_dict = {}
                #         for k,v in dict.items():
                #             json_dict[k] = str(v)
                #         components.append(json_dict)
                    
                #     template.components = components
                try:
                    template.save()
                except Exception as e:
                    pass
                print()
# @method_decorator(campaign_leads_enabled_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesEditView(TemplateView):
    template_name='whatsapp/whatsapp_template_edit.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(WhatsappTemplatesEditView, self).get_context_data(**kwargs)
        template = WhatsappTemplate.objects.get(pk=kwargs.get('template_pk'))
        if self.request.user.profile.company == template.company:
            context['template'] = template
            context['variables'] = template_variables
            context['categories'] = {
                "TRANSACTIONAL":"Transactional",
                "MARKETING":"Marketing",
            }
            return context
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesReadOnlyView(WhatsappTemplatesEditView):
    def get_context_data(self, **kwargs):  
        context = super(WhatsappTemplatesReadOnlyView, self).get_context_data(**kwargs)
        template = WhatsappTemplate.objects.get(pk=kwargs.get('template_pk'))
        if self.request.user.profile.company == template.company:
            context['readonly'] = True
            return context
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesCreateView(TemplateView):
    template_name='whatsapp/whatsapp_template_create.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(WhatsappTemplatesCreateView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get(pk=kwargs.get('site_pk'))
        context['variables'] = template_variables
        context['categories'] = {
            "TRANSACTIONAL":"Transactional",
            "MARKETING":"Marketing",
        }
        return context

    
@login_required
def whatsapp_approval_htmx(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.company == template.company:
        whatsapp = Whatsapp(template.site.whatsapp_access_token)
        if template.message_template_id:
            whatsapp.edit_template(template)
        else:
            whatsapp.create_template(template)
        return render(request, 'whatsapp/whatsapp_templates_row.html', {'template':WhatsappTemplate.objects.get(pk=request.POST.get('template_pk')), 'site':template.site, 'WHATSAPP_ORDER_CHOICES': WHATSAPP_ORDER_CHOICES})

@login_required
def delete_whatsapp_template_htmx(request):
    body = QueryDict(request.body)
    template = WhatsappTemplate.objects.get(pk=body.get('template_pk'))
    site = template.site
    whatsapp = Whatsapp(site.whatsapp_access_token)
    if template.message_template_id and not template.status == 'PENDING_DELETEION':
        whatsapp.delete_template(site.whatsapp_business_account_id, template.name)
    template.delete()
    template.archived = True
    template.save()
    return HttpResponse("", status=200)

         
@login_required
def whatsapp_clear_changes_htmx(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.company == template.company:
        template.pending_category = None
        template.pending_components = None
        template.pending_language = None
        template.pending_name = None
        template.save()
        return render(request, 'whatsapp/whatsapp_templates_row.html', {'template':template, 'WHATSAPP_ORDER_CHOICES': WHATSAPP_ORDER_CHOICES})
                                                                            # 'site_list': get_available_sites_for_user(request.user), 

@login_required
def whatsapp_number_change_alias(request):
    whatsappnumber = WhatsappNumber.objects.get(pk=request.POST.get('whatsappnumber_pk'))
    if get_user_allowed_to_edit_whatsappnumber(request.user, whatsappnumber):
        alias = request.POST.get('alias', None)
        if alias:
            whatsappnumber.alias = alias
            whatsappnumber.save()
            return HttpResponse("",status=200)
    return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)
@login_required
def whatsapp_number_make_default(request):
    whatsappnumber = WhatsappNumber.objects.get(pk=request.POST.get('whatsappnumber_pk'))
    if get_user_allowed_to_edit_whatsappnumber(request.user, whatsappnumber):
        site = whatsappnumber.site
        site.default_number = whatsappnumber
        site.save()
        return render(request, 'core/htmx/site_configuration_htmx.html', {'whatsapp_numbers':site.get_live_whatsapp_phone_numbers(), 'site': site, })
        # 'site_list': get_available_sites_for_user(request.user)})
    return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)
    

@login_required
def whatsapp_template_change_site(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if get_user_allowed_to_edit_template(request.user, template):
        site_pk = request.POST.get('site_pk', None)
        if site_pk:
            site = Site.objects.get(pk=site_pk)
            if site.company == template.site.company and site.whatsapp_business_account_id == template.site.whatsapp_business_account_id:
                template.site = site
                template.save()
                Campaign.objects.filter(first_send_template=template).update(first_send_template=None)
                Campaign.objects.filter(second_send_template=template).update(second_send_template=None)
                Campaign.objects.filter(third_send_template=template).update(third_send_template=None)
                return HttpResponse("",status=200)
    return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)

@login_required
def whatsapp_number_change_site(request):
    whatsappnumber = WhatsappNumber.objects.get(pk=request.POST.get('whatsappnumber_pk'))
    if get_user_allowed_to_edit_whatsappnumber(request.user, whatsappnumber):
        site_pk = request.POST.get('site_pk', None)
        if site_pk:
            site = Site.objects.get(pk=site_pk)
            if site.company == whatsappnumber.site.company and site.whatsapp_business_account_id == whatsappnumber.site.whatsapp_business_account_id:
                whatsappnumber.site = site
                whatsappnumber.save()
                Site.objects.filter(default_number=whatsappnumber).update(default_number=None)
                WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber).update(site=site)
                return HttpResponse("",status=200)
    return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)

# @login_required
# def add_phone_number(request):
#     site_pk = request.POST.get('site_pk', None)
#     country_code = request.POST.get('country_code', None)
#     phone_number = request.POST.get('phone_number', None)
#     if site_pk and country_code and phone_number:
#         site = Site.objects.get(pk=site_pk)
#         if get_user_allowed_to_edit_site(request.user, site):            
#             whatsapp = Whatsapp(site.whatsapp_access_token)
#             whatsapp.create_phone_number(site.whatsapp_business_account_id, country_code, phone_number)
#             return HttpResponse("",status=200,headers={'HX-Refresh':True})
#         return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)
#     return HttpResponse("Incorrect values entered, please try again.",status=500)

@login_required
def add_whatsapp_business_account(request):
    site_pk = request.POST.get('site_pk', None)
    whatsapp_business_acount_id = request.POST.get('whatsapp_business_acount_id', None)
    if site_pk and whatsapp_business_acount_id:
        site = Site.objects.get(pk=site_pk)
        if get_user_allowed_to_edit_site(request.user, site):            
            whatsapp = Whatsapp(site.whatsapp_access_token)
            whatsapp.create_phone_number(site.whatsapp_business_account_id, country_code, phone_number)
            return HttpResponse("",status=200,headers={'HX-Refresh':True})
        return HttpResponse("You are not ellowed to edit this, please contact your manager.",status=500)
    return HttpResponse("Incorrect values entered, please try again.",status=500)


@login_required
def save_whatsapp_template_ajax(request):
    if request.POST.get('created', False):
        template = WhatsappTemplate()
        template.pending_name = request.POST.get('name')
        template.pending_category = request.POST.get('category')
        template.site = Site.objects.get(pk=request.POST.get('site_pk'))
        template.company = request.user.profile.company
    else:
        template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.company == template.company:
        new_components = [
                {'type': 'HEADER', 'format': 'TEXT', 'text': request.POST.get('header')},
                {'type': 'BODY', 'text': request.POST.get('body')},
                {'type': 'FOOTER', 'text': request.POST.get('footer')},
            ]
        changes_made = False
        if template.pending_components:
            if not new_components == template.pending_components:
                changes_made = True
        else:
            if not new_components == template.components:
                changes_made = True
        
        if changes_made:
            template.pending_components = [
                {'type': 'HEADER', 'format': 'TEXT', 'text': request.POST.get('header')},
                {'type': 'BODY', 'text': request.POST.get('body')},
                {'type': 'FOOTER', 'text': request.POST.get('footer')},
            ]
            
            template.edited_by = request.user
            template.edited = datetime.now()
            template.save()
    return HttpResponse("", status=200)