# notifications/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Notification audit trail admin.
    Track all emails and SMS sent to users (booking confirmations, payment confirmations, etc.)
    """
    list_display = (
        'notification_ref',
        'notification_type_badge',
        'channel_badge',
        'recipient_display',
        'status_badge',
        'sent_at',
        'created'
    )
    
    list_filter = (
        'notification_type',
        'channel',
        'status',
        ('sent_at', admin.DateFieldListFilter),
        ('created', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'recipient',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'booking__booking_reference',
        'payment__payment_reference',
        'subject',
        'message'
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'get_user_link',
        'get_booking_link',
        'get_payment_link',
        'get_message_preview',
        'sent_at'
    )
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('notification_type', 'channel', 'status')
        }),
        ('Recipient', {
            'fields': ('recipient', 'user', 'get_user_link')
        }),
        ('Related Records', {
            'fields': ('booking', 'get_booking_link', 'payment', 'get_payment_link'),
            'description': 'Links to related booking or payment'
        }),
        ('Message Content', {
            'fields': ('subject', 'get_message_preview'),
            'description': 'Email subject and message body'
        }),
        ('Delivery Status', {
            'fields': ('sent_at', 'error_message'),
            'description': 'When sent and any errors'
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created',)
    date_hierarchy = 'created'
    actions = ['resend_failed', 'mark_as_sent']
    
    def notification_ref(self, obj):
        """Display notification ID"""
        return format_html(
            '<strong style="font-family: monospace; color: #666;">{}</strong>',
            str(obj.uid)[:8] + '...'
        )
    notification_ref.short_description = 'ID'
    
    def notification_type_badge(self, obj):
        """Show notification type with icons"""
        icons = {
            'booking_confirmation': '📅',
            'payment_confirmed': '✅',
            'booking_cancelled': '❌',
            'payment_failed': '⚠️'
        }
        icon = icons.get(obj.notification_type, '📧')
        
        return format_html(
            '{} <strong>{}</strong>',
            icon,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'
    
    def channel_badge(self, obj):
        """Show channel with icon"""
        icon = '📧' if obj.channel == 'email' else '💬'
        color = '#0066cc' if obj.channel == 'email' else '#ff9800'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_channel_display()
        )
    channel_badge.short_description = 'Channel'
    
    def recipient_display(self, obj):
        """Show recipient address/phone"""
        if obj.channel == 'email':
            return format_html(
                '<a href="mailto:{}">{}</a>',
                obj.recipient,
                obj.recipient
            )
        else:
            return format_html(
                '<a href="tel:{}">{}</a>',
                obj.recipient,
                obj.recipient
            )
    recipient_display.short_description = 'Recipient'
    
    def status_badge(self, obj):
        """Show status with color coding"""
        colors = {
            'pending': '#ff9800',      # orange
            'sent': '#4caf50',         # green
            'failed': '#f44336'        # red
        }
        color = colors.get(obj.status, '#666')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_user_link(self, obj):
        """Link to user account"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" target="_blank">{} ({})</a>',
            url,
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    get_user_link.short_description = 'User Account'
    
    def get_booking_link(self, obj):
        """Link to related booking"""
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.uid])
            return format_html(
                '<a href="{}" target="_blank">View Booking {}</a>',
                url,
                obj.booking.booking_reference
            )
        return '-'
    get_booking_link.short_description = 'Booking'
    
    def get_payment_link(self, obj):
        """Link to related payment"""
        if obj.payment:
            url = reverse('admin:payments_payment_change', args=[obj.payment.uid])
            return format_html(
                '<a href="{}" target="_blank">View Payment {}</a>',
                url,
                obj.payment.payment_reference
            )
        return '-'
    get_payment_link.short_description = 'Payment'
    
    def get_message_preview(self, obj):
        """Show message preview (truncated)"""
        # Strip HTML tags for plain text preview
        import re
        text = re.sub('<[^<]+?>', '', obj.message)
        preview = text[:500] + ('...' if len(text) > 500 else '')
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; '
            'max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px;">'
            '{}'
            '</div>',
            preview
        )
    get_message_preview.short_description = 'Message'
    
    def resend_failed(self, request, queryset):
        """Bulk action to mark failed notifications for resend"""
        failed = queryset.filter(status='failed')
        count = failed.count()
        
        if count > 0:
            # Mark as pending so they can be resent
            failed.update(status='pending', error_message='')
            self.message_user(request, f'{count} failed notification(s) marked as pending.')
        else:
            self.message_user(request, 'No failed notifications to resend.')
    resend_failed.short_description = '🔄 Mark for resend (manual)'
    
    def mark_as_sent(self, request, queryset):
        """Bulk action to mark as sent (use cautiously!)"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can mark notifications as sent.', level='error')
            return
        
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='sent',
            sent_at=timezone.now()
        )
        
        self.message_user(
            request,
            f'{updated} notification(s) marked as sent. Use with caution!'
        )
    mark_as_sent.short_description = '✓ Mark as sent (manual, superuser only)'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion — notifications are audit logs"""
        return False
    
    def has_add_permission(self, request):
        """Notifications are auto-created, prevent manual creation"""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Make almost everything readonly"""
        if obj:  # Editing existing notification
            return [
                'user', 'booking', 'payment', 'notification_type', 'channel',
                'recipient', 'subject', 'message', 'uid', 'created', 'updated',
                'get_user_link', 'get_booking_link', 'get_payment_link', 'get_message_preview'
            ]
        return self.readonly_fields