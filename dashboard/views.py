# dashboard/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class DashboardBaseView(LoginRequiredMixin, TemplateView):
    """
    Base dashboard view that routes to appropriate dashboard based on user role.
    """
    
    def get(self, request, *args, **kwargs):
        """Route to appropriate dashboard based on user role"""
        user = request.user
        
        # Check if user is System Administrator (superuser or staff)
        if user.is_superuser or user.is_staff:
            return redirect('dashboard-admin')
        
        # Check if user is a Driver
        try:
            from drivers.models import Driver
            driver = Driver.objects.get(user=user)
            return redirect('dashboard-driver')
        except:
            pass
        
        # Default to Passenger dashboard
        return redirect('dashboard-passenger')


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(TemplateView):
    """
    System Administrator Dashboard
    Shows overall system metrics, analytics, and management options.
    """
    template_name = 'dashboard/admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from buses.models import Bus, Route, Schedule
            from bookings.models import Booking
            from drivers.models import Driver
            from django.contrib.auth.models import User
            from payments.models import Payment
        except ImportError:
            return context
        
        # Check if user is admin
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            return redirect('passenger')
        
        now = timezone.now()
        today = now.date()
        
        # ════════════════════════════════════════════════════════════════
        # KEY METRICS
        # ════════════════════════════════════════════════════════════════
        
        context['total_users'] = User.objects.count()
        context['total_drivers'] = Driver.objects.filter(is_active=True).count()
        context['total_buses'] = Bus.objects.filter(is_operational=True).count()
        context['total_routes'] = Route.objects.filter(is_reverse=False).count()
        
        # Bookings
        context['total_bookings'] = Booking.objects.count()
        context['bookings_today'] = Booking.objects.filter(
            created__date=today
        ).count()
        context['bookings_pending'] = Booking.objects.filter(
            status='pending'
        ).count()
        context['bookings_confirmed'] = Booking.objects.filter(
            status='confirmed'
        ).count()
        
        # Revenue
        confirmed_payments = Payment.objects.filter(status='paid')
        context['total_revenue'] = sum(p.amount for p in confirmed_payments)
        context['revenue_today'] = sum(
            p.amount for p in confirmed_payments.filter(confirmed_at__date=today)
        )
        context['pending_revenue'] = sum(
            p.amount for p in Payment.objects.filter(status='pending')
        )
        
        # Schedules
        context['total_schedules'] = Schedule.objects.count()
        context['schedules_today'] = Schedule.objects.filter(
            departure_time__date=today
        ).count()
        context['schedules_active'] = Schedule.objects.filter(
            status__in=['scheduled', 'in_progress'],
            departure_time__gte=now
        ).count()
        
        # ════════════════════════════════════════════════════════════════
        # RECENT DATA
        # ════════════════════════════════════════════════════════════════
        
        context['recent_bookings'] = Booking.objects.select_related(
            'user', 'schedule', 'schedule__route'
        ).order_by('-created')[:5]
        
        context['recent_payments'] = Payment.objects.select_related(
            'user', 'booking'
        ).order_by('-created')[:5]
        
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        # Top routes
        context['top_routes'] = Route.objects.filter(
            is_reverse=False
        ).annotate(
            booking_count=Count('schedules__bookings')
        ).order_by('-booking_count')[:5]
        
        # ════════════════════════════════════════════════════════════════
        # CHARTS DATA (for frontend)
        # ════════════════════════════════════════════════════════════════
        
        # Bookings trend (last 7 days)
        from datetime import timedelta
        bookings_trend = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = Booking.objects.filter(created__date=day).count()
            bookings_trend.append({
                'date': day.strftime('%a'),
                'count': count
            })
        context['bookings_trend'] = bookings_trend
        
        # Booking status distribution
        context['booking_status'] = {
            'pending': context['bookings_pending'],
            'confirmed': context['bookings_confirmed'],
            'cancelled': Booking.objects.filter(status='cancelled').count()
        }
        
        # Bus operational status
        context['bus_status'] = {
            'operational': Bus.objects.filter(is_operational=True).count(),
            'maintenance': Bus.objects.filter(is_operational=False).count()
        }
        
        logger.info(f"Admin dashboard accessed by {self.request.user.username}")
        
        return context


@method_decorator(login_required, name='dispatch')
class DriverDashboardView(TemplateView):
    """
    Driver Dashboard
    Shows assigned bus, current trips, schedule, and earnings.
    """
    template_name = 'dashboard/driver.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from drivers.models import Driver
            from buses.models import Schedule
            from bookings.models import Booking
            from payments.models import Payment
        except ImportError:
            return context
        
        user = self.request.user
        
        # Get driver profile
        try:
            driver = Driver.objects.get(user=user)
        except Driver.DoesNotExist:
            logger.warning(f"Non-driver user {user.username} accessed driver dashboard")
            return redirect('passenger')
        
        context['driver'] = driver
        
        # ════════════════════════════════════════════════════════════════
        # ASSIGNED BUS INFO
        # ════════════════════════════════════════════════════════════════
        
        assigned_buses = driver.buses.all()
        context['assigned_buses'] = assigned_buses
        
        if assigned_buses.exists():
            # Use first/main bus
            current_bus = assigned_buses.first()
            context['current_bus'] = current_bus
            context['total_seats'] = current_bus.capacity
            context['available_seats'] = current_bus.seats.count()
        
        # ════════════════════════════════════════════════════════════════
        # SCHEDULES & TRIPS
        # ════════════════════════════════════════════════════════════════
        
        now = timezone.now()
        today = now.date()
        
        if assigned_buses.exists():
            # Today's schedules
            context['today_schedules'] = Schedule.objects.filter(
                bus__in=assigned_buses,
                departure_time__date=today
            ).order_by('departure_time')
            
            # Upcoming schedules (next 7 days)
            context['upcoming_schedules'] = Schedule.objects.filter(
                bus__in=assigned_buses,
                departure_time__gte=now,
                departure_time__date__gte=today
            ).order_by('departure_time')[:5]
            
            # Total trips this month
            from datetime import timedelta
            month_start = today.replace(day=1)
            context['trips_this_month'] = Schedule.objects.filter(
                bus__in=assigned_buses,
                departure_time__date__gte=month_start
            ).count()
        
        # ════════════════════════════════════════════════════════════════
        # EARNINGS
        # ════════════════════════════════════════════════════════════════
        
        if assigned_buses.exists():
            # Get bookings for this driver's buses
            bus_bookings = Booking.objects.filter(
                schedule__bus__in=assigned_buses
            )
            
            # Revenue from trips
            trip_payments = Payment.objects.filter(
                booking__in=bus_bookings,
                status='paid'
            )
            
            context['total_earnings'] = sum(p.amount for p in trip_payments)
            context['earnings_today'] = sum(
                p.amount for p in trip_payments.filter(
                    confirmed_at__date=today
                )
            )
            context['earnings_month'] = sum(
                p.amount for p in trip_payments.filter(
                    confirmed_at__date__gte=today.replace(day=1)
                )
            )
        
        # ════════════════════════════════════════════════════════════════
        # PASSENGER INFO
        # ════════════════════════════════════════════════════════════════
        
        if assigned_buses.exists():
            current_schedule = Schedule.objects.filter(
                bus__in=assigned_buses,
                status='in_progress'
            ).first()
            
            if current_schedule:
                context['current_trip'] = current_schedule
                context['current_passengers'] = Booking.objects.filter(
                    schedule=current_schedule,
                    status='confirmed'
                )
        
        logger.info(f"Driver dashboard accessed by {user.username}")
        
        return context


@method_decorator(login_required, name='dispatch')
class PassengerDashboardView(TemplateView):
    """
    Passenger Dashboard
    Shows user's bookings, upcoming trips, and travel history.
    """
    template_name = 'dashboard/passenger.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from bookings.models import Booking
            from payments.models import Payment
        except ImportError:
            return context
        
        user = self.request.user
        now = timezone.now()
        today = now.date()
        
        # ════════════════════════════════════════════════════════════════
        # BOOKINGS
        # ════════════════════════════════════════════════════════════════
        
        all_bookings = Booking.objects.filter(user=user).order_by('-created')
        
        # Upcoming bookings
        context['upcoming_bookings'] = Booking.objects.filter(
            user=user,
            status='confirmed',
            schedule__departure_time__gte=now
        ).order_by('schedule__departure_time')[:5]
        
        # Past bookings (completed trips)
        context['past_bookings'] = Booking.objects.filter(
            user=user,
            schedule__departure_time__lt=now
        ).order_by('-schedule__departure_time')[:5]
        
        # Pending bookings (awaiting payment)
        context['pending_bookings'] = Booking.objects.filter(
            user=user,
            status='pending'
        )
        
        context['total_bookings'] = all_bookings.count()
        context['confirmed_bookings'] = Booking.objects.filter(
            user=user,
            status='confirmed'
        ).count()
        
        # ════════════════════════════════════════════════════════════════
        # PAYMENT & SPENDING
        # ════════════════════════════════════════════════════════════════
        
        payments = Payment.objects.filter(user=user)
        context['total_spent'] = sum(p.amount for p in payments.filter(status='paid'))
        context['pending_payments'] = sum(p.amount for p in payments.filter(status='pending'))
        
        # This month spending
        month_start = today.replace(day=1)
        context['spent_this_month'] = sum(
            p.amount for p in payments.filter(
                status='paid',
                confirmed_at__date__gte=month_start
            )
        )
        
        # ════════════════════════════════════════════════════════════════
        # TRAVEL STATISTICS
        # ════════════════════════════════════════════════════════════════
        
        completed_bookings = Booking.objects.filter(
            user=user,
            schedule__departure_time__lt=now
        )
        context['total_trips'] = completed_bookings.count()
        
        # Get unique routes traveled
        context['routes_traveled'] = completed_bookings.values(
            'schedule__route__name'
        ).distinct().count()
        
        # ════════════════════════════════════════════════════════════════
        # SAVED INFORMATION
        # ════════════════════════════════════════════════════════════════
        
        # Frequently used routes
        frequent_routes = completed_bookings.values(
            'schedule__route__name',
            'schedule__route__origin',
            'schedule__route__destination'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        context['frequent_routes'] = frequent_routes
        
        logger.info(f"Passenger dashboard accessed by {user.username}")
        
        return context