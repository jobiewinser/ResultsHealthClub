from datetime import timedelta, datetime
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse
from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage, WhatsappTemplate
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
import logging
from django.db.models import Q, Count
from django.template import loader
from asgiref.sync import async_to_sync, sync_to_async
logger = logging.getLogger(__name__)

BOOKING_CHOICES = (
                    ('a', 'In Person'),
                    ('b', 'Phone'),
                )
booking_choices_dict = {}
for tuple in BOOKING_CHOICES:
    booking_choices_dict[tuple[0]] = tuple[1]

# class AdCampaign(models.Model):
#     name = models.TextField(null=True, blank=True)

class Campaign(PolymorphicModel):
    name = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_cost = models.FloatField(default=100)
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)
    webhook_created = models.BooleanField(default=False)
    webhook_id = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    first_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="first_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    second_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="second_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    third_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="third_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    def get_active_leads_qs(self):
        return self.campaignlead_set.filter(complete=False)
    def is_manual(self):
        return False
    @property
    def site_templates(self):
        return WhatsappTemplate.objects.filter(site=self.site)
    @property
    def warnings(self):
        warnings = {}
        if not self.first_send_template:
            warnings["first_send_template_missing"] = "This campaign doesn't have a 1st Auto-Send Template, it won't automatically send a message to the customer"
        return warnings
@receiver(models.signals.post_save, sender=Campaign)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        instance.guid = str(uuid.uuid4())[:16]
        instance.save()

class ManualCampaign(Campaign):
    pass
    @property
    def is_manual(self):
        return True


class Campaignlead(models.Model):
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    
    whatsapp_number = models.TextField(null=True, blank=True)
    # country_code = models.TextField(null=True, blank=True)
    campaign = models.ForeignKey("campaign_leads.Campaign", on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    arrived = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    active_campaign_contact_id = models.TextField(null=True, blank=True)
    active_campaign_form_id = models.TextField(null=True, blank=True)
    possible_duplicate = models.BooleanField(default=False)
    last_dragged = models.DateTimeField(null=True, blank=True)
    
    @property
    def active_errors(self):        
        from core.models import AttachedError
        return AttachedError.objects.filter(Q(campaign_lead=self)|Q(recipient_number=self.whatsapp_number, whatsapp_number__site=self.campaign.site)).filter(archived=False)

    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    @property
    def last_whatsapp(self):
        whatsapps = self.call_set.all()
        if whatsapps:
            return whatsapps.first()
        return None
    
    @property
    def time_until_next_whatsapp(self):
        last_whatsapp = self.last_whatsapp
        print(last_whatsapp)
        if last_whatsapp:
            return last_whatsapp.datetime.replace(hour=9).replace(minute=30).replace(second=0) + timedelta(days=1)
        return "Never"  

    def send_template_whatsapp_message(self, send_order, communication_method = 'a'):
        from core.models import AttachedError
        if communication_method == 'a':
            if send_order == 1:
                template = self.campaign.first_send_template
                type = '1203'
            elif send_order == 2:
                template = self.campaign.second_send_template
                type = '1204'
            elif send_order == 3:
                template = self.campaign.third_send_template
                type = '1205'
            if template:                
                AttachedError.objects.filter(
                    type = type,
                    campaign_lead = self,
                    archived = False,
                ).update(archived = True)
                if template.site.whatsapp_business_account_id:
                    AttachedError.objects.filter(
                        type = '1202',
                        campaign_lead = self,
                        archived = False,
                    ).update(archived = True)
                    if template.message_template_id:
                        AttachedError.objects.filter(
                            type = '1201',
                            campaign_lead = self,
                            archived = False,
                        ).update(archived = True)
                        whatsapp = Whatsapp(self.campaign.site.whatsapp_access_token)
                        template_live = whatsapp.get_template(template.site.whatsapp_business_account_id, template.message_template_id)
                        template.name = template_live['name']

                        template.category = template_live['category']
                        template.language = template_live['language']
                        # template.components = template_live['components']
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
                            # if '{{3}}' in text:
                            #     params.append(           
                            #         {
                            #             "type": "text",
                            #             "text":  self.campaign.company.company_name
                            #         }
                            #     )
                            # if '{{4}}' in text:
                            #     params.append(                   
                            #         {
                            #             "type": "text",
                            #             "text":  self.campaign.site.whatsapp_number
                            #         }
                            #     )
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
                        print("errorhere selected template not found on Whatsapp's system")
                        AttachedError.objects.create(
                            type = '1201',
                            attached_field = "campaign_lead",
                            campaign_lead = self,
                        )
                else:
                    print("errorhere no Whatsapp Business Account Linked")
                    AttachedError.objects.create(
                        type = '1202',
                        attached_field = "campaign_lead",
                        campaign_lead = self,
                    )
            else:
                if send_order == 1:
                    type = '1203'
                elif send_order == 2:
                    type = '1204'
                elif send_order == 3:
                    type = '1205'
                print("errorhere no suitable template found")
                AttachedError.objects.create(
                    type = type,
                    attached_field = "campaign_lead",
                    campaign_lead = self,
                )
            
            

            language = {
                "policy":"deterministic",
                "code":template.language
            }
            site = self.campaign.site
            whatsappnumber = site.default_number
            customer_number = self.whatsapp_number
            response = whatsapp.send_template_message(self.whatsapp_number, whatsappnumber, template, language, components)
            reponse_messages = response.get('messages',[])
            if reponse_messages:
                for response_message in reponse_messages:
                    whatsapp_message, created = WhatsAppMessage.objects.get_or_create(
                        wamid=response_message.get('id'),
                        datetime=datetime.now(),
                        lead=self,
                        message=whole_text,
                        site=site,
                        whatsappnumber=whatsappnumber,
                        customer_number=customer_number,
                        template=template,
                        inbound=False
                    )
                    if created:                        
                        from channels.layers import get_channel_layer
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
                logger.debug("site.send_template_whatsapp_message success") 
                return True
        return HttpResponse("No Communication method specified", status=500)

@receiver(models.signals.post_save, sender=Campaignlead)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created and not instance.complete:
        try:
            instance.send_template_whatsapp_message(1, communication_method='a')
        except:
            pass
        
class Call(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    error_json = models.JSONField(default=dict)
    class Meta:
        ordering = ['-datetime']

class Booking(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE)
    type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    calendly_event_uri = models.TextField(null=True, blank=True)
    class Meta:
        ordering = ['-datetime']

class Note(models.Model):
    text = models.TextField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE, null=True, blank=True)
    call = models.ForeignKey('campaign_leads.Call', on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    #This referes to the date it was created unless it's attached to a call/booking, then it's set to the related datetime
    datetime = models.DateTimeField(null=True, blank=True) 
    class Meta:
        ordering = ['-datetime']

# try:
#     template, created = WhatsappTemplate.objects.get_or_create(pk=1)
#     template.name = "Immediate Lead Followup"
#     template.save()

#     template, created = WhatsappTemplate.objects.get_or_create(pk=2)
#     template.name = "Second Lead Followup"
#     template.save()

#     template, created = WhatsappTemplate.objects.get_or_create(pk=3)
#     template.name = "Third Lead Followup"
#     template.save()
# except:
#     pass