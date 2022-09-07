from django.db import models
from django.db.models.deletion import SET_NULL
from django.contrib.auth.models import User


# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"