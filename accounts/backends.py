from django.contrib.auth.backends import ModelBackend
from accounts.models import User

class EmailBackend(ModelBackend):
    """
    Authentification par email au lieu du username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None