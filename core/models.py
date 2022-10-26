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

class AttachedError(models.Model): 
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    ERROR_TYPES = (
                        ('1101', "You can only edit an active template once every 24 hours"),
                        ('1102', "The system can not send Whatsapp Templates without a template name"),
                        ('1103', "The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)"),
                        ('1201', "Whatsapp Template not found Whatsapp's system"),
                        ('1202', "There is no Whatsapp Business linked to this Lead's assosciated Site"),
                        ('1203', "There is no 1st Whatsapp Template linked to this Lead's assosciated Site"),
                        ('1204', "There is no 2nd Whatsapp Template linked to this Lead's assosciated Site"),
                        ('1205', "There is no 3rd Whatsapp Template linked to this Lead's assosciated Site"),
                    )
    type = models.CharField(choices=ERROR_TYPES, default='c', max_length=5)
    attached_field = models.CharField(null=True, blank=True, max_length=50)
    whatsapp_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    campaign_lead = models.ForeignKey("campaign_leads.Campaignlead", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_number = models.ForeignKey("core.WhatsappNumber", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey("core.Site", related_name="errors", on_delete=models.SET_NULL, null=True, blank=True)
    recipient_number = models.TextField(blank=True, null=True)    
    admin_action_required = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    archived_time = models.DateTimeField(null=True, blank=True)

# class AttachedWarning(models.Model): 
#     created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     ERROR_TYPES = (
#                         ('1101', "You can only edit an active template once every 24 hours"),
#                         ('1102', "The system can not send Whatsapp Templates without a template name"),
#                         ('1103', "The number of parameters submitted does not match the Whatsapp Template (contact Winser Systems)"),
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
#     recipient_number = models.TextField(blank=True, null=True)    
#     admin_action_required = models.BooleanField(default=False)
#     archived = models.BooleanField(default=False)
#     archived_time = models.DateTimeField(null=True, blank=True)

class PhoneNumber(PolymorphicModel):
    number = models.CharField(max_length=30, null=True, blank=True)
    alias = models.TextField(blank=True, null=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    archived = models.BooleanField(default=False)
    @property
    def is_whatsapp(self):
        return False
class WhatsappNumber(PhoneNumber):
    whatsapp_business_phone_number_id = models.CharField(max_length=50, null=True, blank=True)
    quality_rating = models.CharField(max_length=50, null=True, blank=True)
    code_verification_status = models.CharField(max_length=50, null=True, blank=True)
    verified_name = models.CharField(max_length=50, null=True, blank=True)
    @property
    def is_whatsapp(self):
        return True
    pass

    @property
    def company_sites_with_same_whatsapp_business_details(self):
        try:
            from core.models import Site
            return Site.objects.filter(company=self.site.company, whatsapp_business_account_id=self.site.whatsapp_business_account_id).exclude(pk=self.site.pk)
        except Exception as e:
            return Site.objects.none()

    @property
    def get_latest_messages(self):
        message_pk_list = []
        for dict in WhatsAppMessage.objects.filter(whatsappnumber=self).order_by('customer_number','-datetime').distinct('customer_number').values('pk'):
            message_pk_list.append(dict.get('pk'))
        return WhatsAppMessage.objects.filter(pk__in=message_pk_list).order_by('-datetime')

    # @property
    # def get_latest_messages(self):
    #     message_pk_list = []
    #     for dict in WhatsAppMessage.objects.filter(whatsappnumber=self).order_by('customer_number').distinct('customer_number').values('pk'):
    #         message_pk_list.append(dict.get('pk'))
    #     return WhatsAppMessage.objects.filter(pk__in=message_pk_list).order_by('-inbound', '-datetime')

    def send_whatsapp_message(self, customer_number=None, lead=None, message="", user=None, template_used=None):  
        try:
            logger.debug("site.send_whatsapp_message start") 
            if lead:
                customer_number = lead.whatsapp_number
            if settings.ENABLE_WHATSAPP_MESSAGING and self.whatsapp_business_phone_number_id and self.site.whatsapp_access_token and message:
                whatsapp = Whatsapp(self.site.whatsapp_access_token)
                if '+' in self.number:
                    customer_number = f"{self.number.split('+')[-1]}"
                response = whatsapp.send_free_text_message(customer_number, message, self)
                reponse_messages = response.get('messages',[])
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
                            template=template_used,
                            inbound=False,
                            whatsappnumber=self,
                        )
                    logger.debug("site.send_whatsapp_message success") 
                    return message
                
                logger.debug("site.send_whatsapp_message fail") 
                return None
            logger.debug(f"""site.send_whatsapp_message error: 
            
                (settings.ENABLE_WHATSAPP_MESSAGING,{str(settings.ENABLE_WHATSAPP_MESSAGING)})             
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
    default_number = models.ForeignKey("core.WhatsappNumber", on_delete=models.SET_NULL, null=True, blank=True, related_name="site_default_number")
    whatsapp_access_token = models.TextField(blank=True, null=True)
    whatsapp_business_account_id = models.TextField(null=True, blank=True)
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
        phone_numbers = whatsapp.get_phone_numbers(self.whatsapp_business_account_id)  
        whatsapp_number_ids = []
        for number in phone_numbers['data']:
            whatsappnumber, created = WhatsappNumber.objects.get_or_create(whatsapp_business_phone_number_id=number['id'])
            if not whatsappnumber.company or whatsappnumber.company == self.company and created:
                whatsappnumber.number = number['display_phone_number'].replace("+", "").replace(" ", "")
                whatsappnumber.quality_rating = number['quality_rating']
                whatsappnumber.code_verification_status = number['code_verification_status']
                whatsappnumber.verified_name = number['verified_name']
                whatsappnumber.company = self.company
                whatsappnumber.site = self
                whatsappnumber.save()
            whatsapp_number_ids.append(number['id'])
        if settings.DEBUG:
            WhatsappNumber.objects.filter(site=self).exclude(whatsapp_business_phone_number_id__in=whatsapp_number_ids)
        else:
            WhatsappNumber.objects.filter(site=self).exclude(whatsapp_business_phone_number_id__in=whatsapp_number_ids).update(archived=True)
        return self.return_phone_numbers()
    def return_phone_numbers(self):
        return WhatsappNumber.objects.filter(site=self, archived=False)
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
        
    def __str__(self):
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        else:
            return str(self.pk)
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}"
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