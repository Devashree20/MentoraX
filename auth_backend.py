from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

CustomUser = get_user_model()

class RollNoBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
            
        try:
            # Try to fetch by roll_no first (for students), then username
            user = CustomUser.objects.filter(
                Q(roll_no=username) | Q(username=username)
            ).first()
            
            if user and user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None
        return None
