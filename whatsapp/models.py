import json
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

from messaging.models import Message, MessageImage
from django.dispatch import receiver
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import os

GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )

class WhatsAppWebhookRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    REQUEST_TYPE_CHOICES = (
                        ('a', 'POST'),
                        ('b', 'GET'),
                    )
    json_data = models.JSONField(null=True, blank=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)


class WhatsappMessageImage(MessageImage): 
    media_id = models.TextField(blank=True, null=True)
    def create_thumbnail(self):            
        
        THUMBNAIL_SIZE = (99, 66)

        if self.image.name.endswith(".jpg"):
            PIL_TYPE = 'jpeg'
            FILE_EXTENSION = 'jpg'
            DJANGO_TYPE = 'image/jpeg'

        elif self.image.name.endswith(".png"):
            PIL_TYPE = 'png'
            FILE_EXTENSION = 'png'
            DJANGO_TYPE = 'image/png'

        image = Image.open(BytesIO(self.image.read()))
        
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        
        temp_handle = BytesIO()
        image.save(temp_handle, PIL_TYPE)
        temp_handle.seek(0)
        
        suf = SimpleUploadedFile(os.path.split(self.image.name)[-1],
                temp_handle.read(), content_type=DJANGO_TYPE)
                
        self.thumbnail = image
        self.save()


@receiver(models.signals.post_save, sender=WhatsappMessageImage)
def execute_after_save(sender, instance, created, *args, **kwargs):  
    if instance.image:
        instance.create_thumbnail()
    
class WhatsAppMessage(Message):
    wamid = models.TextField(null=True, blank=True)   
    type = models.TextField(null=True, blank=True)   
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhookRequest", null=True, blank=True, on_delete=models.SET_NULL)
    conversationid = models.TextField(null=True, blank=True)  
    whatsappnumber = models.ForeignKey("core.WhatsappNumber", null=True, blank=True, on_delete=models.SET_NULL)
    image = models.ManyToManyField("whatsapp.WhatsappMessageImage")
# class WhatsAppMessage(models.Model):
#     pass 
    
class WhatsAppMessageStatus(models.Model):
    whatsapp_message = models.ForeignKey(WhatsAppMessage, on_delete=models.SET_NULL, null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhookRequest", null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ['-datetime']

# class CustomWhatsappTemplateQuerySet(models.QuerySet):
#     def delete(self):
#         pass
# class WhatsappTemplateManager(models.Manager):
#     def get_queryset(self):
#         return CustomWhatsappTemplateQuerySet(self.model, using=self._db)


WHATSAPP_ORDER_CHOICES = (
    (0, 'Never'),
    (1, 'Send on Lead Creation'),
    (2, 'Send 24 Hrs after Lead Creation'),
    (3, 'Send 48 Hrs after Lead Creation')
)
template_variables = {
    '[[1]]': ["First Name", "Jobie"],    
}
class WhatsappTemplate(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited = models.DateTimeField(null=True, blank=True) 

    status = models.TextField(null=True, blank=True)

    message_template_id = models.TextField(null=True, blank=True)

    name = models.TextField(null=True, blank=True)
    pending_name = models.TextField(null=True, blank=True)
    
    category = models.TextField(null=True, blank=True)
    pending_category = models.TextField(null=True, blank=True)

    language = models.TextField(null=True, blank=True)
    pending_language = models.TextField(null=True, blank=True)
    
    last_approval = models.DateTimeField(null=True, blank=True)

    components = ArrayField(
        JSONField(default=dict),
        null=True,
        blank=True,
        default=[]
    )
    
    pending_components = ArrayField(
        JSONField(default=dict),
        null=True,
        blank=True,
        default=[]
    )

    hidden = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['pk']
    
    @property
    def active_errors(self):
        return self.errors.filter(archived=False)
    @property
    def company_sites_with_same_whatsapp_business_details(self):
        try:
            from core.models import Site
            return Site.objects.filter(company=self.site.company, whatsapp_business_account_id=self.site.whatsapp_business_account_id).exclude(pk=self.site.pk)
        except Exception as e:
            return Site.objects.none()
    @property
    def site_name(self):
        if self.site:
            return self.site.name
        return ''
    # def rendered_demo(self):
    #     return self.text.replace('{1}', 'Jobie')

    # def rendered(self, lead):
    #     return self.text.replace('{1}', str(lead.first_name))