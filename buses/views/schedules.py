# buses/views.py - Add schedules views

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q, Count
from datetime import datetime, timedelta
from ..models import Schedule, Bus, Route
from ..forms import ScheduleForm, ScheduleStatusForm
from helpers.mixins import UIDObjectMixin


class ScheduleListView(LoginRequiredMixin, ListView):
    """List all schedules"""
    model = Schedule
    template_name = 'schedules/index.html'
    context_object_name = 'schedules'
    paginate_by = 20

    def get_queryset(self):
        queryset = Schedule.objects.select_related(
            'bus__driver__user', 'route'
        ).annotate(
            total_bookings=Count('bookings')
        )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status in ['scheduled', 'in_progress', 'completed', 'cancelled']:
            queryset = queryset.filter(status=status)
        
        # Filter by bus
        bus_uid = self.request.GET.get('bus')
        if bus_uid:
            queryset = queryset.filter(bus__uid=bus_uid)
        
        # Filter by route
        route_uid = self.request.GET.get('route')
        if route_uid:
            queryset = queryset.filter(route__uid=route_uid)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(departure_time__gte=date_from)
        if date_to:
            queryset = queryset.filter(departure_time__lte=date_to)
        
        return queryset.order_by('-departure_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_schedules'] = Schedule.objects.count()
        context['scheduled_count'] = Schedule.objects.filter(status='scheduled').count()
        context['in_progress_count'] = Schedule.objects.filter(status='in_progress').count()
        context['completed_count'] = Schedule.objects.filter(status='completed').count()
        context['cancelled_count'] = Schedule.objects.filter(status='cancelled').count()
        
        # For filters
        context['buses'] = Bus.objects.filter(is_operational=True, is_active=True)
        context['routes'] = Route.objects.filter(is_reverse=False, is_active=True)
        
        return context


class ScheduleCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new schedule"""
    model = Schedule
    form_class = ScheduleForm
    template_name = 'schedules/create.html'
    success_message = "Schedule created successfully"

    def get_success_url(self):
        return reverse_lazy('schedules-detail', kwargs={'uid': self.object.uid})


class ScheduleDetailView(LoginRequiredMixin, UIDObjectMixin, DetailView):
    """Display schedule details with full management"""
    model = Schedule
    template_name = 'schedules/detail.html'
    context_object_name = 'schedule'

    def get_queryset(self):
        return Schedule.objects.select_related(
            'bus__driver__user', 'route'
        ).prefetch_related('bookings__user', 'bookings__payment')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schedule = self.object
        
        context['form'] = ScheduleForm(instance=schedule)
        context['status_form'] = ScheduleStatusForm(instance=schedule)
        context['bookings'] = schedule.bookings.select_related(
            'user', 'payment'
        ).order_by('created')
        
        # Calculate duration
        if schedule.departure_time and schedule.arrival_time:
            duration = schedule.arrival_time - schedule.departure_time
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            context['duration'] = f"{hours}h {minutes}m"
        else:
            context['duration'] = "—"
        
        # Calculate stats
        total_bookings = schedule.bookings.count()
        confirmed_bookings = schedule.bookings.filter(status='confirmed').count()
        pending_bookings = schedule.bookings.filter(status='pending').count()
        cancelled_bookings = schedule.bookings.filter(status='cancelled').count()
        
        context['total_bookings'] = total_bookings
        context['confirmed_bookings'] = confirmed_bookings
        context['pending_bookings'] = pending_bookings
        context['cancelled_bookings'] = cancelled_bookings
        context['available_seats'] = schedule.available_seats
        
        # Revenue calculation
        context['total_revenue'] = sum(
            float(b.fare) for b in schedule.bookings.filter(status='confirmed')
        )
        context['pending_revenue'] = sum(
            float(b.fare) for b in schedule.bookings.filter(status='pending')
        )
        
        return context


class ScheduleStatusChangeView(LoginRequiredMixin, UIDObjectMixin, View):
    """Change schedule status via AJAX or form post"""
    model = Schedule

    def post(self, request, uid):
        schedule = get_object_or_404(Schedule, uid=uid)
        form = ScheduleStatusForm(request.POST, instance=schedule)
        
        if form.is_valid():
            old_status = schedule.status
            schedule = form.save()
            message = f"Schedule status changed from {old_status} to {schedule.status}"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'status': schedule.status,
                })
            
            return redirect('schedules-detail', uid=schedule.uid)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        
        return redirect('schedules-detail', uid=schedule.uid)


class ScheduleCancelView(LoginRequiredMixin, UIDObjectMixin, View):
    """Cancel a schedule"""
    model = Schedule

    def post(self, request, uid):
        schedule = get_object_or_404(Schedule, uid=uid)
        
        # Only allow cancelling scheduled or in_progress schedules
        if schedule.status not in ['scheduled', 'in_progress']:
            message = f"Cannot cancel a {schedule.status} schedule"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': message}, status=400)
            return redirect('schedules-detail', uid=schedule.uid)
        
        schedule.status = 'cancelled'
        schedule.save()
        
        message = f"Schedule cancelled successfully"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
            })
        
        return redirect('schedules-detail', uid=schedule.uid)