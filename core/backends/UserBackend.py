

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class CustomerBackend(ModelBackend):
 
    def authenticate(self, request, **kwargs):
        username = kwargs.get('username','')
        email = kwargs['email'].get('email','')
        password = kwargs.get('password','')
        try:
            user = User.objects.get(Q(username__iexact=username)|Q(email__iexact=email))
            if user.user.check_password(password) is True:
                return user.user
        except User.DoesNotExist:
            pass