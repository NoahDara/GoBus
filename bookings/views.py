# bookings/views.py - SIMPLIFIED VERSION

from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import logging
import uuid

from .models import Booking
from buses.models import Schedule, Seat, RouteStop

logger = logging.getLogger(__name__)


class BookingCreateView(LoginRequiredMixin, View):
    """
    Create a booking
    
    POST /bookings/create/
    
    Form data:
    - schedule_uid
    - seat_uid
    - boarding_stop_uid
    - alighting_stop_uid
    
    Redirects to payment
    """
    
    def post(self, request):
        schedule_uid = request.POST.get('schedule_uid')
        seat_uid = request.POST.get('seat_uid')
        boarding_stop_uid = request.POST.get('boarding_stop_uid')
        alighting_stop_uid = request.POST.get('alighting_stop_uid')
        
        # Get objects
        try:
            schedule = Schedule.objects.get(uid=schedule_uid)
            seat = Seat.objects.get(uid=seat_uid)
            boarding_stop = RouteStop.objects.get(uid=boarding_stop_uid)
            alighting_stop = RouteStop.objects.get(uid=alighting_stop_uid)
        except Exception as e:
            messages.error(request, 'Invalid selection. Try again.')
            logger.error(f"Booking error: {str(e)}")
            return redirect('dashboard')
        
        # Validate stops
        if boarding_stop.order >= alighting_stop.order:
            messages.error(request, 'Boarding must be before alighting.')
            return redirect('dashboard')
        
        # Check seat available
        if Booking.objects.filter(
            schedule=schedule,
            seat=seat,
            status='confirmed'
        ).exists():
            messages.error(request, 'Seat no longer available.')
            return redirect('dashboard')
        
        # Check schedule in future
        if schedule.departure_time < timezone.now():
            messages.error(request, 'This trip has already departed.')
            return redirect('dashboard')
        
        # Create booking
        try:
            with transaction.atomic():
                # Calculate fare
                fare = schedule.route.calculate_fare(
                    boarding_stop.order,
                    alighting_stop.order
                )
                
                # Create
                booking = Booking.objects.create(
                    user=request.user,
                    schedule=schedule,
                    seat=seat,
                    boarding_stop=boarding_stop,
                    alighting_stop=alighting_stop,
                    fare=fare,
                    status=Booking.STATUS_PENDING,
                    booking_reference=f"BK{uuid.uuid4().hex[:10].upper()}"
                )
                
                messages.success(request, 'Booking created! Proceed to payment.')
                return redirect('payment-initiate', booking_uid=booking.uid)
        
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            messages.error(request, 'Error creating booking.')
            return redirect('dashboard')