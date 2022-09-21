from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User

from academy_leads.models import AcademyLead

class Site(models.Model):
    name = models.TextField(blank=True, null=True)
    whatsapp_business_phone_number_id = models.TextField(blank=True, null=True)

    def get_leads_created_in_month_and_year(self, date):
        return AcademyLead.objects.filter(active_campaign_list__site=self, created__month=date.month, created__year=date.year)

    def get_leads_created_between_dates(self, start_date, end_date):
        return AcademyLead.objects.filter(active_campaign_list__site=self, created__gte=start_date, created__lte=end_date)
 
# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_phone_number_id = models.TextField(blank=True, null=True)
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

        