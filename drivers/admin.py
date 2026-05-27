# drivers/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    """
    Driver admin with read-only user link, bus assignments, and status.
    """
    list_display = (
        'get_full_name',
        'license_number',
        'phone_number',
        'email',
        'is_active',
        'license_status',
        'assigned_buses',
        'created'
    )
    
    list_filter = (
        'is_active',
        'gender',
        'created',
        ('license_expiry', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'license_number',
        'user__username'
    )
    
    readonly_fields = (
        'user',
        'uid',
        'created',
        'updated',
        'get_assigned_buses_display',
        'get_user_link'
    )
    
    fieldsets = (
        ('Identity', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'address')
        }),
        ('License', {
            'fields': ('license_number', 'license_expiry')
        }),
        ('Account', {
            'fields': ('user', 'get_user_link', 'is_active'),
            'description': 'Link to Django user account (auto-created on driver creation)'
        }),
        ('Assigned Vehicles', {
            'fields': ('get_assigned_buses_display',),
            'description': 'Buses assigned to this driver (manage from Bus admin)'
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created',)
    date_hierarchy = 'created'
    
    actions = ['mark_active', 'mark_inactive', 'check_license_expiry']
    
    def get_full_name(self, obj):
        """Display driver's full name as link"""
        return format_html(
            '<strong>{}</strong>',
            obj.get_full_name()
        )
    get_full_name.short_description = 'Driver'
    
    def license_status(self, obj):
        """Show license status with color coding"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if obj.license_expiry < today:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ EXPIRED</span>'
            )
        elif obj.license_expiry < today + timezone.timedelta(days=30):
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ EXPIRING SOON</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ Valid</span>'
            )
    license_status.short_description = 'License Status'
    
    def assigned_buses(self, obj):
        """Show count of assigned buses"""
        count = obj.buses.count()
        if count == 0:
            return format_html('<span style="color: orange;">Not assigned</span>')
        else:
            return format_html(
                '<strong style="color: green;">{}</strong>',
                count
            )
    assigned_buses.short_description = 'Buses'
    
    def get_assigned_buses_display(self, obj):
        """Display list of assigned buses"""
        buses = obj.buses.all()
        if not buses:
            return 'No buses assigned'
        return ', '.join([f"{bus.bus_number} ({bus.plate_number})" for bus in buses])
    get_assigned_buses_display.short_description = 'Assigned Buses'
    
    def get_user_link(self, obj):
        """Link to user account in admin"""
        if obj.user:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.user.username
            )
        return 'No user account'
    get_user_link.short_description = 'User Account'
    
    def mark_active(self, request, queryset):
        """Bulk action to mark drivers as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} driver(s) marked as active.')
    mark_active.short_description = '✓ Mark selected as active'
    
    def mark_inactive(self, request, queryset):
        """Bulk action to mark drivers as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} driver(s) marked as inactive.')
    mark_inactive.short_description = '✗ Mark selected as inactive'
    
    def check_license_expiry(self, request, queryset):
        """Bulk action to check license expiry"""
        from django.utils import timezone
        today = timezone.now().date()
        
        expired = queryset.filter(license_expiry__lt=today).count()
        expiring_soon = queryset.filter(
            license_expiry__gte=today,
            license_expiry__lte=today + timezone.timedelta(days=30)
        ).count()
        
        message = f'Expired: {expired}, Expiring soon: {expiring_soon}'
        self.message_user(request, message)
    check_license_expiry.short_description = '🔍 Check license expiry'