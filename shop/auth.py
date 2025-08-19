# myapp/auth.py
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class MyOIDCBackend(OIDCAuthenticationBackend):
    def update_user(self, user, claims):
        """
        Populate the user model with claims from Google.
        """
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')
        user.save()
        return user
