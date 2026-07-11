from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
    Allows authenticate(identifier=..., password=...)
    where identifier can be email or username.
    """
    def authenticate(self, request, email=None, username=None, identifier=None, password=None, **kwargs):
        User = get_user_model()
        lookup = identifier or email or username
        if lookup is None or password is None:
            return None
        try:
            lookup = lookup.strip()
            user = User.objects.get(Q(email__iexact=lookup) | Q(username__iexact=lookup))
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None