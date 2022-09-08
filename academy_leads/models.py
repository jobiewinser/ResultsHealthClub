from django.db import models

# Create your models here.


COMMUNICATION_CHOICES = (
                    ('a', 'Phone'),
                    ('b', 'Whatsapp'),
                    ('c', 'Email'),
                    ('d', 'Text')
                )

BOOKING_CHOICES = (
                    ('a', 'In Person'),
                    ('b', 'Phone'),
                )

class AdCampaign(models.Model):
    name = models.TextField(null=True, blank=True)

class AcademyLead(models.Model):
    first_name = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    ad_campign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE)
    phone = models.TextField(null=True, blank=True)
    arrived = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    def next_whatsapp_communication(self):
        last_whatsapp_communication = self.communication_set.filter(type='b')

class Communication(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE)
    type = models.CharField(choices=COMMUNICATION_CHOICES, max_length=2, null=False, blank=False)
    automatic = models.BooleanField(default=False)
    class Meta:
        ordering = ['-date']

class Booking(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE)
    type = models.CharField(choices=BOOKING_CHOICES, max_length=2, null=False, blank=False)

class Note(models.Model):
    text = models.TextField(null=False, blank=False)
    lead = models.ForeignKey(AcademyLead, on_delete=models.CASCADE)
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE)