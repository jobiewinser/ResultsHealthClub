from datetime import datetime, timedelta
import uuid
from django.conf import settings
from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.http import HttpResponse
# from twilio.models import TwilioMessage
from django.db.models import Q, Count
from whatsapp.api import Whatsapp
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)
from polymorphic.models import PolymorphicModel
from whatsapp.models import WhatsAppMessage
from django.template import loader
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.contrib.postgres.fields import ArrayField
from stripe_integration.api import *
from django.core.mail import send_mail
from core.utils import normalize_phone_number
import sys

class Subscription(models.Model):
    NAME_CHOICES = (
                    ('free', 'Free'),
                    ('basic', 'Basic'),
                    ('pro', 'Pro'),
                )
    name = models.CharField(choices=NAME_CHOICES, max_length=5, default="free")
    max_profiles = models.IntegerField(default = 0)
    max_profiles_string = models.TextField(null=True, blank=True)
    analytics_seconds = models.IntegerField(default = 0) #32 days 2764800 #7 days 604800
    stripe_product_id = models.TextField(null=True, blank=True)
    stripe_price_id = models.TextField(null=True, blank=True)
    numerical = models.FloatField(default = 0) #this is a float as all uses of it call |to_int to turn 2.7 to 2 for example. Different prices can therefor be used for the same tier (grandfathered pricing)
    cost = models.FloatField(default = 0)
    whatsapp_enabled = models.BooleanField(default=False)
    bootstrap_colour = models.TextField(null=True, blank=True)
    max_of_this_type = models.IntegerField(default = 0)
    analytics_string = models.TextField(null=True, blank=True)
    analytics_numerical = models.FloatField(default = 0)
    visible_to_all = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.max_profiles:
            self.max_profiles_string = str(self.max_profiles)
        else:
            self.max_profiles_string = "Unlimited"
        super(Subscription, self).save(force_insert, force_update, using, update_fields)

class SiteSubscriptionChange(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True, default=None)
    processed = models.DateTimeField(null=True, blank=True, default=None)
    canceled = models.DateTimeField(null=True, blank=True, default=None)
    users_to_keep = models.ManyToManyField(User, related_name="site_subscription_change_users_to_keep", null=True, blank=True)
    subscription_from = models.ForeignKey("core.Subscription", related_name="site_subscription_change_subscription_from", on_delete=SET_NULL, null=True, blank=True)
    subscription_from_text = models.CharField(max_length=20, null=True, blank=True)
    subscription_to = models.ForeignKey("core.Subscription", related_name="site_subscription_change_subscription_to", on_delete=SET_NULL, null=True, blank=True)
    subscription_to_text = models.CharField(max_length=20, null=True, blank=True)
    version_started = models.CharField(max_length=20, null=True, blank=True)
    site = models.ForeignKey("core.Site", on_delete=SET_NULL, null=True, blank=True)
    stripe_session_id = models.TextField(blank=True, null=True)  
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.subscription_from:
            self.subscription_from_text = str(self.subscription_from.name)
        if self.subscription_to:
            self.subscription_to_text = str(self.subscription_to.name)
        super(SiteSubscriptionChange, self).save(force_insert, force_update, using, update_fields)

    def process(self):
        users_to_keep = self.users_to_keep.all()
        for user in User.objects.filter(profile__sites_allowed=self.site).order_by('profile__role'):
            if not user in users_to_keep:
                profile = user.profile
                profile.sites_allowed.remove(self.site)
                if profile.site == self.site:
                    profile.site = profile.sites_allowed.all().first()
                profile.save()
        self.processed = datetime.now()
        self.save()
        profile = self.completed_by.profile
        profile.sites_allowed.add(self.site)
        profile.save()
        SiteSubscriptionChange.objects.filter(site=self.site, processed=None).update(canceled=datetime.now())        
        # cancel_all_subscriptions(self.site.stripecustomer.customer_id)
        
    def complete(self):
        self.completed = datetime.now()
        self.save()
        
class SiteUsersOnline(models.Model):
    users_online = models.CharField(max_length=1500, default=";")
    site = models.ForeignKey("core.Site", on_delete=models.SET_NULL, null=True, blank=True)
    feature = models.CharField(max_length=50, default="leads")
if not sys.argv[1] in ["makemigrations", "migrate", "collectstatic", "random_leads"]:
    SiteUsersOnline.objects.all().update(users_online="")
class AttachedError(models.Model): 
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    ERROR_TYPES = (
                        ('0101', "You can only edit an active template once every 24 hours"),
                        ('0102', "The system can not send Whatsapp Templates without a template name"),
                        ('0103', "The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)"),
                        ('0104', "the template has been deleted from Whatsapp Manager."),
                        ('1104', "Message failed to send because more than 24 hours have passed since the customer last replied to this number. You can still send a template message at 24 hour intervals instead"),
                        ('1105', "Message failed to send because the Whatsapp account is not yet registered (contact Winser Systems)"),
                        ('1106', "The requested phone number has been deleted"),
                        ('1107', "Phone number probably not on Whatsapp"),
                        ('1108', "The message sent was too long (including any variables). Please edit the whatsapp template to make the offending section shorter or edit the lead/contact's name to be shorter for example."),
                        ('1201', "Whatsapp Template not found Whatsapp's system"),
                        ('1202', "There is no Whatsapp Business linked to this Lead's assosciated Site"),
                        ('1203', "Couldn't auto-send, there is no 1st Whatsapp Template linked to this Lead's Campaign"),
                        # ('1204', "Couldn't auto-send, there is no 2nd Whatsapp Template linked to this Lead's Campaign"),
                        # ('1205', "Couldn't auto-send, there is no 3rd Whatsapp Template linked to this Lead's Campaign"),
                        # ('1206', "Couldn't auto-send, there is no 4th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1207', "Couldn't auto-send, there is no 5th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1208', "Couldn't auto-send, there is no 6th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1209', "Couldn't auto-send, there is no 7th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1210', "Couldn't auto-send, there is no 8th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1211', "Couldn't auto-send, there is no 9th Whatsapp Template linked to this Lead's Campaign"),
                        # ('1212', "Couldn't auto-send, there is no 10th Whatsapp Template linked to this Lead's Campaign"),
                        ('1220', "This site has template messaging currently disabled, reenable it on the site configuration page"),
                        ('1230', "This lead's campaign has no whatsapp number linked to it. Couldn't send first message"),
                        ('1300', "Unknown Error (We will investigate)"),
                        ('1301', "This template is missing a component"),
                        ('1302', "This template needs a name"),
                        ('1303', "One of this template's sections is too long"),
                        ('1304', "A template with this name was recently deleted, please change the template name then try again"),
                    )
    type = models.CharField(choices=ERROR_TYPES, default='c', max_length=5)
    attached_field = models.CharField(null=True, blank=True, max_length=50)
    whatsapp_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    campaign_lead = models.ForeignKey("campaign_leads.Campaignlead", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey("core.Contact", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    site_contact = models.ForeignKey("core.SiteContact", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    
    whatsapp_number = models.ForeignKey("core.WhatsappNumber", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_message = models.ForeignKey("whatsapp.WhatsappMessage", related_name="attached_errors", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="attached_errors", on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey("core.Site", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    customer_number = models.TextField(blank=True, null=True)    
    admin_action_required = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    archived_time = models.DateTimeField(null=True, blank=True)
    additional_info = models.TextField(blank=True, null=True)  
    
class Contact(models.Model):
    first_name_old = models.TextField(null=True, blank=True, max_length=25)
    last_name_old = models.TextField(null=True, blank=True, max_length=25)
    site_old = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey('core.Company', on_delete=models.SET_NULL, null=True, blank=True)
    customer_number = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # @property
    # def name(self):
    #     if self.last_name:
    #         return f"{self.first_name} {self.last_name}"
    #     return self.first_name
    

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.customer_number = normalize_phone_number(self.customer_number)
        super(Contact, self).save(force_insert, force_update, using, update_fields)

class SiteContact(models.Model):
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey('core.Contact', on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    first_name = models.TextField(null=True, blank=True, max_length=25)
    last_name = models.TextField(null=True, blank=True, max_length=25)
    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    @property
    def customer_number(self):
        return self.contact.customer_number
    
    def send_template_whatsapp_message(self, whatsappnumber=None, template=None, communication_method = 'a'):
        print("Contact send_template_whatsapp_message", whatsappnumber, template, communication_method)
        customer_number = self.customer_number
        if settings.DEMO:
            whatsapp_message, created = WhatsAppMessage.objects.get_or_create(
                wamid="",
                datetime=datetime.now(),
                contact=self.contact,
                site_contact=self,
                message=f"""
                <b>Hi {self.first_name}</b>
                <br>
                <br>
                <p>This is a demonstration of the whatsapp system! With the Pro subscription, you can add your own whatsapp accounts and automate sending templates here!</p>
                <small>Thanks from Winser Systems!</small>
                """,
                site=self.site,
                whatsappnumber=whatsappnumber,
                customer_number=customer_number,
                template=template,
                inbound=False,
            )
            send_message_to_websocket(whatsappnumber, customer_number, whatsapp_message, self.site)
            return HttpResponse(status=200)
        from core.models import AttachedError
        if communication_method == 'a' and whatsappnumber:
            if template:    
                AttachedError.objects.filter(
                    type = type,
                    contact = self.contact,
                    site_contact=self,
                    archived = False,
                ).update(archived = True)
                if template.whatsapp_business_account.whatsapp_business_account_id: 
                    AttachedError.objects.filter(
                        type = '1202',
                        contact = self.contact,
                        site_contact=self,
                        archived = False,
                    ).update(archived = True)
                    if template.whatsapp_business_account.site.whatsapp_template_sending_enabled:
                        AttachedError.objects.filter(
                            type = '1220',
                            contact = self.contact,
                            site_contact=self,
                            archived = False,
                        ).update(archived = True)
                        if template.message_template_id:
                            AttachedError.objects.filter(
                                type = '1201',
                                contact = self.contact,
                                site_contact=self,
                                archived = False,
                            ).update(archived = True)
                            whatsapp = Whatsapp(self.contact.company.whatsapp_access_token)
                            template_live = whatsapp.get_template(template.whatsapp_business_account.whatsapp_business_account_id, template.message_template_id)
                            template.name = template_live['name']
                            template.category = template_live['category']
                            template.language = template_live['language']
                            template.save()
                            components =   [] 
                            
                            whole_text = template.render_whatsapp_template_to_html(site_contact=self)
                            counter = 1
                            for component in template.components:
                                params = []
                                component_type = component.get('type', "").lower()
                                # if component_type == 'header':
                                text = component.get('text', '')
                                if component_type in ['header', 'body']:
                                    if '[[1]]' in text:
                                        params.append(              
                                            {
                                                "type": "text",
                                                "text":  self.first_name
                                            }
                                        )
                                        text = text.replace('[[1]]',self.first_name)
                                        counter = counter + 1
                                    if '[[2]]' in text:
                                        raise Exception #investigrate this further, this can't be sent as there may be no campaign linked
                                    # if '[[2]]' in text:
                                    #     params.append(              
                                    #         {
                                    #             "type": "text",
                                    #             "text":  self.campaign.name
                                    #         }
                                    #     )
                                    #     text = text.replace('[[2]]',self.campaign.name)
                                    #     counter = counter + 1
                                if params:
                                    components.append(
                                        {
                                            "type": component_type,
                                            "parameters": params
                                        }
                                    )
                        else:
                            attached_error, created = AttachedError.objects.get_or_create(
                                type = '1201',
                                attached_field = "contact",
                                contact = self.contact,
                                site_contact=self,
                                archived = False,
                            )
                            if not created:
                                attached_error.created = datetime.now()
                                attached_error.save()
                            return HttpResponse("Messaging Error: Couldn't find the specified template", status=400)
                    else:
                        print("errorhere template messaging disabled")
                        attached_error, created = AttachedError.objects.get_or_create(
                            type = '1220',
                            attached_field = "contact",
                            contact = self.contact,
                            site_contact=self,
                            archived = False,
                        )
                        if not created:
                            attached_error.created = datetime.now()
                            attached_error.save()
                        return HttpResponse("Messaging Error: Template Messaging disabled for this site", status=400)
                else:
                    print("errorhere no Whatsapp Business Account Linked")
                    attached_error, created = AttachedError.objects.get_or_create(
                        type = '1202',
                        attached_field = "contact",
                        contact = self.contact,
                        site_contact=self,
                        archived = False,
                    )
                    if not created:
                        attached_error.created = datetime.now()
                        attached_error.save()
                    return HttpResponse("Messaging Error: No Whatsapp Business Account linked", status=400)
                language = {
                    "policy":"deterministic",
                    "code":template.language
                }
                site = self.site
                response = whatsapp.send_template_message(customer_number, whatsappnumber, template, language, components)
                reponse_messages = response.get('messages',[])
                if reponse_messages:
                    for response_message in reponse_messages:
                        whatsapp_message, created = WhatsAppMessage.objects.get_or_create(
                            wamid=response_message.get('id'),
                            datetime=datetime.now(),
                            contact = self.contact,
                            site_contact=self,
                            message=whole_text,
                            site=site,
                            whatsappnumber=whatsappnumber,
                            customer_number=customer_number,
                            template=template,
                            inbound=False,
                        )
                        if created:                        
                            send_message_to_websocket(whatsappnumber, customer_number, whatsapp_message, whatsappnumber.whatsapp_business_account )
                    logger.debug("site.send_template_whatsapp_message success") 
                    return HttpResponse("Message Sent", status=200)
def send_message_to_websocket(whatsappnumber, customer_number, whatsapp_message, site):
    channel_layer = get_channel_layer()          
    message_context = {
        "message": whatsapp_message,
        "site": site,
        "whatsappnumber": whatsappnumber,
    }
    rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
    rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
    rendered_html = f"""

    <span id='latest_message_row_{str(whatsapp_message.site_contact.pk)}' hx-swap-oob='delete'></span>
    <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin'>{rendered_message_list_row}</span>

    <span id='messageWindowInnerBody_{str(whatsapp_message.site_contact.pk)}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>
    """
    
    async_to_sync(channel_layer.group_send)(
        f"messaging_{whatsappnumber.pk}",
        {
            'type': 'chatbox_message',
            "message": rendered_html,
        }
    )
    channel_layer = get_channel_layer()   
    
    async_to_sync(channel_layer.group_send)(
        f"message_count_{whatsappnumber.site.company.pk}",
        {
            'type': 'messages_count_update',
            'data':{
                'rendered_html':f"""<span hx-swap-oob="afterbegin:.company_message_count"><span hx-trigger="load" hx-swap="none" hx-get="/update-message-counts/"></span>""",
            }
        }
    )
# class AttachedWarning(models.Model): 
#     created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     ERROR_TYPES = (
#                         ('0101', "You can only edit an active template once every 24 hours"),
#                         ('0102', "The system can not send Whatsapp Templates without a template name"),
#                         ('0103', "The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)"),
#                         ('1201', "Whatsapp Template not found Whatsapp's system"),
#                         ('1202', "There is no Whatsapp Business linked to this Lead's assosciated Site"),
#                         ('1203', "There is no 1st Whatsapp Template linked to this Lead's assosciated Site"),
#                         ('1204', "There is no 2nd Whatsapp Template linked to this Lead's assosciated Site"),
#                         ('1205', "There is no 3rd Whatsapp Template linked to this Lead's assosciated Site"),
#                     )
#     type = models.CharField(choices=ERROR_TYPES, default='c', max_length=5)
#     attached_field = models.CharField(null=True, blank=True, max_length=50)
#     whatsapp_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="warnings", on_delete=models.SET_NULL, null=True, blank=True)
#     campaign_lead = models.ForeignKey("campaign_leads.Campaignlead", related_name="warnings", on_delete=models.SET_NULL, null=True, blank=True)
#     whatsapp_number = models.ForeignKey("core.WhatsappNumber", related_name="warnings", on_delete=models.SET_NULL, null=True, blank=True)
#     customer_number = models.TextField(blank=True, null=True)    
#     admin_action_required = models.BooleanField(default=False)
#     archived = models.BooleanField(default=False)
#     archived_time = models.DateTimeField(null=True, blank=True)

class WhatsappBusinessAccount(models.Model):
    whatsapp_business_account_id = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    @property
    def active_templates(self):
        return self.whatsapptemplate_set.exclude(archived=True).exclude(name__icontains="sample")
    @property
    def active_live_templates(self):
        return self.whatsapptemplate_set.filter(status="APPROVED").exclude(archived=True).exclude(name__icontains="sample")
    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # if self.site and self.active and self.whatsappnumber:
            # for whatsapp_number in self.whatsappnumber.all():
            #     whatsapp_number.company = self.site.company
            #     whatsapp_number.save()
            # self.whatsappnumber.company = self.site.company
            # self.whatsappnumber.save()
        # super(WhatsappBusinessAccount, self).save(force_insert, force_update, using, update_fields)

class PhoneNumber(PolymorphicModel):
    number = models.CharField(max_length=30, null=True, blank=True)
    alias = models.CharField(max_length=25, blank=True, null=True)
    # site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    archived = models.BooleanField(default=False)
    def __str__(self):
        if self.alias:
            return str(self.alias)
        elif self.number:
            return str(self.number)
        return f"PhoneNumber {str(self.pk)}"
    @property
    def is_whatsapp(self):
        return False
    @property
    def site(self):
        return self.whatsapp_business_account.site
class WhatsappNumber(PhoneNumber):
    whatsapp_business_phone_number_id = models.CharField(max_length=50, null=True, blank=True)
    quality_rating = models.CharField(max_length=50, null=True, blank=True)
    code_verification_status = models.CharField(max_length=50, null=True, blank=True)
    verified_name = models.CharField(max_length=50, null=True, blank=True)
    whatsapp_business_account = models.OneToOneField('core.WhatsappBusinessAccount', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def active_errors(self):        
        from core.models import AttachedError
        return AttachedError.objects.filter(whatsapp_number=self).filter(archived=False)
        
    def active_errors_for_customer_number(self, customer_number):        
        from core.models import AttachedError
        return AttachedError.objects.filter(whatsapp_number=self, customer_number=customer_number).filter(archived=False)
    
    def outstanding_whatsapp_messages(self, user):
        # Readdress this, I can't find a good way to get latest message for each conversation, then filter based on the last message being inbound...
        count = 0
        if self.whatsapp_business_account.site in user.profile.active_sites_allowed:
            for message in  WhatsAppMessage.objects.filter(whatsappnumber=self).order_by('customer_number', '-datetime').distinct('customer_number'):
                if message.inbound and not message.read:
                    count = count + 1
        return count

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.number = normalize_phone_number(self.number)
        super(WhatsappNumber, self).save(force_insert, force_update, using, update_fields)
    @property
    def is_whatsapp(self):
        return True
    pass

    # @property
    # def company_sites_with_same_whatsapp_business_details(self):
    #     try:
    #         from core.models import Site
    #         return Site.objects.filter(company=self.site.company, whatsapp_business_account_id=self.site.whatsapp_business_account_id).exclude(pk=self.site.pk)
    #     except Exception as e:
    #         return Site.objects.none()
    def get_latest_messages(self, after_datetime_timestamp=None, query={}):
        message_pk_list = []
        qs = WhatsAppMessage.objects.filter(whatsappnumber=self)
        if query.get('hide_auto'):
            qs = qs.filter(template=None)
        search_string = query.get('search_string')
        if search_string:
            qs = qs.filter(
                            Q(lead__last_name__icontains=search_string)|
                            Q(lead__first_name__icontains=search_string)|
                            Q(lead__email__icontains=search_string)|
                            Q(customer_number__icontains=search_string)|
                            Q(message__icontains=search_string)
                        )

        if after_datetime_timestamp:
            after_datetime = datetime.fromtimestamp(int(float(after_datetime_timestamp)))
            qs = qs.filter(datetime__lt=after_datetime)
        for dict in qs.order_by('customer_number','-datetime').distinct('customer_number').values('pk'):
            message_pk_list.append(dict.get('pk'))
        qs = WhatsAppMessage.objects.filter(pk__in=message_pk_list).order_by('-datetime')
        
        received = query.get('received')
        if received:
            qs = qs.filter(inbound=True, read=False)
            
        return qs[:10]

    def send_whatsapp_message(self, customer_number=None, lead=None, message="", user=None):  
        # try:
            logger.debug("site.send_whatsapp_message start") 
            if lead:
                customer_number = normalize_phone_number(lead.contact.customer_number)
                site_contact = lead.site_contact
            else:
                site_contact = SiteContact.objects.get(site=self.site, contact__customer_number=normalize_phone_number(customer_number))
            if self.whatsapp_business_phone_number_id and self.company.whatsapp_access_token and message:
                whatsapp = Whatsapp(self.company.whatsapp_access_token)
                if '+' in self.number:
                    customer_number = normalize_phone_number(f"{self.number}")
                response_body, attached_errors = whatsapp.send_free_text_message(customer_number, message, self)
                if not attached_errors:
                    reponse_messages = response_body.get('messages',[])
                    if reponse_messages:
                        for response_message in reponse_messages:
                            message, created = WhatsAppMessage.objects.get_or_create(
                                wamid=response_message.get('id'),
                                message=message,
                                datetime=datetime.now(),
                                lead=lead,
                                site_contact=site_contact,
                                site=self.site,
                                user=user,
                                customer_number=customer_number,
                                inbound=False,
                                whatsappnumber=self,
                                pending=not settings.DEBUG,
                            )
                        logger.debug("site.send_whatsapp_message success") 
                        return message
                
                logger.debug("site.send_whatsapp_message fail") 
                return None
            logger.debug(f"""site.send_whatsapp_message error:           
                (self.whatsapp_business_phone_number_id,{str(self.whatsapp_business_phone_number_id)})             
                (self.company.whatsapp_access_token,{str(self.company.whatsapp_access_token)}) 
                (message,{str(message)}) 
            """) 
        # except Exception as e:
        #     logger.debug("site.send_whatsapp_message error: "+str(e)) 
        #     return None


# class StripeSubscriptionSnapshot(models.Model):
#     created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     site = models.ForeignKey("core.Site", on_delete=models.SET_NULL, null=True, blank=True)
#     json_data = models.JSONField(null=True, blank=True)

class SubscriptionOverride(models.Model): #can give a site extra basic/pro subscription incase of stripe breaking or bad implementation
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    site = models.OneToOneField("core.Site", on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.OneToOneField("core.Subscription", on_delete=models.SET_NULL, null=True, blank=True)

class StripeCustomer(models.Model): #can give a site extra basic/pro subscription incase of stripe breaking or bad implementation
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    site = models.OneToOneField("core.Site", on_delete=models.SET_NULL, null=True, blank=True)
    customer_id = models.TextField(blank=True, null=True)
    json_data = models.JSONField(null=True, blank=True)
    subscription_id = models.TextField(blank=True, null=True)
    
class Site(models.Model):
    created = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    name = models.TextField(blank=True, null=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    # whatsapp_number = models.CharField(max_length=50, null=True, blank=True)
    # default_number = models.ForeignKey("core.WhatsappNumber", on_delete=models.SET_NULL, null=True, blank=True, related_name="site_default_number")
    whatsapp_access_token_old = models.TextField(blank=True, null=True)
    whatsapp_template_sending_enabled = models.BooleanField(default=False)
    active_campaign_leads_enabled = models.BooleanField(default=False)
    
    # whatsapp_business_account_id = models.TextField(null=True, blank=True)
    calendly_token = models.TextField(blank=True, null=True)
    calendly_user = models.TextField(blank=True, null=True)
    calendly_organization = models.TextField(blank=True, null=True)   
    # SUBSCRIPTION_CHOICES = (
    #                 ('free', 'Free'),
    #                 ('basic', 'Basic'),
    #                 ('pro', 'Pro'),
    #             )
    subscription = models.ForeignKey("core.Subscription", on_delete=models.SET_NULL, null=True, blank=True) #temp called new
    sign_up_subscription = models.ForeignKey("core.Subscription", related_name="sign_up_subscription_site", on_delete=models.SET_NULL, null=True, blank=True) #temp called new
    
    # subscription_old = models.CharField(max_length=5, default="free") #temp
    billing_email = models.TextField(blank=True, null=True, max_length=50)
    
    stripe_subscription_id = ArrayField(
        models.TextField(null=True, blank=True),
        null=True,
        blank=True,
        default=[]
    )
    # calendly_webhook_created = models.BooleanField(default=False)  
    guid = models.TextField(null=True, blank=True) 
    
    @property
    def get_stripe_invoices_by_customer_and_update_models(self):
        stripe_invoices = list_upcoming_invoices_by_customer(self.stripecustomer.customer_id)
        return stripe_invoices['data']
    
    
    def get_stripe_subscriptions_and_update_models(self):
        try:
            temp = self.stripecustomer.pk
        except Site.stripecustomer.RelatedObjectDoesNotExist as e:
            stripe_customer = get_or_create_customer(billing_email=self.billing_email)
            customer_id = stripe_customer['id']
            stripe_customer_object, created = StripeCustomer.objects.get_or_create(
                customer_id=customer_id
            )
            stripe_customer_object.site = self
            stripe_customer_object.save()
        
        stripe_subscriptions = list_subscriptions(self.stripecustomer.customer_id)
        sub_ids = []
        subscription_object = None
        subscription = None
        for subscription in stripe_subscriptions:
            sub_ids.append(subscription['id'])
            subscription_objects = Subscription.objects.filter(stripe_price_id=subscription['plan'].stripe_id)
            default_payment_method = subscription['default_payment_method']
            if default_payment_method:
                subscription['default_payment_method_data'] = retrieve_payment_method(subscription['default_payment_method'])
            else:
                subscription['default_payment_method_data'] = {}
            if subscription_objects.exists():
                subscription_object = subscription_objects.first()
                break
                
        subscription_override = SubscriptionOverride.objects.filter(
            created__lte = datetime.now(),
            end__gte = datetime.now(),
            site = self,
        ).first()
        if subscription_override:
            self.subscription = subscription_override.subscription
        elif subscription:
            if subscription.get('status') == 'active':
                self.subscription = subscription_object
        elif not stripe_subscriptions:
            self.subscription = Subscription.objects.filter(numerical__lt=1).last()
        
            
        if len(stripe_subscriptions) > 1 and not settings.DEMO and not settings.DEBUG:
            send_mail(
                subject=f'Winser Systems {os.getenv("SITE_URL")} - 500 error ',
                message=f"detected 2 subscriptions for a customer, this probably isn't right: #{str(self.pk)}, stripe sub ids: {str(sub_ids)}",
                from_email='jobiewinser@gmail.com',
                recipient_list=['jobiewinser@gmail.com'])
        self.stripe_subscription_id = sub_ids
        self.save()
        return stripe_subscriptions
    
    @property
    def stripe_payment_methods(self):
        return list_payment_methods(self.stripecustomer.customer_id)       
         
    
    # @property
    # def subscription(self):
    #     if not self.subscription and self.subscription_old:
    #         self.subscription = Subscription.objects.filter(name=self.subscription_old).first()
    #         self.save()
    #     return self.subscription
    
    @property
    def users(self):
        return User.objects.filter(profile__sites_allowed=self, is_active=True).order_by('profile__role')
    @property
    def inactive_users(self):
        return User.objects.filter(profile__sites_allowed=self, is_active=False).order_by('profile__role')
    # @property
    # def allowed_user_count(self):
    #     if self.subscription == 'free':
    #         return 5
    #     if self.subscription == 'basic':
    #         return 10
    #     if self.subscription == 'pro':
    #         return 999

        
    def check_if_allowed_to_get_analytics(self, start_date):
        if not self.subscription:
            self.save()
        if not self.subscription.analytics_seconds:
            return True
        if (datetime.now() - timedelta(seconds=self.subscription.analytics_seconds)) < start_date:
            return True
        return False
    def __str__(self):
        return f"({str(self.pk)}) {str(self.name)}"
        
    def outstanding_whatsapp_messages(self, user):
        # Readdress this, I can't find a good way to get latest message for each conversation, then filter based on the last message being inbound...
        count = 0
        if self in user.profile.active_sites_allowed:
            for whatsappnumber in self.return_phone_numbers():
                for message in WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber).order_by('customer_number', '-datetime').distinct('customer_number'):
                    if message.inbound and not message.read:
                        count = count + 1
        return count
    def get_live_whatsapp_phone_numbers(self):
        whatsapp = Whatsapp(self.company.whatsapp_access_token)  
        for whatsapp_business_account in self.whatsappbusinessaccount_set.all():
            try:
                phone_numbers = whatsapp.get_phone_numbers(whatsapp_business_account.whatsapp_business_account_id).get('data',[])  
                
                whatsapp_number_ids = []
                if phone_numbers:
                    for number in phone_numbers:
                        whatsappnumber, created = WhatsappNumber.objects.get_or_create(whatsapp_business_phone_number_id=number['id'])
                        if not whatsappnumber.company or whatsappnumber.company == self.company and created:
                            whatsappnumber.number = number['display_phone_number'].replace("+", "").replace(" ", "")
                            whatsappnumber.quality_rating = number['quality_rating']
                            whatsappnumber.code_verification_status = number['code_verification_status']
                            whatsappnumber.verified_name = number['verified_name']
                            whatsappnumber.company = self.company
                            # whatsappnumber.site = self
                            whatsappnumber.whatsapp_business_account = whatsapp_business_account                        
                            whatsappnumber.save()
                        whatsapp_number_ids.append(number['id'])
                    # if settings.DEBUG:
                    #     WhatsappNumber.objects.filter(whatsapp_business_account__site=self).exclude(whatsapp_business_phone_number_id__in=whatsapp_number_ids)
                    # else:
                    #     WhatsappNumber.objects.filter(whatsapp_business_account__site=self).exclude(whatsapp_business_phone_number_id__in=whatsapp_number_ids).update(archived=True)
            except Exception as e:
                print("get_live_whatsapp_phone_numbers ERROR: ", str(e))
        return self.return_phone_numbers()
    def return_phone_numbers(self):
        return WhatsappNumber.objects.filter(whatsapp_business_account__site=self, whatsapp_business_account__active=True).order_by('pk')
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.active and not self.created:
            self.created = datetime.now()
        # if not self.subscription and self.subscription_old:
        #     self.subscription = Subscription.objects.filter(name=self.subscription_old).first()
        super(Site, self).save(force_insert, force_update, using, update_fields)
        
        
    def complete_stripe_subscription_new_site(self, payment_method_id):
        try:
            temp = self.stripecustomer.pk
        except Site.stripecustomer.RelatedObjectDoesNotExist as e:
            stripe_customer = get_or_create_customer(billing_email=self.billing_email)
            customer_id = stripe_customer['id']
            stripe_customer_object, created = StripeCustomer.objects.get_or_create(
                customer_id=customer_id
            )
            stripe_customer_object.self = self
            stripe_customer_object.save()
            
        stripe_subscription = add_or_update_subscription(
            self.stripecustomer.customer_id, 
            payment_method_id, 
            self.sign_up_subscription.stripe_price_id,
            subscription_id=self.stripecustomer.subscription_id,
            proration_behavior='create_prorations',
        )
        self.get_stripe_subscriptions_and_update_models()

        


@receiver(models.signals.post_save, sender=Site)
def execute_after_save(sender, instance, created, *args, **kwargs):  
    if not instance.guid:
        instance.guid = str(uuid.uuid4())[:16]
        instance.save()
    # if not settings.DEBUG and instance.calendly_token and instance.guid and instance.company.calendly_enabled and not instance.calendly_webhook_created:
    #     try:
    #         instance.create_calendly_webhook()  
    #     except:
    #         pass
    #     instance.calendly_webhook_created = True 
    #     instance.save()
# Extending User Model Using a One-To-One Link
from django.core.cache import caches
class Company(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    company_logo_white = models.ImageField(default='default.png', upload_to='company_images')
    company_logo_black = models.ImageField(default='default.png', upload_to='company_images')
    company_logo_trans = models.ImageField(default='default.png', upload_to='company_images')
    # campaign_leads_enabled = models.BooleanField(default=False)#
    # calendly_enabled = models.BooleanField(default=False)#
    # free_taster_enabled = models.BooleanField(default=False)
    # whatsapp_enabled = models.BooleanField(default=False)
    # active_campaign_enabled = models.BooleanField(default=False)
    demo = models.BooleanField(default=False)
    whatsapp_access_token = models.TextField(blank=True, null=True)
    whatsapp_app_secret_key = models.TextField(blank=True, null=True)
    whatsapp_app_business_id = models.TextField(blank=True, null=True)
    active_campaign_url = models.TextField(null=True, blank=True)
    active_campaign_api_key = models.TextField(null=True, blank=True)
    contact_email = models.TextField(blank=True, null=True, max_length=50)
    is_active = models.BooleanField(default=True)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.get_company_cache()
        super(Company, self).save(force_insert, force_update, using, update_fields)
    def get_company_cache(self):
        # construct a unique name for the per-company cache
        company_cache_name = f"company_analytics_{str(self.pk)}"
        # check if the cache exists in django's settings
        if company_cache_name not in settings.CACHES.keys():
            # if not, create a new entry in settings and register it in django's cache registry
            settings.CACHES[company_cache_name] = {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': 'redis://127.0.0.1:6379/1',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                }
            }
            # caches.register(company_cache_name, settings.CACHES[company_cache_name])
        # return the per-user cache
        return caches[company_cache_name]
    def get_subscription_sites(self, numerical):
        return self.site_set.filter(subscription__numerical=numerical)
    def outstanding_whatsapp_messages(self, user):
        # Readdress this, I can't find a good way to get latest message for each conversation, then filter based on the last message being inbound...
        count = 0
        for site in self.active_sites:
            if site in user.profile.active_sites_allowed:
                for whatsappnumber in site.return_phone_numbers():
                    for message in  WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber).order_by('customer_number', '-datetime').distinct('customer_number'):
                        if message.inbound and not message.read:
                            count = count + 1
        return count
    @property
    def users(self):
        return User.objects.filter(profile__company=self, is_active=True).order_by('profile__site', 'profile__role')
    @property
    def free_sites(self):
        return self.site_set.filter(subscription__numerical=0)
    @property
    def has_pro_subscription_site(self):
        return self.site_set.filter(subscription__numerical=2).exists()
    @property
    def part_created_site(self):
        return self.site_set.filter(created=None).first()
    
    @property
    def get_campaign_leads_enabled(self):
        return self.campaign_leads_enabled
    @property
    def get_calendly_enabled(self):
        return self.calendly_enabled
    def __str__(self):
        return f"{str(self.name)}"   

    def get_and_generate_campaign_objects(self):
        # if self.active_campaign_url:
            # from active_campaign.api import ActiveCampaignApi
            # from active_campaign.models import ActiveCampaign
            
            # if not settings.DEBUG:
            # for campaign_dict in ActiveCampaignApi(self.active_campaign_api_key, self.active_campaign_url).get_lists(self.active_campaign_url).get('lists',[]):
            #     campaign, created = ActiveCampaign.objects.get_or_create(
            #         active_campaign_id = campaign_dict.pop('id'),
            #         name = campaign_dict.pop('name'),
            #         company = self,
            #     )
            #     campaign.json_data = campaign_dict
            #     campaign.save()
        from campaign_leads.models import Campaign
        return Campaign.objects.all()
    @property
    def active_sites(self):
        return self.site_set.filter(active=True)
 
# Extending User Model Using a One-To-One Link
ROLE_CHOICES = (
                ('a', 'Owner'),
                ('b', 'Manager'),
                ('c', 'Employee'),
            )
class Profile(models.Model):
    ROLE_CHOICES_PROFILE = ROLE_CHOICES
    role = models.CharField(choices=ROLE_CHOICES_PROFILE, default='c', max_length=1)
    theme = models.CharField(max_length=10, default="light")
    demo_account_theme_colour = models.CharField(null=True, blank=True, default="", max_length=16)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(default='default.png', upload_to='profile_images')
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    campaign_category = models.ForeignKey("campaign_leads.campaigncategory", on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    sites_allowed = models.ManyToManyField("core.Site", related_name="profile_sites_allowed", null=True, blank=True)
    calendly_event_page_url = models.TextField(blank=True, null=True)
    register_uuid = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=15, null=False, blank=False, default="96,248,61")
    @property
    def active_sites_allowed(self):
        return self.sites_allowed.filter(active=True).order_by('created')
    
    @property
    def campaigns_allowed(self):
        sites = self.sites_allowed.filter(active=True)
        from campaign_leads.models import Campaign
        return Campaign.objects.filter(site__in=sites)
    
    
    @property
    def active_campaigns_allowed(self):
        from active_campaign.models import ActiveCampaign
        sites = self.sites_allowed.filter(active=True)
        return ActiveCampaign.objects.filter(site__in=sites)
    
    @property
    def name(self):
        if self.user:
            if self.user.first_name or self.user.last_name:
                return f"{self.user.first_name} {self.user.last_name}"
            if self.user.email:
                return f"{self.user.email}"
            return "No name configured"
        return "This profile is disabled"
    @property
    def warnings(self):
        warnings = {}
        if not self.company:
            warnings["no_company_warning"] = "This profile has no company assigned to it"
        else:
            if not self.active_sites_allowed:
                warnings["no_company_warning"] = "This profile has no sites that they are allowed to access"
            if not self.site:
                warnings["no_site_warning"] = "This profile has no primary site assigned to it"
            if not self.avatar:
                warnings["no_avatar_warning"] = "This profile has no profile picture"
            if not self.calendly_event_page_url:
                warnings["no_calendly_event_page_url_warning"] = "This profile has no calendly event page (calendly won't work for this user)"
        return warnings
        
    def __str__(self):
        return str(self.name)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.campaign_category:
            if not self.campaign_category.site == self.site:
                self.campaign_category = None
                self
        if not self.site and self.pk:
            self.site = self.sites_allowed.all().first()
        super(Profile, self).save(force_insert, force_update, using, update_fields)
        if not self.site in self.active_sites_allowed and self.site:
            self.sites_allowed.add(self.site)   
        if self.company:
            for site in self.company.active_sites:
                try:
                    permissions, created = SiteProfilePermissions.objects.get_or_create(profile=self, site=site)
                except:
                    pass
            try:
                permissions, created = CompanyProfilePermissions.objects.get_or_create(profile=self, company=self.company)
            except:
                pass
        
class FreeTasterLink(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guid = models.TextField(blank=True, null=True)
    customer_name = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)

class FreeTasterLinkClick(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    link = models.ForeignKey(FreeTasterLink, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['-created']

class ErrorModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)

# class ChangeLog(models.Model):     
#     datetime = models.DateTimeField(null=True, blank=True)
#     version = models.FloatField(null=True, blank=True)
#     content = models.TextField(null=True, blank=True)

class CompanyProfilePermissions(models.Model):
    profile = models.ForeignKey("core.Profile", on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.CASCADE, null=True, blank=True)
    edit_user_permissions = models.BooleanField(default=False)
    edit_whatsapp_settings = models.BooleanField(default=False)
    permissions_count = models.IntegerField(default = 0)
    class Meta:
        ordering = ['-pk']   

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        role = self.profile.role
        self.permissions_count = 0
        for field in self._meta.fields:
            if type(field) == models.BooleanField:
                if getattr(self, field.attname, False):
                    self.permissions_count +=1
                elif role == 'a':
                    setattr(self, field.attname, True)
                    self.permissions_count +=1
        return super(CompanyProfilePermissions, self).save(force_insert, force_update, using, update_fields)

class SiteProfilePermissions(models.Model):
    profile = models.ForeignKey("core.Profile", on_delete=models.CASCADE, null=True, blank=True)
    site = models.ForeignKey("core.Site", on_delete=models.CASCADE, null=True, blank=True)
    view_site_configuration = models.BooleanField(default=False)
    edit_site_configuration = models.BooleanField(default=False)
    edit_site_calendly_configuration = models.BooleanField(default=False)
    
    toggle_active_campaign = models.BooleanField(default=False)
    toggle_whatsapp_sending = models.BooleanField(default=False)
    change_subscription = models.BooleanField(default=False)
    permissions_count = models.IntegerField(default = 0) 
    class Meta:
        ordering = ['-pk']   
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        role = self.profile.role
        self.permissions_count = 0
        for field in self._meta.fields:
            if type(field) == models.BooleanField:
                if role == 'a':
                    setattr(self, field.attname, True)
                    self.permissions_count +=1
                elif getattr(self, field.attname, False):
                    self.permissions_count +=1
        return super(SiteProfilePermissions, self).save(force_insert, force_update, using, update_fields)
    
    

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta:
        ordering = ['-created']
class StripeConfig(models.Model):
    webhook_id = models.TextField(null=True, blank=True)
    webhook_secret = models.TextField(null=True, blank=True)

    
