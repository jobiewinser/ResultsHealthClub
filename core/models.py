from datetime import datetime
from django.conf import settings
from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User

from campaign_leads.models import Call, Campaignlead, WhatsappTemplate
from twilio.models import TwilioMessage
from django.db.models import Q, Count
from whatsapp.api import Whatsapp

from whatsapp.models import WhatsAppMessage

class Site(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    name = models.TextField(blank=True, null=True)
    company = models.ManyToManyField("core.Company")
    whatsapp_number = models.CharField(max_length=50, null=True, blank=True)
    whatsapp_business_phone_number_id = models.CharField(max_length=50, null=True, blank=True)
    whatsapp_access_token = models.TextField(blank=True, null=True)
    @property
    def get_company(self):
        if self.company.all():
            return self.company.all()[0]
        fake_company = Company
        return fake_company

    def send_whatsapp_message(self, customer_number=None, lead=None, whatsapp_template_send_order=None, message="", user=None, template_used=None):  
        if lead:
            customer_number = lead.whatsapp_number
        if settings.ENABLE_WHATSAPP_MESSAGING and self.whatsapp_business_phone_number_id and self.whatsapp_access_token and message:
            whatsapp = Whatsapp()
            if '+' in self.whatsapp_number:
                customer_number = f"{self.whatsapp_number.split('+')[-1]}"
            response = whatsapp.send_message(customer_number, message, self.whatsapp_business_phone_number_id, self.whatsapp_access_token)
            reponse_messages = response.get('messages',[])
            if reponse_messages:
                for response_message in reponse_messages:
                    WhatsAppMessage.objects.get_or_create(
                        wamid=response_message.get('id'),
                        message=message,
                        lead=lead,
                        site=self,
                        user=user,
                        system_user_number=self.whatsapp_number,
                        customer_number=customer_number,
                        template=template_used,
                        inbound=False
                    )
                return True
            return False

    def get_fresh_messages(self):
        return WhatsAppMessage.objects.filter(site=self).order_by('datetime').order_by('customer_number').distinct('customer_number')

    def get_leads_created_in_month_and_year(self, date):
        return Campaignlead.objects.filter(active_campaign_list__site=self, created__month=date.month, created__year=date.year)

    def get_leads_created_between_dates(self, start_date, end_date):
        return Campaignlead.objects.filter(active_campaign_list__site=self, created__gte=start_date, created__lte=end_date)
 
# Extending User Model Using a One-To-One Link
class Company(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    company_name = models.TextField(null=True, blank=True)
    company_logo_white = models.ImageField(default='default.jpg', upload_to='company_images')
    company_logo_black = models.ImageField(default='default.jpg', upload_to='company_images')
    company_logo_trans = models.ImageField(default='default.jpg', upload_to='company_images')
    campaign_leads_enabled = models.BooleanField(default=False)#
    free_taster_enabled = models.BooleanField(default=False)#
    active_campaign_url = models.TextField(null=True, blank=True)
    @property
    def get_campaign_leads_enabled(self):
        return self.campaign_leads_enabled
    def __str__(self):
        return f"{self.company_name}"   

    def get_and_generate_active_campaign_list_objects(self):
        from active_campaign.api import ActiveCampaign
        from active_campaign.models import ActiveCampaignList
        for active_campaign_list_dict in ActiveCampaign().get_lists(self.active_campaign_url).get('lists',[]):
            active_campaign_list, created = ActiveCampaignList.objects.get_or_create(
                active_campaign_id = active_campaign_list_dict.pop('id'),
                name = active_campaign_list_dict.pop('name')
            )
            active_campaign_list.json_data = active_campaign_list_dict
            active_campaign_list.save()
        return ActiveCampaignList.objects.all()
 
# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ManyToManyField("core.Company")
    @property
    def name(self):
        if self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.first_name
    @property
    def get_company(self):
        if self.company.all():
            return self.company.all()[0]
        fake_company = Company
        return fake_company
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
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
    link = models.ForeignKey(FreeTasterLink, on_delete=models.CASCADE)
    class Meta:
        ordering = ['-created']

class ErrorModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)