from datetime import datetime
from django.conf import settings
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse
from whatsapp.api import Whatsapp
from whatsapp.models import WhatsAppMessage, WhatsappTemplate
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
import logging
from django.db.models import Q
from django.template import loader
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.views import get_or_create_contact_for_lead
logger = logging.getLogger(__name__)

BOOKING_CHOICES = (
                    ('a', 'In Person'),
                    ('b', 'Phone'),
                )
booking_choices_dict = {}
for tuple in BOOKING_CHOICES:
    booking_choices_dict[tuple[0]] = tuple[1]

class Campaign(PolymorphicModel):
    name = models.TextField(null=True, blank=True)   
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_cost = models.FloatField(default=100)
    json_data = models.JSONField(default=dict)
    guid = models.TextField(null=True, blank=True)
    webhook_created = models.BooleanField(default=False)
    webhook_id = models.TextField(null=True, blank=True)
    webhook_enabled = models.BooleanField(default=True)
    
    campaign_category = models.ForeignKey("campaign_leads.campaigncategory", on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
    # first_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="first_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    # second_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="second_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    # third_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="third_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    # fourth_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="fourth_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    # fifth_send_template = models.ForeignKey("whatsapp.WhatsappTemplate", related_name="fifth_send_template_campaign", on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_business_account = models.ForeignKey('core.WhatsappBusinessAccount', on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=15, null=False, blank=False, default="96,248,61")
    
    def __str__(self):
        return self.name
    
    def get_active_leads_qs(self):
        return self.campaignlead_set.exclude(archived=True).exclude(sale__archived=False)
    def is_manual(self):
        return False
        
    @property
    def campaigntemplatelinks_with_templates(self):
        return self.campaigntemplatelink_set.exclude(template=None)
    @property
    def campaign_template_links_with_send_orders(self):
        campaign_template_links = []
        try:
            max_send_order = self.campaigntemplatelink_set.all().order_by('-send_order').first().send_order or 1
        except:
            max_send_order = 0

        for i in range(1, max_send_order+2):
            campaign_template_links.append(self.campaigntemplatelink_set.filter(send_order = i).first())
        return campaign_template_links
    @property
    def site_templates(self):
        from whatsapp.models import WhatsappTemplate
        return WhatsappTemplate.objects.filter(site=self.site)
    @property
    def warnings(self):
        warnings = {}
        if self.site:
            if self.site.subscription:
                if self.site.subscription.whatsapp_enabled:
                    if not self.campaigntemplatelink_set.filter(send_order=1):
                        warnings["first_send_template_missing"] = "This campaign doesn't have a 1st Auto-Send Template, it won't automatically send a message to the customer"
        return warnings
# class AdCampaign(models.Model):
#     name = models.TextField(null=True, blank=True)
class CampaignCategory(models.Model):
    name = models.TextField(null=True, blank=True)  
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
class CampaignTemplateLink(PolymorphicModel):
    send_order =  models.IntegerField(null=True, blank=True)
    template = models.ForeignKey("whatsapp.WhatsappTemplate", on_delete=models.CASCADE, null=True, blank=True)
    campaign = models.ForeignKey("campaign_leads.Campaign", on_delete=models.CASCADE, null=True, blank=True)
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
    
    def __str__(self):
        return f"Manually Created ({self.site.name})"


class Campaignlead(models.Model):
    contact = models.ForeignKey("core.Contact", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.TextField(null=True, blank=True, max_length=25)
    last_name = models.TextField(null=True, blank=True, max_length=25)
    email = models.TextField(null=True, blank=True, max_length=50)    
    whatsapp_number_old = models.TextField(null=True, blank=True)
    # country_code = models.TextField(null=True, blank=True)
    campaign = models.ForeignKey("campaign_leads.Campaign", on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    arrived = models.BooleanField(default=False)
    sold_old = models.BooleanField(default=False, null=True, blank=True)
    # marked_sold_old = models.DateTimeField(null=True, blank=True)
    # sold_by_old = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="campaignlead_sold_by", null=True, blank=True)
    disabled_automated_messaging = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    active_campaign_contact_id = models.TextField(null=True, blank=True)
    active_campaign_form_id = models.TextField(null=True, blank=True)
    possible_duplicate = models.BooleanField(default=False)
    last_dragged = models.DateTimeField(null=True, blank=True)
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product_cost = models.FloatField(null=True, blank=True)
    def __str__(self):
        if self.name:
            return str(self.name)
        return f"CampaignLead {str(self.pk)}"
    @property
    def site_contact(self):  
        if self.campaign.site:
            from core.models import SiteContact
            site_contact, created = SiteContact.objects.get_or_create(site=self.campaign.site, contact = self.contact)
            return site_contact
        return None
    @property
    def ordered_bookings(self):  
        return self.booking_set.all().order_by('-datetime')
    @property
    def whatsapp_number(self):  
        return self.contact.customer_number
    @property
    def active_sales_qs(self):
        return self.sale_set.exclude(archived=True)
    @property
    def get_product_cost(self):  
        if self.product_cost:
            return self.product_cost      
        if self.campaign:
            self.product_cost = self.campaign.product_cost
            self.save()
            return self.product_cost
        return 0
    @property
    def is_last_whatsapp_message_inbound(self):        
        message = WhatsAppMessage.objects.filter(customer_number=self.whatsapp_number, whatsappnumber__whatsapp_business_account__site=self.campaign.site).last()
        if message:
            return message.inbound
        return False
    @property
    def active_errors(self):        
        from core.models import AttachedError
        return AttachedError.objects.filter(Q(campaign_lead=self)|Q(customer_number=self.whatsapp_number, whatsapp_number__whatsapp_business_account__site=self.campaign.site)).filter(archived=False)
    @property
    def active_bookings(self):        
        return self.booking_set.exclude(archived=True)

    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def trigger_refresh_websocket(self, refresh_position=False):
        channel_layer = get_channel_layer()   
        if refresh_position:
            rendered_html = self.get_leads_html(new_position=Call.objects.filter(lead=self).count())
            async_to_sync(channel_layer.group_send)(
                f"lead_{self.campaign.site.company.pk}",
                {
                    'type': 'lead_update',
                    'data':{
                        'rendered_html':rendered_html,
                    }
                }
            )
        else:
            rendered_html = self.get_leads_html()
            async_to_sync(channel_layer.group_send)(
                f"lead_{self.campaign.site.company.pk}",
                {
                    'type': 'lead_update',
                    'data':{
                        'rendered_html':rendered_html,
                    }
                }
            )
    def get_leads_html(self, new_position=None):
        if self:
            if new_position == None:    
                rendered_html = f"<span hx-swap-oob='outerHTML:.lead-{self.pk}' hx-get='/refresh-lead-article/{self.pk}/' hx-swap='outerHTML' hx-indicator='#top-htmx-indicator' hx-trigger='load' ></span>"
                return rendered_html
            else:
                delete_htmx = f"<span hx-swap-oob='delete' id='lead-{self.pk}'></span>"
                campaign = self.campaign
                if self.campaign.campaign_category:
                    campaign_category_pk = self.campaign.campaign_category.pk
                else:
                    campaign_category_pk = 0
                site = self.campaign.site
                company = site.company
                rendered_html = f"<span hx-swap-oob='beforeend:.campaign_column_{campaign.pk}_calls_{new_position},.campaign_category_column_{campaign_category_pk}_calls_{new_position},.site_column_{site.pk}_calls_{new_position},.company_column_{company.pk}_calls_{new_position}'><a hx-get='/refresh-lead-article/{self.pk}/' hx-swap='outerHTML' hx-vals=' U+007B U+0022 flash U+0022 : true U+007D' hx-indicator='#top-htmx-indicator' hx-trigger='load' href='#'></a> </span>"
                from django.utils.safestring import mark_safe
                return mark_safe(f"{rendered_html} {delete_htmx}")

    def send_template_whatsapp_message(self, whatsappnumber=None, send_order=None, template=None, communication_method = 'a'):
        if self.disabled_automated_messaging and send_order:
            pass #not sure if anything needs to happen here yet. will probably indicate on the leads card that messaging is disabled
        else:
            print("Campaignlead send_template_whatsapp_message", whatsappnumber, send_order, template, communication_method)
            if not whatsappnumber:
                whatsappnumber = self.campaign.whatsapp_business_account.whatsappnumber
            from core.models import AttachedError, send_message_to_websocket
            customer_number = self.whatsapp_number
            if settings.DEMO:
                whatsapp_message, created = WhatsAppMessage.objects.get_or_create(
                    wamid="",
                    datetime=datetime.now(),
                    lead=self,
                    message=f"""
                    <b>Hi {self.first_name}</b>
                    <br>
                    <br>
                    <p>This is a demonstration of the whatsapp system! With the Pro subscription, you can add your own whatsapp accounts and automate sending templates here!</p>
                    <small>Thanks from Winser Systems!</small>
                    """,
                    site=self.campaign.site,
                    whatsappnumber=whatsappnumber,
                    customer_number=customer_number,
                    template=template,
                    inbound=False,
                )
                send_message_to_websocket(whatsappnumber, customer_number, whatsapp_message, self.campaign.site)
                self.trigger_refresh_websocket(refresh_position=False)
                return HttpResponse(status=200)
            if communication_method == 'a':
                print("CampaignleadDEBUG1")
                if send_order:
                    campaigntemplatelink = self.campaign.campaigntemplatelink_set.filter(send_order=send_order).first()
                    if campaigntemplatelink:
                        template = campaigntemplatelink.template
                    type = str(1202)
                else:
                    type = None
                
                if template:      
                    print("CampaignleadDEBUG2")
                    if type:          
                        AttachedError.objects.filter(
                            type = type,
                            campaign_lead = self,
                            archived = False,
                        ).update(archived = True)
                    if template.whatsapp_business_account.whatsapp_business_account_id:  
                        print("CampaignleadDEBUG3")                  
                        AttachedError.objects.filter(
                            type = '1202',
                            campaign_lead = self,
                            archived = False,
                        ).update(archived = True)
                        if template.whatsapp_business_account.site.whatsapp_template_sending_enabled:
                            print("CampaignleadDEBUG4")
                            AttachedError.objects.filter(
                                type = '1220',
                                campaign_lead = self,
                                archived = False,
                            ).update(archived = True)
                            if template.message_template_id:
                                print("CampaignleadDEBUG5")
                                AttachedError.objects.filter(
                                    type = '1201',
                                    campaign_lead = self,
                                    archived = False,
                                ).update(archived = True)
                                whatsapp = Whatsapp(self.campaign.company.whatsapp_access_token)
                                template_live = whatsapp.get_template(template.whatsapp_business_account.whatsapp_business_account_id, template.message_template_id)
                                print(template_live)
                                template.name = template_live['name']

                                template.category = template_live['category']
                                template.language = template_live['language']
                                template.save()

                                components =   [] 

                                whole_text = template.render_whatsapp_template_to_html(lead=self)
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
                                        if '[[2]]' in text:
                                            params.append(              
                                                {
                                                    "type": "text",
                                                    "text":  str(self.campaign.name)
                                                }
                                            )
                                            text = text.replace('[[2]]',self.campaign.name)
                                            counter = counter + 1
                                    if params:
                                        components.append(
                                            {
                                                "type": component_type,
                                                "parameters": params
                                            }
                                        )
                            else:
                                print("CampaignleadDEBUG6")
                                print("errorhere selected template not found on Whatsapp's system")
                                attached_error, created = AttachedError.objects.get_or_create(
                                    type = '1201',
                                    attached_field = "campaign_lead",
                                    campaign_lead = self,
                                    archived = False,
                                )
                                if not created:
                                    attached_error.created = datetime.now()
                                    attached_error.save()
                                return HttpResponse("Messaging Error: Couldn't find the specified template", status=400)
                        else:
                            print("CampaignleadDEBUG7")
                            print("errorhere template messaging disabled")
                            attached_error, created = AttachedError.objects.get_or_create(
                                type = '1220',
                                attached_field = "campaign_lead",
                                campaign_lead = self,
                                archived = False,
                            )
                            if not created:
                                attached_error.created = datetime.now()
                                attached_error.save()
                            return HttpResponse("Messaging Error: Template Messaging disabled for this site", status=400)
                    else:
                        print("CampaignleadDEBUG8")
                        print("errorhere no Whatsapp Business Account Linked")
                        attached_error, created = AttachedError.objects.get_or_create(
                            type = '1202',
                            attached_field = "campaign_lead",
                            campaign_lead = self,
                            archived = False,
                        )
                        if not created:
                            attached_error.created = datetime.now()
                            attached_error.save()
                        return HttpResponse("Messaging Error: No Whatsapp Business Account linked", status=400)
                    language = {
                        "policy":"deterministic",
                        "code":template.language
                    }
                    site = self.campaign.site
                    if not whatsappnumber and send_order:
                        whatsappnumber = self.campaign.whatsapp_business_account.whatsappnumber
                    if not settings.DEMO:
                        response = whatsapp.send_template_message(self.whatsapp_number, whatsappnumber, template, language, components)
                    else:
                        response = {} #TODO
                    print(str(response))
                    logger.debug(str(response))
                    
                    reponse_messages = response.get('messages',[])
                    error = response.get('error',[])
                    if reponse_messages:
                        AttachedError.objects.filter(
                            type__in = ['1107','1106'], 
                            attached_field = "campaign_lead",
                            campaign_lead = self,
                            archived = False,
                        ).update(archived = True)    
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
                                inbound=False,
                                send_order=send_order
                            )
                            if created:                 
                                send_message_to_websocket(whatsappnumber, customer_number, whatsapp_message, whatsappnumber.whatsapp_business_account )                           
                        logger.debug("site.send_template_whatsapp_message success") 
                        self.trigger_refresh_websocket(refresh_position=False)
                        return HttpResponse("Message Sent", status=200)
                        
                    elif error.get('code', None) == 33:
                        AttachedError.objects.create(
                            type = '1106',
                            attached_field = "customer_number",
                            whatsapp_number = whatsappnumber,
                            customer_number = customer_number,
                            admin_action_required = True,
                        )
                    elif error.get('code', None) == 100:   
                        attached_error, created = AttachedError.objects.get_or_create(
                            type = '1107',
                            attached_field = "campaign_lead",
                            campaign_lead = self,
                            archived = False,
                        )
                        self.trigger_refresh_websocket(refresh_position=False)
                        return HttpResponse("Message Not Sent", status=400)
                    else:     
                        self.trigger_refresh_websocket(refresh_position=False)
                        return HttpResponse("Message Failed", status=500)
                else:
                    print("CampaignleadDEBUG10")
                    if send_order == 1:
                        type = '1203'
                        attached_error, created = AttachedError.objects.get_or_create(
                            type = type,
                            attached_field = "campaign_lead",
                            campaign_lead = self,
                            archived = False,
                        )
                        if not created:
                            print("CampaignleadDEBUG11")
                            attached_error.created = datetime.now()
                            attached_error.save()
            return HttpResponse("Message Error", status=400)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.contact and self.campaign:
            contact = get_or_create_contact_for_lead(self, self.whatsapp_number_old)
            self.contact = contact
        try:
            if not self.product_cost:
                self.product_cost = self.campaign.product_cost
        except:
            pass
        super(Campaignlead, self).save(force_insert, force_update, using, update_fields)
        
        
@receiver(models.signals.post_save, sender=Campaignlead)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created and not instance.archived:
        try:
            instance.send_template_whatsapp_message(send_order=1)
        except:
            pass
        
class Call(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # error_json = models.JSONField(default=dict)
    archived = models.BooleanField(default=False)
    class Meta:
        ordering = ['-datetime']

class Sale(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    lead = models.ForeignKey(Campaignlead, on_delete=models.SET_NULL, null=True, blank=True)
    # type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    archived = models.BooleanField(default=False)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Sale, self).save(force_insert, force_update, using, update_fields)
    # class Meta:
    #     ordering = ['-datetime']

class Booking(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    lead = models.ForeignKey(Campaignlead, on_delete=models.SET_NULL, null=True, blank=True)
    # type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    calendly_event_uri = models.TextField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    # class Meta:
    #     ordering = ['-datetime']

class Note(models.Model):
    text = models.TextField(null=False, blank=False)
    lead = models.ForeignKey(Campaignlead, on_delete=models.SET_NULL, null=True, blank=True)
    call = models.ForeignKey('campaign_leads.Call', on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
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
