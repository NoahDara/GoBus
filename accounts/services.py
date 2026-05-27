# accounts/services.py - Google OAuth Service

from django.contrib.auth.models import User
from django.contrib.auth import login
from google.auth.transport import requests
from google.oauth2 import id_token
import logging

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """
    Service for handling Google OAuth authentication.
    Handles JWT token verification and user creation/login.
    """
    
    def __init__(self, client_id=None):
        """
        Initialize service with Google Client ID.
        
        Args:
            client_id: Google OAuth 2.0 Client ID from Google Console
        """
        from django.conf import settings
        self.client_id = client_id or getattr(
            settings, 'GOOGLE_OAUTH_CLIENT_ID', None
        )
        
        if not self.client_id:
            raise ValueError('Google Client ID not configured')
    
    def verify_token(self, token):
        """
        Verify Google JWT token and extract user info.
        
        Args:
            token: JWT token from Google OAuth
            
        Returns:
            dict: User info {email, name, picture, sub}
            None: If token is invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )
            
            # Verify token hasn't been revoked
            if idinfo.get('aud') != self.client_id:
                logger.warning(f"Token audience mismatch: {idinfo.get('aud')}")
                return None
            
            return idinfo
        
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            return None
    
    def authenticate_user(self, token):
        """
        Authenticate or create user from Google token.
        
        Args:
            token: JWT token from Google OAuth
            
        Returns:
            User: Django User object if successful, None otherwise
        """
        # Verify token
        idinfo = self.verify_token(token)
        if not idinfo:
            return None
        
        email = idinfo.get('email')
        name = idinfo.get('name', '').strip()
        picture_url = idinfo.get('picture')
        google_id = idinfo.get('sub')
        
        if not email:
            logger.warning("Google token missing email")
            return None
        
        try:
            # Try to get existing user
            user = User.objects.get(email=email)
            logger.info(f"Existing user logged in via Google: {email}")
        
        except User.DoesNotExist:
            # Create new user
            try:
                # Parse name
                name_parts = name.split(' ', 1)
                first_name = name_parts[0] if name_parts else 'User'
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Generate unique username from email
                base_username = email.split('@')[0].lower()
                username = base_username
                counter = 1
                
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=self._generate_random_password()  # Random password
                )
                
                logger.info(f"New user created via Google: {email} (username: {username})")
                
            except Exception as e:
                logger.error(f"Error creating user from Google: {str(e)}")
                return None
        
        return user
    
    def _generate_random_password(self, length=32):
        """
        Generate a random secure password.
        Users who sign up via Google won't need this password.
        
        Args:
            length: Password length
            
        Returns:
            str: Random password
        """
        from django.contrib.auth.models import make_password
        from secrets import token_urlsafe
        
        return token_urlsafe(length)


class GoogleAuthHelper:
    """
    Helper class for Google OAuth integration.
    Simplifies token verification and user authentication.
    """
    
    @staticmethod
    def get_service(client_id=None):
        """
        Get Google Auth Service instance.
        
        Args:
            client_id: Google OAuth 2.0 Client ID
            
        Returns:
            GoogleAuthService: Service instance
        """
        return GoogleAuthService(client_id)
    
    @staticmethod
    def login_user_from_token(request, token, client_id=None):
        """
        Verify token and login user in one call.
        
        Args:
            request: Django request object
            token: Google JWT token
            client_id: Google OAuth 2.0 Client ID
            
        Returns:
            tuple: (user, success, error_message)
        """
        try:
            service = GoogleAuthService(client_id)
            user = service.authenticate_user(token)
            
            if user:
                # Log user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"User logged in via Google: {user.email}")
                return user, True, None
            else:
                return None, False, "Failed to authenticate with Google"
        
        except Exception as e:
            error_msg = f"Google auth error: {str(e)}"
            logger.error(error_msg)
            return None, False, error_msg