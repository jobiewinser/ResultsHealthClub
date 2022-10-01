from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User

from campaign_leads.models import Campaignlead

class Site(models.Model):
    name = models.TextField(blank=True, null=True)
    whatsapp_business_phone_number_id = models.TextField(blank=True, null=True)
    whatsapp_business_phone_number = models.TextField(blank=True, null=True)
    company = models.ManyToManyField("core.Company")

    def get_leads_created_in_month_and_year(self, date):
        return Campaignlead.objects.filter(active_campaign_list__site=self, created__month=date.month, created__year=date.year)

    def get_leads_created_between_dates(self, start_date, end_date):
        return Campaignlead.objects.filter(active_campaign_list__site=self, created__gte=start_date, created__lte=end_date)
 
# Extending User Model Using a One-To-One Link
class Company(models.Model):
    company_name = models.TextField(null=True, blank=True)
    company_logo_white = models.ImageField(default='default.jpg', upload_to='company_images')
    company_logo_black = models.ImageField(default='default.jpg', upload_to='company_images')
    company_logo_trans = models.ImageField(default='default.jpg', upload_to='company_images')
    campaign_leads_enabled = models.BooleanField(default=False)#
    @property
    def get_campaign_leads_enabled(self):
        return self.campaign_leads_enabled
 
# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_phone_number_id = models.TextField(blank=True, null=True)
    company = models.ManyToManyField("core.Company")
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
    staff_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guid = models.TextField(blank=True, null=True)
    customer_name = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)

class FreeTasterLinkClick(models.Model):
    link = models.ForeignKey(FreeTasterLink, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created']

        