# payments/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Payment audit trail admin.
    Complete tracking of all payment attempts, confirmations, and failures.
    """
    list_display = (
        'payment_reference',
        'booking_ref',
        'passenger_name',
        'phone_number',
        'amount_display',
        'status_badge',
        'paynow_status_badge',
        'confirmed_at',
        'created'
    )
    
    list_filter = (
        'status',
        ('confirmed_at', admin.DateFieldListFilter),
        'created',
        'paynow_status',
    )
    
    search_fields = (
        'payment_reference',
        'booking__booking_reference',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'phone_number',
        'booking__user__email',
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'payment_reference',
        'poll_url',
        'get_booking_link',
        'get_passenger_info',
        'get_paynow_details',
        'get_status_timeline',
        'get_metadata'
    )
    
    fieldsets = (
        ('Payment Reference', {
            'fields': ('payment_reference', 'status', 'get_status_timeline')
        }),
        ('Booking Link', {
            'fields': ('booking', 'get_booking_link')
        }),
        ('Passenger', {
            'fields': ('user', 'get_passenger_info')
        }),
        ('Payment Details', {
            'fields': ('phone_number', 'amount_display')
        }),
        ('Paynow Integration', {
            'fields': ('poll_url', 'paynow_status', 'get_paynow_details'),
            'description': 'Paynow gateway details and status tracking'
        }),
        ('Payment Status', {
            'fields': ('confirmed_at',),
            'description': 'Timestamp when payment was confirmed'
        }),
        ('Error Tracking', {
            'fields': ('error_message',),
            'description': 'Error message if payment failed'
        }),
        ('Status Checks', {
            'fields': ('status_check_count', 'last_checked'),
            'classes': ('collapse',),
            'description': 'How many times status was checked from Paynow'
        }),
        ('Metadata', {
            'fields': ('get_metadata',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created',)
    date_hierarchy = 'created'
    actions = ['resend_status_check', 'mark_paid_manual', 'export_payment_report']
    
    def payment_reference(self, obj):
        """Display payment reference as code"""
        return format_html(
            '<strong style="font-family: monospace; color: #0066cc;">{}</strong>',
            obj.payment_reference
        )
    payment_reference.short_description = 'Reference'
    
    def booking_ref(self, obj):
        """Show linked booking reference"""
        if obj.booking:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:bookings_booking_change', args=[obj.booking.uid]),
                obj.booking.booking_reference
            )
        return '-'
    booking_ref.short_description = 'Booking'
    
    def passenger_name(self, obj):
        """Show passenger name"""
        return obj.user.get_full_name() or obj.user.username
    passenger_name.short_description = 'Passenger'
    
    def amount_display(self, obj):
        """Show amount with currency"""
        return format_html(
            '<strong style="color: green; font-size: 14px;">${}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        """Show payment status with color coding"""
        colors = {
            'pending': '#ff9800',      # orange
            'paid': '#4caf50',         # green
            'failed': '#f44336',       # red
            'cancelled': '#9c27b0'     # purple
        }
        color = colors.get(obj.status, '#666')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def paynow_status_badge(self, obj):
        """Show Paynow status"""
        if not obj.paynow_status:
            return '-'
        
        if obj.paynow_status.lower() == 'paid':
            color = '#4caf50'
        else:
            color = '#ff9800'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.paynow_status
        )
    paynow_status_badge.short_description = 'Paynow Status'
    
    def get_booking_link(self, obj):
        """Link to related booking"""
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.uid])
            return format_html(
                '<a href="{}" target="_blank">View Booking {}</a>',
                url,
                obj.booking.booking_reference
            )
        return 'No booking linked'
    get_booking_link.short_description = 'Booking'
    
    def get_passenger_info(self, obj):
        """Detailed passenger information"""
        user = obj.user
        return format_html(
            '<strong>{}</strong><br>Username: {}<br>Email: <a href="mailto:{}">{}</a>',
            user.get_full_name() or user.username,
            user.username,
            user.email,
            user.email
        )
    get_passenger_info.short_description = 'Passenger Info'
    
    def get_paynow_details(self, obj):
        """Paynow integration details"""
        return format_html(
            '<strong>Poll URL:</strong><br><code style="word-break: break-all; font-size: 11px;">{}</code><br><br>'
            '<strong>Paynow Status:</strong> {}<br>'
            '<strong>Status Checks:</strong> {}',
            obj.poll_url,
            obj.paynow_status or 'Not updated',
            obj.status_check_count
        )
    get_paynow_details.short_description = 'Paynow Details'
    
    def get_status_timeline(self, obj):
        """Show payment status timeline"""
        timeline = f'<strong>Current:</strong> {obj.get_status_display()}<br>'
        
        if obj.confirmed_at:
            timeline += f'<strong>Confirmed:</strong> {obj.confirmed_at.strftime("%Y-%m-%d %H:%M:%S")}<br>'
        
        if obj.last_checked:
            timeline += f'<strong>Last Checked:</strong> {obj.last_checked.strftime("%Y-%m-%d %H:%M:%S")}<br>'
        
        timeline += f'<strong>Created:</strong> {obj.created.strftime("%Y-%m-%d %H:%M:%S")}'
        
        return format_html(timeline)
    get_status_timeline.short_description = 'Timeline'
    
    def get_metadata(self, obj):
        """Display metadata as formatted JSON"""
        if obj.metadata:
            import json
            meta_str = json.dumps(obj.metadata, indent=2)
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">{}</pre>',
                meta_str
            )
        return 'No metadata'
    get_metadata.short_description = 'Metadata'
    
    def resend_status_check(self, request, queryset):
        """Bulk action to recheck payment status from Paynow"""
        # This is for logging/audit purposes
        pending = queryset.filter(status='pending')
        count = pending.count()
        
        if count > 0:
            self.message_user(
                request,
                f'{count} pending payment(s) marked for status recheck. '
                'Use the payment tracker to poll Paynow.'
            )
        else:
            self.message_user(request, 'No pending payments to recheck.')
    resend_status_check.short_description = '🔄 Recheck status (manual)'
    
    def mark_paid_manual(self, request, queryset):
        """Bulk action to manually mark as paid (use cautiously!)"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can mark payments as paid.', level='error')
            return
        
        updated = 0
        for payment in queryset.filter(status='pending'):
            payment.mark_paid(paynow_status='Manually Confirmed')
            updated += 1
        
        self.message_user(
            request,
            f'{updated} payment(s) manually marked as paid. Use with caution!'
        )
    mark_paid_manual.short_description = '⚠️ Mark as paid (manual, superuser only)'
    
    def export_payment_report(self, request, queryset):
        """Export selected payments to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payments_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Booking', 'Passenger', 'Phone', 'Amount',
            'Status', 'Paynow Status', 'Confirmed At', 'Created', 'Error'
        ])
        
        for payment in queryset:
            writer.writerow([
                payment.payment_reference,
                payment.booking.booking_reference if payment.booking else '-',
                payment.user.get_full_name(),
                payment.phone_number,
                payment.amount,
                payment.get_status_display(),
                payment.paynow_status or '-',
                payment.confirmed_at or '-',
                payment.created.strftime('%Y-%m-%d %H:%M:%S'),
                payment.error_message or '-'
            ])
        
        return response
    export_payment_report.short_description = '📊 Export to CSV'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion — payments are audit-critical"""
        return False