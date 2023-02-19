from django.db import models
from django.contrib.auth.models import User
from polymorphic.models import PolymorphicModel
# Create your models here.
class Message(PolymorphicModel):
    contact = models.ForeignKey("core.Contact", null=True, blank=True, on_delete=models.SET_NULL)
    site_contact = models.ForeignKey("core.SiteContact", null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey("campaign_leads.Campaignlead", null=True, blank=True, on_delete=models.SET_NULL)
    inbound = models.BooleanField(default=True)
    read = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    customer_number = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    template = models.ForeignKey("whatsapp.WhatsappTemplate", on_delete=models.SET_NULL, null=True, blank=True)
    # company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['-datetime']
    # @property
    # def get_contact(self):     
    #     from core.models import Contact   
    #     if self.contact:
    #         return self.contact
    #     self.contact = Contact.objects.filter(customer_number=self.customer_number).last()
    #     self.save()
    #     return self.contact 
    @property
    def get_site_contact(self):     
        from core.models import SiteContact   
        if self.site_contact:
            return self.site_contact
        self.site_contact = SiteContact.objects.filter(contact__customer_number=self.customer_number).last()
        self.save()
        return self.site_contact    

class MessageImage(PolymorphicModel):  
    image = models.ImageField(upload_to="secure/message_images", null=True, blank=True)    
    thumbnail = models.TextField(null=True, blank=True)
