import base64
import json
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import bleach
from django.db.models import JSONField

from messaging.models import Message, MessageImage
from PIL import Image
from io import BytesIO
from core.utils import normalize_phone_number
from datetime import datetime
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
    meta_data = models.JSONField(default=dict)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)
    
from django.http import Http404

class WhatsappMessageImage(MessageImage): 
    media_id = models.TextField(blank=True, null=True)
    
    @property
    def image_base64(self):
        if self.image:
            base = str(settings.BASE_DIR)
            path = base+self.image.url
            try:
                with open(path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            except:
                raise Http404('No image found.')
            return image_data

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.image:
            self.thumbnail = None
        else:
            thumbnail_size = 100, 100
            data_img = BytesIO()
            tiny_img = Image.open(self.image)
            tiny_img.thumbnail(thumbnail_size)
            tiny_img.save(data_img, format="BMP")
            tiny_img.close()
            try:
                self.thumbnail = "data:image/jpg;base64,{}".format(
                    base64.b64encode(data_img.getvalue()).decode("utf-8")
                )
            except UnicodeDecodeError:
                self.blurred_image = None

        super(WhatsappMessageImage, self).save(force_insert, force_update, using, update_fields)
    
class WhatsAppMessage(Message):
    wamid = models.TextField(null=True, blank=True)   
    type = models.TextField(null=True, blank=True)   
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhookRequest", null=True, blank=True, on_delete=models.SET_NULL)
    conversationid = models.TextField(null=True, blank=True)  
    whatsappnumber = models.ForeignKey("core.WhatsappNumber", null=True, blank=True, on_delete=models.SET_NULL)
    image = models.ManyToManyField("whatsapp.WhatsappMessageImage", null=True, blank=True)
    send_order =  models.IntegerField(null=True, blank=True)
    @property
    def active_errors(self):        
        from core.models import AttachedError
        return AttachedError.objects.filter(whatsapp_message=self).filter(archived=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        unique = None
        if self.message:
            self.message = bleach.clean(self.message, settings.BLEACH_VALID_TAGS, settings.BLEACH_VALID_ATTRS, settings.BLEACH_VALID_STYLES)
        while not unique:
            qs = WhatsAppMessage.objects.filter(datetime=self.datetime)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs:
                self.datetime = self.datetime + datetime.timedelta(seconds=1)
            else:
                unique = True
        if self.customer_number:
            self.customer_number = normalize_phone_number(self.customer_number)
        super(WhatsAppMessage, self).save(force_insert, force_update, using, update_fields)
    
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
    '[[1]]': ["First Name", "Lead Name"],    
    '[[2]]': ["Campaign Alias", "Fitness Campaign"],    
}
class WhatsappTemplate(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited = models.DateTimeField(null=True, blank=True) 

    status = models.TextField(null=True, blank=True)

    message_template_id = models.TextField(null=True, blank=True)

    latest_reason = models.TextField(null=True, blank=True)

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
    # site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_business_account = models.ForeignKey('core.WhatsappBusinessAccount', on_delete=models.SET_NULL, null=True, blank=True)
    
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['pk']
    
    @property
    def active_errors(self):
        from core.models import AttachedError
        return AttachedError.objects.filter(whatsapp_template=self).filter(archived=False)
    # @property
    # def company_sites_with_same_whatsapp_business_details(self):
    #     try:
    #         from core.models import Site
    #         return Site.objects.filter(company=self.site.company, whatsapp_business_account_id=self.site.whatsapp_business_account_id).exclude(pk=self.site.pk)
    #     except Exception as e:
    #         return Site.objects.none()
    @property
    def site_name(self):
        if self.site:
            return self.site.name
        return ''

    def render_whatsapp_template_to_html(self, lead=None, site_contact=None, first_name=None):
        rendered_html = ""
        try:
            text = f"<b>{self.components[0]['text']}</b>"
            if '[[1]]' in text:
                if lead:                
                    text = text.replace('[[1]]',lead.first_name)
                elif site_contact:
                    text = text.replace('[[1]]',site_contact.first_name)
                elif first_name:
                    text = text.replace('[[1]]',first_name)
            if '[[2]]' in text:            
                text = text.replace('[[2]]',lead.campaign.name)
            rendered_html = rendered_html + text
        except:
            pass
        try:
            text = f"<br> <br> <p>{self.components[1]['text']}</p>"
            if '[[1]]' in text:
                if lead:                
                    text = text.replace('[[1]]',lead.first_name)
                elif site_contact:
                    text = text.replace('[[1]]',site_contact.first_name)
                elif first_name:
                    text = text.replace('[[1]]',first_name)
            if '[[2]]' in text:   
                text = text.replace('[[2]]',lead.campaign.name)
            rendered_html = rendered_html + text
        except:
            pass
        try:
            text = f"<small>{self.components[2]['text']}</small>"
            if '[[1]]' in text:
                if lead:                
                    text = text.replace('[[1]]',lead.first_name)
                elif site_contact:
                    text = text.replace('[[1]]',site_contact.first_name)
                elif first_name:
                    text = text.replace('[[1]]',first_name)
            if '[[2]]' in text:
                text = text.replace('[[2]]',lead.campaign.name)
            rendered_html = rendered_html + text
        except:
            pass        
        
        return rendered_html