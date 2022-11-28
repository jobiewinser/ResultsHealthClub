from datetime import datetime
import uuid
from django.conf import settings
from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.http import HttpResponse
from calendly.api import Calendly

from campaign_leads.models import Campaign, Campaignlead, ManualCampaign
from twilio.models import TwilioMessage
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

class AttachedError(models.Model): 
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    ERROR_TYPES = (
                        ('0101', "You can only edit an active template once every 24 hours"),
                        ('0102', "The system can not send Whatsapp Templates without a template name"),
                        ('0103', "The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)"),
                        ('1104', "Message failed to send because more than 24 hours have passed since the customer last replied to this number. You can still send a template message at 24 hour intervals instead"),
                        ('1105', "Message failed to send because the Whatsapp account is not yet registered (contact Winser Systems)"),
                        ('1106', "The requested phone number has been deleted"),
                        ('1201', "Whatsapp Template not found Whatsapp's system"),
                        ('1202', "There is no Whatsapp Business linked to this Lead's assosciated Site"),
                        ('1203', "There is no 1st Whatsapp Template linked to this Lead's Campaign"),
                        ('1204', "There is no 2nd Whatsapp Template linked to this Lead's Campaign"),
                        ('1205', "There is no 3rd Whatsapp Template linked to this Lead's Campaign"),
                        ('1206', "There is no 4th Whatsapp Template linked to this Lead's Campaign"),
                        ('1207', "There is no 5th Whatsapp Template linked to this Lead's Campaign"),
                        ('1220', "This site has template messaging currently disabled, reenable it on the site configuration page"),
                    )
    type = models.CharField(choices=ERROR_TYPES, default='c', max_length=5)
    attached_field = models.CharField(null=True, blank=True, max_length=50)
    whatsapp_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    campaign_lead = models.ForeignKey("campaign_leads.Campaignlead", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey("core.Contact", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_number = models.ForeignKey("core.WhatsappNumber", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_message = models.ForeignKey("whatsapp.WhatsappMessage", related_name="attached_errors", on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey("core.Site", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    customer_number = models.TextField(blank=True, null=True)    
    admin_action_required = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    archived_time = models.DateTimeField(null=True, blank=True)
    
class Contact(models.Model):
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    customer_number = models.CharField(max_length=50, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    def send_template_whatsapp_message(self, whatsappnumber=None, template=None, communication_method = 'a'):
        print("Contact send_template_whatsapp_message", whatsappnumber, template, communication_method)
        from core.models import AttachedError
        if communication_method == 'a' and whatsappnumber:
            print("ContactDEBUG1")
            if template:    
                print("ContactDEBUG2")            
                AttachedError.objects.filter(
                    type = type,
                    contact = self,
                    archived = False,
                ).update(archived = True)
                if template.whatsapp_business_account.whatsapp_business_account_id: 
                    print("ContactDEBUG3")                   
                    AttachedError.objects.filter(
                        type = '1202',
                        contact = self,
                        archived = False,
                    ).update(archived = True)
                    if template.whatsapp_business_account.site.whatsapp_template_sending_enabled:
                        print("ContactDEBUG4")
                        AttachedError.objects.filter(
                            type = '1220',
                            contact = self,
                            archived = False,
                        ).update(archived = True)
                        if template.message_template_id:
                            print("ContactDEBUG5")
                            AttachedError.objects.filter(
                                type = '1201',
                                contact = self,
                                archived = False,
                            ).update(archived = True)
                            whatsapp = Whatsapp(self.site.whatsapp_access_token)
                            template_live = whatsapp.get_template(template.whatsapp_business_account.whatsapp_business_account_id, template.message_template_id)
                            template.name = template_live['name']
                            template.category = template_live['category']
                            template.language = template_live['language']
                            template.save()
                            components =   [] 
                            whole_text = ""
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
                                whole_text = f"""
                                    {whole_text} 
                                    {text}
                                """
                                if params:
                                    components.append(
                                        {
                                            "type": component_type,
                                            "parameters": params
                                        }
                                    )
                        else:
                            print("ContactDEBUG6")
                            print("errorhere selected template not found on Whatsapp's system")
                            attached_error, created = AttachedError.objects.get_or_create(
                                type = '1201',
                                attached_field = "contact",
                                contact = self,
                            )
                            if not created:
                                attached_error.created = datetime.now()
                                attached_error.save()
                            return HttpResponse("Messaging Error: Couldn't find the specified template", status=400)
                    else:
                        print("ContactDEBUG7")
                        print("errorhere template messaging disabled")
                        attached_error, created = AttachedError.objects.get_or_create(
                            type = '1220',
                            attached_field = "contact",
                            contact = self,
                        )
                        if not created:
                            attached_error.created = datetime.now()
                            attached_error.save()
                        return HttpResponse("Messaging Error: Template Messaging disabled for this site", status=400)
                else:
                    print("ContactDEBUG8")
                    print("errorhere no Whatsapp Business Account Linked")
                    attached_error, created = AttachedError.objects.get_or_create(
                        type = '1202',
                        attached_field = "contact",
                        contact = self,
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
                customer_number = self.customer_number
                response = whatsapp.send_template_message(self.customer_number, whatsappnumber, template, language, components)
                reponse_messages = response.get('messages',[])
                if reponse_messages:
                    print("ContactDEBUG9")
                    for response_message in reponse_messages:
                        whatsapp_message, created = WhatsAppMessage.objects.get_or_create(
                            wamid=response_message.get('id'),
                            datetime=datetime.now(),
                            contact=self,
                            message=whole_text,
                            site=site,
                            whatsappnumber=whatsappnumber,
                            customer_number=customer_number,
                            template=template,
                            inbound=False,
                        )
                        if created:                        
                            channel_layer = get_channel_layer()                            
                            message_context = {
                                "message": whatsapp_message,
                                "site": site,
                                "whatsappnumber": whatsappnumber,
                            }
                            rendered_message_list_row = loader.render_to_string('messaging/htmx/message_list_row.html', message_context)
                            rendered_message_chat_row = loader.render_to_string('messaging/htmx/message_chat_row.html', message_context)
                            rendered_html = f"""

                            <span id='latest_message_row_{customer_number}' hx-swap-oob='delete'></span>
                            <span id='messageCollapse_{whatsappnumber.pk}' hx-swap-oob='afterbegin'>{rendered_message_list_row}</span>

                            <span id='messageWindowInnerBody_{customer_number}' hx-swap-oob='beforeend'>{rendered_message_chat_row}</span>
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
                    logger.debug("site.send_template_whatsapp_message success") 
                    return HttpResponse("Message Sent", status=200)
        # return HttpResponse("No Communication method specified", status=500)

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
    @property
    def active_templates(self):
        return self.whatsapptemplate_set.exclude(archived=True).exclude(name__icontains="sample")
    @property
    def active_live_templates(self):
        return self.whatsapptemplate_set.filter(status="APPROVED").exclude(archived=True).exclude(name__icontains="sample")

class PhoneNumber(PolymorphicModel):
    number = models.CharField(max_length=30, null=True, blank=True)
    alias = models.TextField(blank=True, null=True)
    # site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    archived = models.BooleanField(default=False)
    
    def __str__(self):
        if self.alias:
            return self.alias
        return self.number
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
        if self.whatsapp_business_account.site in user.profile.sites_allowed.all():
            for message in  WhatsAppMessage.objects.filter(whatsappnumber=self).order_by('customer_number', '-datetime').distinct('customer_number'):
                if message.inbound:
                    count = count + 1
        return count

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
            qs = qs.filter(inbound=True)
        return qs[:10]

    def send_whatsapp_message(self, customer_number=None, lead=None, message="", user=None):  
        try:
            logger.debug("site.send_whatsapp_message start") 
            if lead:
                customer_number = lead.whatsapp_number
            if self.whatsapp_business_phone_number_id and self.site.whatsapp_access_token and message:
                whatsapp = Whatsapp(self.site.whatsapp_access_token)
                if '+' in self.number:
                    customer_number = f"{self.number.split('+')[-1]}"
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
                                site=self.site,
                                user=user,
                                customer_number=customer_number,
                                inbound=False,
                                whatsappnumber=self,
                                pending=True,
                            )
                        logger.debug("site.send_whatsapp_message success") 
                        return message
                
                logger.debug("site.send_whatsapp_message fail") 
                return None
            logger.debug(f"""site.send_whatsapp_message error:           
                (self.whatsapp_business_phone_number_id,{str(self.whatsapp_business_phone_number_id)})             
                (self.site.whatsapp_access_token,{str(self.site.whatsapp_access_token)}) 
                (message,{str(message)}) 
            """) 
        except Exception as e:
            logger.debug("site.send_whatsapp_message error: "+str(e)) 
            return None

class Site(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    name = models.TextField(blank=True, null=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    # whatsapp_number = models.CharField(max_length=50, null=True, blank=True)
    # default_number = models.ForeignKey("core.WhatsappNumber", on_delete=models.SET_NULL, null=True, blank=True, related_name="site_default_number")
    whatsapp_access_token = models.TextField(blank=True, null=True)
    whatsapp_app_secret_key = models.TextField(blank=True, null=True)
    whatsapp_template_sending_enabled = models.BooleanField(default=True)
    active_campaign_leads_enabled = models.BooleanField(default=True)
    
    # whatsapp_business_account_id = models.TextField(null=True, blank=True)
    calendly_token = models.TextField(blank=True, null=True)
    calendly_user = models.TextField(blank=True, null=True)
    calendly_organization = models.TextField(blank=True, null=True)   
    # calendly_webhook_created = models.BooleanField(default=False)  
    guid = models.TextField(null=True, blank=True) 
    def __str__(self):
        return f"({self.pk}) {self.name}"
        
    def outstanding_whatsapp_messages(self, user):
        # Readdress this, I can't find a good way to get latest message for each conversation, then filter based on the last message being inbound...
        count = 0
        if self in user.profile.sites_allowed.all():
            for whatsappnumber in self.return_phone_numbers():
                for message in WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber).order_by('customer_number', '-datetime').distinct('customer_number'):
                    if message.inbound:
                        count = count + 1
        return count
    def get_live_whatsapp_phone_numbers(self):
        whatsapp = Whatsapp(self.whatsapp_access_token)  
        for whatsapp_business_account in self.whatsappbusinessaccount_set.all():
            try:
                phone_numbers = whatsapp.get_phone_numbers(whatsapp_business_account.whatsapp_business_account_id).get('data',[])  
                print("get_live_whatsapp_phone_numbers phone_numbers", str(phone_numbers))
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
        return WhatsappNumber.objects.filter(whatsapp_business_account__site=self, archived=False).order_by('pk')
    # def create_calendly_webhook(self):
    #     calendly = Calendly(self.calendly_token)
    #     if self.calendly_user:
    #         calendly.create_webhook_subscription(self.guid, user = self.calendly_user)
    #     elif self.calendly_organization:
    #         calendly.create_webhook_subscription(self.guid, organization = self.calendly_organization)

    def generate_lead(self, first_name, email, phone_number, lead_generation_app='a', request=None):
        if lead_generation_app == 'b' and not self.company.active_campaign_enabled:
            return HttpResponse(f"Active Campaign is not enabled for {self.company.company_name}", status=500)
        if lead_generation_app == 'a':
            manually_created_campaign, created = ManualCampaign.objects.get_or_create(site=self, name=f"Manually Created")
            lead = Campaignlead.objects.create(
                first_name=first_name,
                email=email,
                whatsapp_number=phone_number,
                campaign=manually_created_campaign
            )
            return lead


    # def get_leads_created_in_month_and_year(self, date):
    #     return Campaignlead.objects.filter(campaign__site=self, created__month=date.month, created__year=date.year)

    # def get_leads_created_between_dates(self, start_date, end_date):
    #     return Campaignlead.objects.filter(campaign__site=self, created__gte=start_date, created__lte=end_date)

    # def get_(self, date):
    #     return Campaignlead.objects.filter(campaign__site=self, created__month=date.month, created__year=date.year)
 

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
class Company(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    company_name = models.TextField(null=True, blank=True)
    company_logo_white = models.ImageField(default='default.png', upload_to='company_images')
    company_logo_black = models.ImageField(default='default.png', upload_to='company_images')
    company_logo_trans = models.ImageField(default='default.png', upload_to='company_images')
    campaign_leads_enabled = models.BooleanField(default=False)#
    calendly_enabled = models.BooleanField(default=False)#
    free_taster_enabled = models.BooleanField(default=False)
    active_campaign_enabled = models.BooleanField(default=False)
    active_campaign_url = models.TextField(null=True, blank=True)
    active_campaign_api_key = models.TextField(null=True, blank=True)
    
    def outstanding_whatsapp_messages(self, user):
        # Readdress this, I can't find a good way to get latest message for each conversation, then filter based on the last message being inbound...
        count = 0
        for site in self.site_set.all():
            if site in user.profile.sites_allowed.all():
                for whatsappnumber in site.return_phone_numbers():
                    for message in  WhatsAppMessage.objects.filter(whatsappnumber=whatsappnumber).order_by('customer_number', '-datetime').distinct('customer_number'):
                        if message.inbound:
                            count = count + 1
        return count
    @property
    def users(self):
        return User.objects.filter(profile__company=self).order_by('profile__site', 'profile__role')
    @property
    def get_campaign_leads_enabled(self):
        return self.campaign_leads_enabled
    @property
    def get_calendly_enabled(self):
        return self.calendly_enabled
    def __str__(self):
        return f"{self.company_name}"   

    def get_and_generate_campaign_objects(self):
        if self.active_campaign_enabled and self.active_campaign_url:
            from active_campaign.api import ActiveCampaignApi
            from active_campaign.models import ActiveCampaign
            
            # if not settings.DEBUG:
            # for campaign_dict in ActiveCampaignApi(self.active_campaign_api_key, self.active_campaign_url).get_lists(self.active_campaign_url).get('lists',[]):
            #     campaign, created = ActiveCampaign.objects.get_or_create(
            #         active_campaign_id = campaign_dict.pop('id'),
            #         name = campaign_dict.pop('name'),
            #         company = self,
            #     )
            #     campaign.json_data = campaign_dict
            #     campaign.save()
        return Campaign.objects.all()
 
ROLE_CHOICES = (
                    ('a', 'Owner'),
                    ('b', 'Manager'),
                    ('c', 'Employee'),
                )
# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    role = models.CharField(choices=ROLE_CHOICES, default='c', max_length=1)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(default='default.png', upload_to='profile_images')
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    sites_allowed = models.ManyToManyField("core.Site", related_name="profile_sites_allowed", null=True, blank=True)
    calendly_event_page_url = models.TextField(blank=True, null=True)
    @property
    def name(self):
        if self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.first_name
    @property
    def warnings(self):
        warnings = {}
        if not self.company:
            warnings["no_company_warning"] = "This profile has no company assigned to it"
        else:
            if not self.sites_allowed.all():
                warnings["no_company_warning"] = "This profile has no sites that they are allowed to access"
            if not self.site:
                warnings["no_site_warning"] = "This profile has no main site assigned to it"
            if not self.avatar:
                warnings["no_avatar_warning"] = "This profile has no profile picture"
            if not self.calendly_event_page_url:
                warnings["no_calendly_event_page_url_warning"] = "This profile has no calendly event page (calendly won't work for this user)"
        return warnings
        
    def __str__(self):
        try:
            if self.user.first_name or self.user.last_name:
                return f"{self.user.first_name} {self.user.last_name}"
        except:
            pass
        return str(self.pk)
    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}"
@receiver(models.signals.post_save, sender=Profile)
def execute_after_save(sender, instance, created, *args, **kwargs):  
    if not instance.site in instance.sites_allowed.all():
        instance.sites_allowed.add(instance.site)
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