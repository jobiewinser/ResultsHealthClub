import uuid
from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User


GYM_CHOICES = (
                    ('a', 'Abingdon'),
                    ('b', 'Alton'),
                    ('c', 'Fleet')
                )


# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    gym = models.CharField(choices=GYM_CHOICES, max_length=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class FreeTasterLink(models.Model):
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE)
    guid = models.TextField(blank=True, null=True)
    customer_name = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    gym = models.CharField(choices=GYM_CHOICES, max_length=2, null=True, blank=True)

class FreeTasterLinkClick(models.Model):
    link = models.ForeignKey(FreeTasterLink, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created']

        