# bookings/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Booking admin with booking details, passenger info, seat assignment, and fare.
    """
    list_display = (
        'booking_reference',
        'passenger_name',
        'route_display',
        'trip_date',
        'seat_display',
        'fare_display',
        'status_badge',
        'created'
    )
    
    list_filter = (
        'status',
        'created',
        ('schedule__departure_time', admin.DateFieldListFilter),
        ('schedule__route', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'booking_reference',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'schedule__route__name',
        'seat__seat_number'
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'booking_reference',
        'get_passenger_info',
        'get_schedule_info',
        'get_seat_info',
        'get_route_stops',
        'get_fare_breakdown'
    )
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking_reference', 'status')
        }),
        ('Passenger', {
            'fields': ('user', 'get_passenger_info')
        }),
        ('Trip Details', {
            'fields': ('schedule', 'get_schedule_info')
        }),
        ('Seat Assignment', {
            'fields': ('seat', 'get_seat_info')
        }),
        ('Route Segment', {
            'fields': ('boarding_stop', 'alighting_stop', 'get_route_stops')
        }),
        ('Fare', {
            'fields': ('fare', 'get_fare_breakdown')
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',),
            'description': 'Only populated if booking was cancelled'
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created',)
    date_hierarchy = 'created'
    actions = ['mark_confirmed', 'mark_cancelled']
    
    def booking_reference(self, obj):
        """Display booking reference as link"""
        return format_html(
            '<strong style="font-family: monospace; color: #0066cc;">{}</strong>',
            obj.booking_reference
        )
    booking_reference.short_description = 'Reference'
    
    def passenger_name(self, obj):
        """Show passenger full name"""
        return obj.user.get_full_name() or obj.user.username
    passenger_name.short_description = 'Passenger'
    
    def route_display(self, obj):
        """Show route as origin → destination"""
        route = obj.schedule.route
        return format_html(
            '<strong>{}</strong> → <strong>{}</strong>',
            route.origin,
            route.destination
        )
    route_display.short_description = 'Route'
    
    def trip_date(self, obj):
        """Show trip date"""
        return obj.schedule.departure_time.strftime('%Y-%m-%d %H:%M')
    trip_date.short_description = 'Departure'
    
    def seat_display(self, obj):
        """Show seat location"""
        return format_html(
            'Row {} Seat {}',
            obj.seat.row,
            obj.seat.seat_number
        )
    seat_display.short_description = 'Seat'
    
    def fare_display(self, obj):
        """Show fare amount"""
        return format_html(
            '<strong style="color: green;">${}</strong>',
            obj.fare
        )
    fare_display.short_description = 'Fare'
    
    def status_badge(self, obj):
        """Show status with color coding"""
        colors = {
            'pending': '#ff9800',      # orange
            'confirmed': '#4caf50',    # green
            'cancelled': '#f44336'     # red
        }
        color = colors.get(obj.status, '#666')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_passenger_info(self, obj):
        """Detailed passenger information"""
        user = obj.user
        return format_html(
            '<strong>{}</strong><br>Username: {}<br>Email: <a href="mailto:{}">{}</a><br>Phone: {}',
            user.get_full_name() or user.username,
            user.username,
            user.email,
            user.email,
            getattr(user, 'phone_number', 'N/A')
        )
    get_passenger_info.short_description = 'Passenger Info'
    
    def get_schedule_info(self, obj):
        """Detailed schedule information"""
        schedule = obj.schedule
        return format_html(
            '<strong>Bus:</strong> {} ({})<br><strong>Route:</strong> {}<br><strong>Departure:</strong> {}<br><strong>Arrival:</strong> {}',
            schedule.bus.bus_number,
            schedule.bus.plate_number,
            schedule.route.name,
            schedule.departure_time.strftime('%Y-%m-%d %H:%M'),
            schedule.arrival_time.strftime('%Y-%m-%d %H:%M')
        )
    get_schedule_info.short_description = 'Schedule Info'
    
    def get_seat_info(self, obj):
        """Seat location display"""
        seat = obj.seat
        return format_html(
            '<strong>Bus:</strong> {}<br><strong>Row:</strong> {}<br><strong>Seat #:</strong> {}',
            seat.bus.bus_number,
            seat.row,
            seat.seat_number
        )
    get_seat_info.short_description = 'Seat Info'
    
    def get_route_stops(self, obj):
        """Show boarding and alighting stops"""
        return format_html(
            '<strong>Board at:</strong> {}<br><strong>Alight at:</strong> {}',
            obj.boarding_stop.name,
            obj.alighting_stop.name
        )
    get_route_stops.short_description = 'Stops'
    
    def get_fare_breakdown(self, obj):
        """Show how fare is calculated"""
        route = obj.schedule.route
        segment_price = route.calculate_fare(
            obj.boarding_stop.order,
            obj.alighting_stop.order
        )
        return format_html(
            '<strong>Total Fare: ${}</strong><br>Segments: {} to {}',
            obj.fare,
            obj.boarding_stop.order,
            obj.alighting_stop.order
        )
    get_fare_breakdown.short_description = 'Fare Breakdown'
    
    def mark_confirmed(self, request, queryset):
        """Bulk action to mark bookings as confirmed"""
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} booking(s) marked as confirmed.')
    mark_confirmed.short_description = '✓ Mark as confirmed'
    
    def mark_cancelled(self, request, queryset):
        """Bulk action to mark bookings as cancelled"""
        updated = queryset.filter(status='pending').update(
            status='cancelled',
            cancelled_at=timezone.now(),
            cancellation_reason='Cancelled via admin'
        )
        self.message_user(request, f'{updated} booking(s) cancelled.')
    mark_cancelled.short_description = '✗ Mark as cancelled'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion — bookings are audit-critical"""
        return False