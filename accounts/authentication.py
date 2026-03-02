import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions
from .models import Client

class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        try:
            # Expected format: "Bearer <token>"
            token = auth_header.split(' ')[1]
        except IndexError:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')

        # Supabase signs JWTs with a secret specified in the dashboard
        jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
        if not jwt_secret:
            # Fallback if the user hasn't set it yet, but strictly it's an error.
            # Usually during initial setup we just want to show what's wrong.
            raise exceptions.AuthenticationFailed('SUPABASE_JWT_SECRET not configured on backend.')

        try:
            # Verify and decode the JWT
            # Supabase tokens usually use HS256 and the secret is base64 encoded by default?
            # Actually, most users just pass the raw secret or depend on how they got it.
            # We assume the secret is the raw string from Supabase settings.
            payload = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=["HS256"],
                options={"verify_aud": True, "verify_sub": True}
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

        # Extract user data from the payload
        # Supabase stores the unique user UUID in the 'sub' claim
        supabase_id = payload.get('sub')
        email = payload.get('email')
        
        if not supabase_id:
            raise exceptions.AuthenticationFailed('Token payload missing "sub" claim.')

        # Metadata often contains names
        user_metadata = payload.get('user_metadata', {})
        first_name = user_metadata.get('full_name', '').split(' ')[0] if user_metadata.get('full_name') else ''
        last_name = ' '.join(user_metadata.get('full_name', '').split(' ')[1:]) if user_metadata.get('full_name') else ''

        # Get or create the Django User
        # We use the Supabase UUID as the username to ensure uniqueness across providers (Discord, Google, etc)
        user, created = User.objects.get_or_create(
            username=supabase_id,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            }
        )
        
        # If the user already existed, update their email if it changed in Supabase
        if not created and user.email != email:
            user.email = email
            user.save()

        # Ensure the Client profile exists
        if not hasattr(user, 'client'):
            Client.objects.create(
                user=user,
                role='customer' # Default role
            )

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
