from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User
from shop.models import Customer

class CustomOIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        """Create a new User and matching Customer when logging in first time."""
        user = User.objects.create_user(
            username=claims.get("email"),
            email=claims.get("email"),
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
        )
        # Also create Customer linked to this User
        Customer.objects.create(user=user)
        return user

    def update_user(self, user, claims):
        """Keep user details in sync."""
        user.email = claims.get("email", user.email)
        user.first_name = claims.get("given_name", user.first_name)
        user.last_name = claims.get("family_name", user.last_name)
        user.save()
        return user
