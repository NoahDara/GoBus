from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
import logging

logger = logging.getLogger(__name__)


class LoginView(View):
    """
    User login view.
    Handles:
    - Traditional email/username + password login
    - Google OAuth integration via django-allauth
    """
    template_name = 'accounts/login.html'
    
    def get(self, request):
        """Render login form"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        context = {
            'google_client_id': self._get_google_client_id()
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle traditional login submission"""
        username_or_email = request.POST.get('username_or_email', '').strip()
        password = request.POST.get('password', '')
        
        if not username_or_email or not password:
            messages.error(request, 'Please provide both username/email and password.')
            return render(request, self.template_name)
        
        # Try authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        if not user:
            # Try email login
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request, user)
            logger.info(f"User {user.username} logged in with email/password")
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            logger.warning(f"Failed login attempt for: {username_or_email}")
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, self.template_name)
    
    def _get_google_client_id(self):
        """Get Google OAuth client ID from settings"""
        from django.conf import settings
        return getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {}).get(
            'google', {}
        ).get('APP', {}).get('client_id', '')


class RegisterView(View):
    """
    User registration view.
    Handles:
    - Traditional email/password signup
    - Google OAuth signup via django-allauth
    """
    template_name = 'accounts/register.html'
    
    def get(self, request):
        """Render registration form"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle registration submission"""
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        errors = []
        
        if not all([first_name, last_name, email, username, password]):
            errors.append('All fields are required.')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name)
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            logger.info(f"New user registered: {username}")
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        
        except IntegrityError as e:
            logger.error(f"Error creating user: {str(e)}")
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, self.template_name)


class GoogleAuthView(View):
    """
    Handle Google OAuth token verification (AJAX endpoint).
    Called from login.html JavaScript when user authenticates with Google.
    """
    
    def post(self, request):
        """
        Handle POST request with Google JWT token.
        
        Expected JSON:
        {
            "token": "JWT_TOKEN_FROM_GOOGLE"
        }
        """
        import json
        from django.http import JsonResponse
        from .services import GoogleAuthHelper
        
        try:
            data = json.loads(request.body)
            token = data.get('token')
            
            if not token:
                return JsonResponse({
                    'success': False,
                    'error': 'No token provided'
                }, status=400)
            
            # Authenticate user with Google token
            user, success, error = GoogleAuthHelper.login_user_from_token(
                request, 
                token
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome, {user.first_name}!',
                    'redirect_url': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': error
                }, status=401)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in GoogleAuthView: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during authentication'
            }, status=500)


class GoogleAuthCallbackView(View):
    """
    Handles Google OAuth callback from authorization code flow.
    This is used if you want server-side OAuth flow instead of implicit.
    """
    
    def get(self, request):
        """
        Handle callback from Google OAuth.
        Exchange authorization code for token.
        """
        from .services import GoogleAuthService
        import json
        
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            logger.warning(f"Google OAuth error: {error}")
            messages.error(request, 'Google authentication failed.')
            return redirect('login')
        
        if not code:
            messages.error(request, 'No authorization code received.')
            return redirect('login')
        
        try:
            # Exchange code for token (requires backend handling)
            # This is more secure than implicit flow
            
            # For now, redirect to login
            # In production, you'd exchange the code for an access token here
            messages.info(request, 'Google authentication received. Please complete sign-in.')
            return redirect('login')
        
        except Exception as e:
            logger.error(f"Error in Google callback: {str(e)}")
            messages.error(request, 'An error occurred during authentication.')
            return redirect('login')


class LogoutView(View):
    """
    User logout view.
    Terminates user session.
    """
    
    @method_decorator(login_required)
    def get(self, request):
        """Handle logout"""
        username = request.user.username
        logout(request)
        logger.info(f"User {username} logged out")
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    User profile view.
    Shows user details and booking history.
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's bookings
        try:
            from bookings.models import Booking
            context['bookings'] = Booking.objects.filter(user=user).order_by('-created')[:10]
            context['total_bookings'] = Booking.objects.filter(user=user).count()
        except:
            context['bookings'] = []
            context['total_bookings'] = 0
        
        # Get user's payments
        try:
            from payments.models import Payment
            payments = Payment.objects.filter(user=user, status='paid').order_by('-created')[:5]
            context['payments'] = payments
            context['total_spent'] = sum(p.amount for p in payments)
        except:
            context['payments'] = []
            context['total_spent'] = 0
        
        return context


class ProfileUpdateView(LoginRequiredMixin, View):
    """
    Update user profile (name, email).
    """
    template_name = 'accounts/profile_edit.html'
    
    def get(self, request):
        """Render profile edit form"""
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle profile update"""
        user = request.user
        
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        
        # Validation
        if not all([first_name, last_name, email]):
            messages.error(request, 'All fields are required.')
            return render(request, self.template_name)
        
        # Check email uniqueness
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Email already in use by another account.')
            return render(request, self.template_name)
        
        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        logger.info(f"User {user.username} updated profile")
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')


class ChangePasswordView(LoginRequiredMixin, View):
    """
    Change user password.
    """
    template_name = 'accounts/change_password.html'
    
    def get(self, request):
        """Render password change form"""
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle password change"""
        user = request.user
        
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')
        
        # Validation
        if not user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, self.template_name)
        
        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
            return render(request, self.template_name)
        
        if new_password != new_password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, self.template_name)
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Re-authenticate user to keep session alive
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        logger.info(f"User {user.username} changed password")
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')