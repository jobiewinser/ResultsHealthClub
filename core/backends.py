from django.contrib.auth.backends import ModelBackend, UserModel
from django.db.models import Q
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            users = UserModel.objects.filter(Q(username__iexact=username.lower()) | Q(email__iexact=username.lower()))
            if not users:
                raise UserModel.DoesNotExist
            user = users.first()
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            temp = user.check_password(password)
            temp2 =  self.user_can_authenticate(user)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None