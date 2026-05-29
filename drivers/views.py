# drivers/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import logging

from drivers.models import Driver
from helpers.emails import send_onboarding_reset_password_mail

logger = logging.getLogger(__name__)


class DriverIndexView(LoginRequiredMixin, ListView):
    """
    List all drivers - admin only via permission checking in template/admin panel
    """
    model = Driver
    template_name = 'drivers/index.html'
    context_object_name = 'drivers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Driver.objects.all().select_related('user').order_by('-created')
        
        # Optional search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                first_name__icontains=search_query
            ) | queryset.filter(
                last_name__icontains=search_query
            ) | queryset.filter(
                email__icontains=search_query
            ) | queryset.filter(
                license_number__icontains=search_query
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_drivers'] = Driver.objects.count()
        context['drivers_with_user'] = Driver.objects.filter(user__isnull=False).count()
        context['drivers_without_user'] = Driver.objects.filter(user__isnull=True).count()
        return context


class DriverDetailView(LoginRequiredMixin, DetailView):
    """
    Show driver details.
    Allow deactivate user or create user account.
    """
    model = Driver
    template_name = 'drivers/detail.html'
    context_object_name = 'driver'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        driver = self.get_object()
        
        # Check if user exists
        context['has_user'] = driver.user is not None
        context['user_email'] = driver.user.email if driver.user else driver.email
        context['user_active'] = driver.user.is_active if driver.user else None
        
        # Get assigned bus
        context['assigned_bus'] = driver.buses.filter(is_operational=True).first()
        
        return context


class DriverCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new driver.
    Option to create user account at the same time.
    """
    model = Driver
    template_name = 'drivers/form.html'
    fields = [
        'first_name', 'last_name', 'email', 'phone_number',
        'license_number', 'license_expiry', 'date_of_birth',
        'gender', 'address', 'profile_picture'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Driver'
        context['create_user'] = True
        return context

    def post(self, request, *args, **kwargs):
        create_user = request.POST.get('create_user_account') == 'on'
        form = self.get_form()
        
        if form.is_valid():
            with transaction.atomic():
                # Create driver
                driver = form.save(commit=False)
                driver.save()
                
                # Create user if requested
                if create_user:
                    try:
                        username = request.POST.get('username', f"{driver.first_name.lower()}{driver.last_name.lower()}")
                        
                        # Create user
                        user = User.objects.create_user(
                            username=username,
                            email=driver.email,
                            first_name=driver.first_name,
                            last_name=driver.last_name,
                        )
                        
                        # Generate random password (user will reset via email)
                        user.set_unusable_password()
                        user.save()
                        
                        # Link user to driver
                        driver.user = user
                        driver.save(update_fields=['user'])
                        
                        # Send onboarding email with try/except
                        try:
                            send_onboarding_reset_password_mail(request, user)
                            messages.success(
                                request,
                                f"✅ Driver '{driver.first_name} {driver.last_name}' created successfully! "
                                f"Welcome email sent to {driver.email}."
                            )
                        except Exception as e:
                            logger.error(f"Failed to send email to {user.email}: {str(e)}")
                            messages.warning(
                                request,
                                f"⚠️ Driver created but email failed to send. "
                                f"You can resend from the detail page."
                            )
                    
                    except Exception as e:
                        logger.error(f"Error creating user for driver: {str(e)}")
                        messages.error(
                            request,
                            f"❌ Driver created but user account failed. "
                            f"Try creating user from the detail page."
                        )
                else:
                    messages.success(
                        request,
                        f"✅ Driver '{driver.first_name} {driver.last_name}' created successfully! "
                        f"No user account created (you can add later)."
                    )
            
            return redirect('drivers-detail', uid=driver.uid)
        
        return self.form_invalid(form)


class DriverUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update driver information.
    """
    model = Driver
    template_name = 'drivers/form.html'
    fields = [
        'first_name', 'last_name', 'email', 'phone_number',
        'license_number', 'license_expiry', 'date_of_birth',
        'gender', 'address', 'profile_picture'
    ]
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Driver'
        return context

    def form_valid(self, form):
        messages.success(self.request, "✅ Driver updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('drivers-detail', kwargs={'uid': self.object.uid})


class DriverDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a driver.
    """
    model = Driver
    template_name = 'drivers/driver_confirm_delete.html'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def delete(self, request, *args, **kwargs):
        messages.success(request, "✅ Driver deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('drivers-index')


# ════════════════════════════════════════════════════════════════
# ACTIONS (for detail page)
# ════════════════════════════════════════════════════════════════

@method_decorator(require_http_methods(["POST"]), name='dispatch')
class CreateUserAccountView(LoginRequiredMixin, UpdateView):
    """
    Create a user account for a driver who doesn't have one yet.
    """
    model = Driver
    fields = []
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def post(self, request, *args, **kwargs):
        driver = self.get_object()
        
        if driver.user:
            messages.warning(request, "⚠️ This driver already has a user account!")
            return redirect('drivers-detail', uid=driver.uid)
        
        try:
            with transaction.atomic():
                username = f"{driver.first_name.lower()}{driver.last_name.lower()}"
                
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=driver.email,
                    first_name=driver.first_name,
                    last_name=driver.last_name,
                )
                
                user.set_unusable_password()
                user.save()
                
                driver.user = user
                driver.save(update_fields=['user'])
                
                try:
                    send_onboarding_reset_password_mail(request, user)
                    messages.success(
                        request,
                        f"✅ User account created! Welcome email sent to {driver.email}."
                    )
                except Exception as e:
                    logger.error(f"Email failed for {driver.email}: {str(e)}")
                    messages.warning(
                        request,
                        f"⚠️ Account created but email failed. "
                        f"Username: {username} | Email: {driver.email}"
                    )
        
        except Exception as e:
            logger.error(f"Error creating user account: {str(e)}")
            messages.error(request, f"❌ Error creating user account: {str(e)}")
        
        return redirect('drivers-detail', uid=driver.uid)


@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeactivateUserView(LoginRequiredMixin, UpdateView):
    """
    Deactivate user account for a driver.
    """
    model = Driver
    fields = []
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def post(self, request, *args, **kwargs):
        driver = self.get_object()
        
        if not driver.user:
            messages.warning(request, "⚠️ This driver doesn't have a user account!")
            return redirect('drivers-detail', uid=driver.uid)
        
        try:
            user = driver.user
            user.is_active = False
            user.save()
            
            messages.success(
                request,
                f"✅ User account '{user.username}' has been deactivated!"
            )
        
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            messages.error(request, f"❌ Error deactivating user: {str(e)}")
        
        return redirect('drivers-detail', uid=driver.uid)


@method_decorator(require_http_methods(["POST"]), name='dispatch')
class ActivateUserView(LoginRequiredMixin, UpdateView):
    """
    Activate user account for a driver.
    """
    model = Driver
    fields = []
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def post(self, request, *args, **kwargs):
        driver = self.get_object()
        
        if not driver.user:
            messages.warning(request, "⚠️ This driver doesn't have a user account!")
            return redirect('drivers-detail', uid=driver.uid)
        
        try:
            user = driver.user
            user.is_active = True
            user.save()
            
            messages.success(
                request,
                f"✅ User account '{user.username}' has been activated!"
            )
        
        except Exception as e:
            logger.error(f"Error activating user: {str(e)}")
            messages.error(request, f"❌ Error activating user: {str(e)}")
        
        return redirect('drivers-detail', uid=driver.uid)


@method_decorator(require_http_methods(["POST"]), name='dispatch')
class ResendWelcomeEmailView(LoginRequiredMixin, UpdateView):
    """
    Resend welcome email to driver's user account.
    """
    model = Driver
    fields = []
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def post(self, request, *args, **kwargs):
        driver = self.get_object()
        
        if not driver.user:
            messages.warning(request, "⚠️ This driver doesn't have a user account!")
            return redirect('drivers-detail', uid=driver.uid)
        
        try:
            send_onboarding_reset_password_mail(request, driver.user)
            messages.success(
                request,
                f"✅ Welcome email resent to {driver.email}!"
            )
        
        except Exception as e:
            logger.error(f"Failed to resend email: {str(e)}")
            messages.error(
                request,
                f"❌ Failed to send email: {str(e)}"
            )
        
        return redirect('drivers-detail', uid=driver.uid)