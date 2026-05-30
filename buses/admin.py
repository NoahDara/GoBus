# buses/admin.py

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.db.models import Count
from .models import Bus, Seat, Route, RouteStop, RouteSegment, Schedule


# ============================================================================
# INLINE ADMINS
# ============================================================================

class SeatInline(admin.TabularInline):
    """
    Inline admin for seats — show all seats for a bus.
    """
    model = Seat
    extra = 0
    fields = ('seat_number', 'row', 'uid')
    readonly_fields = ('seat_number', 'row', 'uid')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Seats are auto-generated, don't allow manual add"""
        return False


class RouteStopInline(admin.TabularInline):
    """
    Inline admin for route stops.
    """
    model = RouteStop
    extra = 1
    fields = ('order', 'name')
    ordering = ('order',)


class RouteSegmentInline(admin.TabularInline):
    """
    Inline admin for route segments (pricing between stops).
    """
    model = RouteSegment
    extra = 1
    fields = ('from_stop', 'to_stop', 'price')
    ordering = ('from_stop__order',)


class ScheduleInline(admin.TabularInline):
    """
    Inline admin for schedules — show recent trips for a route.
    """
    model = Schedule
    extra = 0
    fields = ('departure_time', 'arrival_time', 'status', 'available_seats')
    readonly_fields = ('departure_time', 'arrival_time', 'available_seats')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Create schedules from Schedule admin"""
        return False


# ============================================================================
# BUS ADMIN
# ============================================================================

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    """
    Bus admin with seats display and driver assignment.
    """
    list_display = (
        'bus_number',
        'plate_number',
        'assigned_driver',
        'capacity',
        'seat_status',
        'is_operational',
        'created'
    )
    
    list_filter = (
        'is_operational',
        'created',
        ('driver', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'bus_number',
        'plate_number',
        'driver__first_name',
        'driver__last_name'
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'get_seat_count',
        'get_schedules'
    )
    
    fieldsets = (
        ('Bus Details', {
            'fields': ('bus_number', 'plate_number', 'capacity', 'is_operational')
        }),
        ('Driver Assignment', {
            'fields': ('driver',)
        }),
        ('Seats', {
            'fields': ('get_seat_count',),
            'description': 'Total seats auto-generated on bus creation'
        }),
        ('Recent Schedules', {
            'fields': ('get_schedules',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SeatInline, ScheduleInline]
    ordering = ('bus_number',)
    actions = ['mark_operational', 'mark_non_operational']
    
    def assigned_driver(self, obj):
        """Show assigned driver"""
        if obj.driver:
            return format_html(
                '<strong style="color: green;">{}</strong>',
                obj.driver.get_full_name()
            )
        return mark_safe('<span style="color: orange;">Not assigned</span>')
    assigned_driver.short_description = 'Driver'
    
    def seat_status(self, obj):
        """Show seat layout status"""
        total_seats = obj.seats.count()
        if total_seats == 0:
            return mark_safe('<span style="color: red;">⚠️ No seats</span>')
        return format_html(
            '<strong>{}</strong> seats',
            total_seats
        )
    seat_status.short_description = 'Seats'
    
    def get_seat_count(self, obj):
        """Count total seats"""
        count = obj.seats.count()
        return format_html(
            '<strong style="color: green;">{}</strong> seats generated',
            count
        )
    get_seat_count.short_description = 'Seat Count'
    
    def get_schedules(self, obj):
        """Show recent schedules"""
        schedules = obj.schedules.filter(status__in=['scheduled', 'in_progress'])[:5]
        if not schedules:
            return 'No upcoming schedules'
        return format_html(
            '<ul>{}</ul>',
            mark_safe(''.join([
                f'<li>{s.route.name} @ {s.departure_time.strftime("%Y-%m-%d %H:%M")}</li>'
                for s in schedules
            ]))
        )
    get_schedules.short_description = 'Upcoming Trips'
    
    def mark_operational(self, request, queryset):
        """Bulk action to mark buses as operational"""
        updated = queryset.update(is_operational=True)
        self.message_user(request, f'{updated} bus(es) marked as operational.')
    mark_operational.short_description = '✓ Mark as operational'
    
    def mark_non_operational(self, request, queryset):
        """Bulk action to mark buses as non-operational"""
        updated = queryset.update(is_operational=False)
        self.message_user(request, f'{updated} bus(es) marked as non-operational.')
    mark_non_operational.short_description = '✗ Mark as non-operational'


# ============================================================================
# ROUTE ADMIN
# ============================================================================

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    """
    Route admin with stops and segments.
    """
    list_display = (
        'name',
        'route_path',
        'stop_count',
        'is_reverse',
        'estimated_duration',
        'created'
    )
    
    list_filter = (
        'is_reverse',
        'created',
    )
    
    search_fields = (
        'name',
        'origin',
        'destination',
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'is_reverse',
        'reverse_of',
        'get_segment_pricing'
    )
    
    fieldsets = (
        ('Route Details', {
            'fields': ('name', 'origin', 'destination', 'estimated_duration')
        }),
        ('Route Type', {
            'fields': ('is_reverse', 'reverse_of'),
            'description': 'Main routes auto-generate reverse routes'
        }),
        ('Segment Pricing', {
            'fields': ('get_segment_pricing',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RouteStopInline, RouteSegmentInline, ScheduleInline]
    ordering = ('name',)
    
    def route_path(self, obj):
        """Show route as origin → destination"""
        return format_html(
            '<strong>{}</strong> → <strong>{}</strong>',
            obj.origin,
            obj.destination
        )
    route_path.short_description = 'Route'
    
    def stop_count(self, obj):
        """Show number of stops"""
        count = obj.stops.count()
        return format_html('<strong>{}</strong>', count)
    stop_count.short_description = 'Stops'
    
    def get_segment_pricing(self, obj):
        """Display all segment pricing"""
        segments = obj.segments.all().order_by('from_stop__order')
        if not segments:
            return 'No segments'
        return format_html(
            '<table><tr><th>From</th><th>To</th><th>Price</th></tr>{}</table>',
            mark_safe(''.join([
                f'<tr><td>{s.from_stop.name}</td><td>{s.to_stop.name}</td><td>${s.price}</td></tr>'
                for s in segments
            ]))
        )
    get_segment_pricing.short_description = 'Segment Pricing'


# ============================================================================
# ROUTE STOP ADMIN (Read-only, managed via Route inline)
# ============================================================================

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    """
    RouteStop admin — mainly for reference/viewing.
    """
    list_display = ('route', 'order', 'name')
    list_filter = ('route',)
    search_fields = ('name', 'route__name')
    readonly_fields = ('uid', 'created', 'updated')
    
    fieldsets = (
        ('Stop Details', {
            'fields': ('route', 'name', 'order')
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('route', 'order')


# ============================================================================
# ROUTE SEGMENT ADMIN (Pricing management)
# ============================================================================

@admin.register(RouteSegment)
class RouteSegmentAdmin(admin.ModelAdmin):
    """
    RouteSegment admin for managing segment pricing.
    """
    list_display = ('route', 'from_stop_name', 'to_stop_name', 'price')
    list_filter = ('route',)
    search_fields = ('route__name', 'from_stop__name', 'to_stop__name')
    readonly_fields = ('uid', 'created', 'updated')
    
    fieldsets = (
        ('Segment', {
            'fields': ('route', 'from_stop', 'to_stop', 'price')
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('route', 'from_stop__order')
    
    def from_stop_name(self, obj):
        return obj.from_stop.name
    from_stop_name.short_description = 'From'
    
    def to_stop_name(self, obj):
        return obj.to_stop.name
    to_stop_name.short_description = 'To'


# ============================================================================
# SCHEDULE ADMIN
# ============================================================================

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """
    Schedule admin for managing bus trips.
    """
    list_display = (
        'bus_number',
        'route_name',
        'departure_time',
        'arrival_time',
        'occupancy',
        'status',
        'created'
    )
    
    list_filter = (
        'status',
        'created',
        ('departure_time', admin.DateFieldListFilter),
        ('bus', admin.RelatedOnlyFieldListFilter),
        ('route', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'bus__bus_number',
        'route__name',
        'route__origin',
        'route__destination'
    )
    
    readonly_fields = (
        'uid',
        'created',
        'updated',
        'get_occupancy_display'
    )
    
    fieldsets = (
        ('Trip Details', {
            'fields': ('bus', 'route', 'status')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time')
        }),
        ('Seat Status', {
            'fields': ('available_seats', 'get_occupancy_display')
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-departure_time',)
    date_hierarchy = 'departure_time'
    actions = ['mark_scheduled', 'mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def bus_number(self, obj):
        return obj.bus.bus_number
    bus_number.short_description = 'Bus'
    
    def route_name(self, obj):
        return obj.route.name
    route_name.short_description = 'Route'
    
    def occupancy(self, obj):
        """Show occupancy percentage with color coding"""
        total = obj.bus.capacity
        booked = total - obj.available_seats
        percentage = int((booked / total) * 100) if total > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{} ({}%)</span>',
            color,
            booked,
            total,
            percentage
        )
    occupancy.short_description = 'Occupancy'
    
    def get_occupancy_display(self, obj):
        """Detailed occupancy display"""
        total = obj.bus.capacity
        booked = total - obj.available_seats
        available = obj.available_seats
        percentage = int((booked / total) * 100) if total > 0 else 0
        
        return format_html(
            '<strong>{}/{}</strong> seats booked ({}%)<br>Available: <strong>{}</strong>',
            booked,
            total,
            percentage,
            available
        )
    get_occupancy_display.short_description = 'Occupancy Details'
    
    def mark_scheduled(self, request, queryset):
        updated = queryset.update(status='scheduled')
        self.message_user(request, f'{updated} schedule(s) marked as scheduled.')
    mark_scheduled.short_description = 'Mark as scheduled'
    
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} schedule(s) marked as in progress.')
    mark_in_progress.short_description = 'Mark as in progress'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} schedule(s) marked as completed.')
    mark_completed.short_description = 'Mark as completed'
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} schedule(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark as cancelled'


# ============================================================================
# SEAT ADMIN (Read-only reference)
# ============================================================================

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    """
    Seat admin — read-only for reference/checking layout.
    """
    list_display = ('bus_number', 'seat_number', 'row')
    list_filter = ('bus__bus_number',)
    search_fields = ('bus__bus_number', 'seat_number')
    readonly_fields = ('uid', 'created', 'updated', 'bus', 'seat_number', 'row')
    
    fieldsets = (
        ('Seat Details', {
            'fields': ('bus', 'seat_number', 'row')
        }),
        ('System', {
            'fields': ('uid', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('bus', 'row', 'seat_number')
    
    def has_add_permission(self, request):
        """Seats are auto-generated, don't allow manual creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow seat deletion"""
        return False
    
    def bus_number(self, obj):
        return obj.bus.bus_number
    bus_number.short_description = 'Bus'