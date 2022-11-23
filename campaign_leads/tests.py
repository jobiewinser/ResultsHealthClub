from django.test import TestCase

from campaign_leads.models import *

class FullLeadRunThroughTestCase(TestCase):
    def setUp(self):
        Campaign.objects.create(
            name = "test_campaign_1"  
    webhook_created = models.BooleanField(default=False)
    webhook_id = models.TextField(null=True, blank=True)
    site = models.ForeignKey('core.Site', on_delete=models.SET_NULL, null=True, blank=True)
    company =     company = models.ForeignKey("core.Company", on_delete=models.SET_NULL, null=True, blank=True)
,
    first_send_template = None,
    second_send_template = None,
    third_send_template = None,
    whatsapp_business_account = models.ForeignKey('core.WhatsappBusinessAccount', on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=15, null=False, blank=False, default="96,248,61")

        Animal.objects.create(name="cat", sound="meow")

    def test_animals_can_speak(self):