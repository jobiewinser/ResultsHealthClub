import json
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField


GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )

class WhatsAppWebhook(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    REQUEST_TYPE_CHOICES = (
                        ('a', 'POST'),
                        ('b', 'GET'),
                    )
    json_data = models.JSONField(null=True, blank=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    request_type = models.CharField(choices=REQUEST_TYPE_CHOICES, default='a', max_length=1)

class WhatsAppMessage(models.Model):
    wamid = models.TextField(null=True, blank=True)   
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhook", null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey("campaign_leads.Campaignlead", null=True, blank=True, on_delete=models.SET_NULL)
    inbound = models.BooleanField(default=True)
    errors = models.ManyToManyField("core.ErrorModel", null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    conversationid = models.TextField(null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)   
    system_user_number = models.CharField(max_length=50, null=True, blank=True)
    customer_number = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    template = models.ForeignKey("whatsapp.WhatsappTemplate", on_delete=models.SET_NULL, null=True, blank=True)
    # company = models.ManyToManyField("core.Company")
    class Meta:
        ordering = ['-datetime']
    
class WhatsAppMessageStatus(models.Model):
    whatsapp_message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, null=True, blank=True)    
    datetime = models.DateTimeField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    raw_webhook = models.ForeignKey("whatsapp.WhatsAppWebhook", null=True, blank=True, on_delete=models.SET_NULL)
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
    '{{1}}': ["First Name", "Jobie"],
    # '{{2}}': ["Last Name", "Winser"],
    '{{3}}': ["Company Name", "Winser Systems"],
    '{{4}}': ["Site Number", "+44 7872 000364"],
}
class WhatsappTemplate(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    send_order = models.IntegerField(choices=WHATSAPP_ORDER_CHOICES, null=True, blank=True, default=0)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    edited = models.DateTimeField(null=True, blank=True) 

    latest_reason = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)

    message_template_id = models.TextField(null=True, blank=True)

    name = models.TextField(null=True, blank=True)
    pending_name = models.TextField(null=True, blank=True)
    
    category = models.TextField(null=True, blank=True)
    pending_category = models.TextField(null=True, blank=True)

    language = models.TextField(null=True, blank=True)
    pending_language = models.TextField(null=True, blank=True)

    components = ArrayField(
        JSONField(default=dict),
        null=True,
        blank=True,
        default=[]
    )
    # parameters = ArrayField(
    #     models.TextField(null=True, blank=True),
    #     null=True,
    #     blank=True,
    #     default=[]
    # )
    
    pending_components = ArrayField(
        JSONField(default=dict),
        null=True,
        blank=True,
        default=[]
    )
    # pending_parameters = ArrayField(
    #     models.TextField(null=True, blank=True),
    #     null=True,
    #     blank=True,
    #     default=[]
    # )

    hidden = models.BooleanField(default=False)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    # objects = WhatsappTemplateManager()
    class Meta:
        ordering = ['pk']
    # def delete(self):
    #     self.save()
    # def get_edit_components(self):
    #     edit_components = {}
    #     if self.pending_components:
    #         for component in self.pending_components:
    #             component_type = component.get('type', None)
    #             component_text = component.get('text', "")
    #             component_format = component.get('format', "")
    #             if component_type:
    #                 edit_components[component_type] = ""

    #     elif self.components:
    #         for component in self.components
    #     return edit_components

    #     elif self.components:
    #         for component in self.components
    #     return edit_components
    @property
    def site_name(self):
        if self.site:
            return self.site.name
        return ''
    # def rendered_demo(self):
    #     return self.text.replace('{1}', 'Jobie')

    # def rendered(self, lead):
    #     return self.text.replace('{1}', str(lead.first_name))