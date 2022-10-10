from datetime import datetime
import logging
from django.conf import settings
from django.http import HttpResponse, QueryDict
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from campaign_leads.models import Campaignlead, Call
from messaging.consumers import ChatConsumer
from whatsapp.api import Whatsapp
from django.views.generic import TemplateView
from whatsapp.models import WHATSAPP_ORDER_CHOICES, WhatsAppMessage, WhatsAppMessageStatus, WhatsAppWebhook, WhatsappTemplate, template_variables
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator
from core.models import ErrorModel, Site
from asgiref.sync import async_to_sync, sync_to_async
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
           
        webhook = WhatsAppWebhook.objects.create(
            json_data=body,
            request_type='a',
        )
        for entry in body.get('entry'):
            for change in entry.get('changes'):
                field = change.get('field')
                value = change.get('value')
                if field == 'messages':
                    for message in value.get('messages', []):
                        metadata = value.get('metadata')
                        wamid = message.get('id')
                        to_number = metadata.get('display_phone_number')
                        from_number = message.get('from')
                        datetime_from_request = datetime.fromtimestamp(int(message.get('timestamp')))
                        existing_messages = WhatsAppMessage.objects.filter( wamid=wamid ).exclude(wamid="ABGGFlA5Fpa1")
                        print(f"existing_messages", str(existing_messages))
                        print(f"wamid", str(wamid))
                        if not existing_messages or settings.DEBUG:
                            print("REACHED past if not existing_messages or settings.DEBUG")
                            try:
                                lead = Campaignlead.objects.get(whatsapp_number__icontains=from_number[-10:])
                                # name = lead.name
                            except Exception as e:
                                lead = None
                            # Likely a message from a customer     
                            lead = Campaignlead.objects.filter(whatsapp_number=from_number).last()
                            site = Site.objects.get(whatsapp_number=to_number)
                            whatsapp_message = WhatsAppMessage.objects.create(
                                wamid=wamid,
                                message = message.get('text').get('body',''),
                                datetime = datetime_from_request,
                                customer_number = from_number,
                                system_user_number = to_number,
                                inbound=True,
                                site=site,
                                lead=lead,
                                raw_webhook=webhook,
                            )
                            whatsapp_message.save()
                            from channels.layers import get_channel_layer
                            channel_layer = get_channel_layer()
                            if lead:
                                name = lead.name
                            else:
                                name = from_number
                            async_to_sync(channel_layer.group_send)(
                                f"chat_{from_number}_{site.pk}",
                                {
                                    'type': 'chatbox_message',
                                    "message": message.get('text').get('body',''),
                                    "user_name": name,
                                    "whatsapp_number": from_number,
                                    "inbound": True,
                                }
                            )
                            
                            async_to_sync(channel_layer.group_send)(
                                f"chatlist_{site.pk}",
                                {
                                    'type': 'chatlist_message',
                                    "message": message.get('text').get('body',''),
                                    "user_name": name,
                                    "whatsapp_number": from_number,
                                    "user_avatar": "/static/img/blank-profile-picture.png", 
                                    "inbound": True,
                                }
                            )
                            logger.debug("webhook sending to chat end")                     

                elif field == 'statuses':
                    for status_dict in value.get('statuses', []):
                        print("STATUS", str(status_dict))
                        whatsapp_messages = WhatsAppMessage.objects.filter(wamid=status_dict.get('id'))
                        if whatsapp_messages:
                            whatsapp_message_status = WhatsAppMessageStatus.objects.get_or_create(
                                whatsapp_message=whatsapp_messages[0],
                                datetime = datetime.fromtimestamp(int(status_dict.get('timestamp'))),
                                status = status_dict.get('status'),
                                raw_webhook = webhook,
                            )[0]                

                elif field == 'message_template_status_update':                    
                    templates = WhatsappTemplate.objects.filter(message_template_id=value.get('message_template_id'))
                    if templates:
                        template = templates[0]
                        template.status=value.get('event')
                        reason = value.get('reason', None)
                        if reason and not reason.lower() == 'none':
                            template.latest_reason=value.get('reason')
                        else:
                            template.latest_reason=None
                        template.name=value.get('message_template_name')
                        template.language=value.get('message_template_language')
                        whatsapp = Whatsapp(template.site.whatsapp_access_token)
                        template_live = whatsapp.get_template(template.site.whatsapp_business_account_id, template.message_template_id)
                        if value.get('event', "") == 'APPROVED':
                            template.name = template_live.get('name')
                            template.pending_name = ""

                            template.category = template_live.get('category')
                            template.pending_category = ""

                            template.language = template_live.get('language')
                            template.pending_language = ""

                            template.components = template_live.get('components')
                            template.pending_components = []
                        template.save()
        response = HttpResponse("")
        response.status_code = 200     
        
        return response
        
from django.contrib.auth.decorators import login_required
@login_required
def clear_chat_from_session(request):
    try:
        request.session['open_chats'].remove(request.POST.get('whatsapp_number'))
    except Exception as e:
        pass
    return HttpResponse("", "text", 200)
        
from django.contrib.auth.decorators import login_required
@login_required
def add_chat_to_session(request):
    try:
        temp = request.session['open_chats']
        if not 'open_chats' in request.session:
            request.session['open_chats'] = [request.POST.get('whatsapp_number')]
        elif not request.POST.get('whatsapp_number') in request.session['open_chats']:
            request.session['open_chats'].append(request.POST.get('whatsapp_number'))
    except Exception as e:
        pass
    return HttpResponse("", "text", 200)


        
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
        context['site_list'] = Site.objects.all()
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
                template.company = site.get_company
                template.status = api_template.get('status')
                template.name = api_template.get('name')
                template.language = api_template.get('language')
                template.category = api_template.get('category')
                components = []
                for dict in api_template.get('components', []):
                    json_dict = {}
                    for k,v in dict.items():
                        json_dict[k] = str(v)
                    components.append(json_dict)
                
                template.components = components
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
        if self.request.user.profile.get_company == template.company:
            context['template'] = template
            context['variables'] = template_variables
            context['categories'] = {
                "TRANSACTIONAL":"Transactional",
                "MARKETING":"Marketing",
            }
            return context
@method_decorator(login_required, name='dispatch')
class WhatsappTemplatesCreateView(TemplateView):
    template_name='whatsapp/whatsapp_template_create.html'

    def get_context_data(self, **kwargs):
        self.request.GET._mutable = True     
        context = super(WhatsappTemplatesCreateView, self).get_context_data(**kwargs)
        context['variables'] = template_variables
        context['categories'] = {
            "TRANSACTIONAL":"Transactional",
            "MARKETING":"Marketing",
        }
        return context

    
def delete_whatsapp_template_htmx(request):
    body = QueryDict(request.body)
    site = Site.objects.get(pk=body.get('site_pk'))
    whatsapp = Whatsapp(site.whatsapp_access_token)
    template = WhatsappTemplate.objects.get(pk=body.get('template_pk'))
    if template.message_template_id:
        whatsapp.delete_template(site.whatsapp_business_account_id, template.name)
    # template.delete()
    template.archived = True
    return HttpResponse("", status=200)
def whatsapp_approval_htmx(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.get_company == template.company:
        whatsapp = Whatsapp(template.site.whatsapp_access_token)
        if template.message_template_id:
            whatsapp.edit_template(template)
        else:
            whatsapp.create_template(template)
        return render(request, 'whatsapp/whatsapp_templates_row.html', {'template':template, 'site':template.site, 'WHATSAPP_ORDER_CHOICES': WHATSAPP_ORDER_CHOICES})

def whatsapp_assign_send_order_htmx(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.get_company == template.company:
        send_order = request.POST.get('send_order')
        templates_with_send_order_already = WhatsappTemplate.objects.filter(send_order = send_order)
        if templates_with_send_order_already:
            templates_with_send_order_already.update(send_order=0)
        template.send_order = send_order
        template.save()
        return render(request, 'whatsapp/whatsapp_templates_row.html', {'template':template, 
                                                                        'site':template.site,
                                                                        'templates_with_send_order_already':templates_with_send_order_already, 
                                                                        'WHATSAPP_ORDER_CHOICES': WHATSAPP_ORDER_CHOICES})

def whatsapp_clear_changes_htmx(request):
    template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.get_company == template.company:
        template.pending_category = None
        template.pending_components = None
        template.pending_language = None
        template.pending_name = None
        template.save()
        return render(request, 'whatsapp/whatsapp_templates_row.html', {'template':template, 'site':template.site, 'WHATSAPP_ORDER_CHOICES': WHATSAPP_ORDER_CHOICES})

def save_whatsapp_template_ajax(request):
    if request.POST.get('created', False):
        template = WhatsappTemplate()
        template.pending_name = request.POST.get('name')
        template.pending_category = request.POST.get('category')
        if request.user.profile.site:
            template.site = request.user.profile.site
        else:
            template.site = request.user.profile.get_company.site_set.first()
        template.company = request.user.profile.get_company
    else:
        template = WhatsappTemplate.objects.get(pk=request.POST.get('template_pk'))
    if request.user.profile.get_company == template.company:
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

