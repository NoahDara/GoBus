# buses/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from ..models import Bus
from ..forms import BusForm, BusReassignDriverForm
from drivers.models import Driver
from helpers.mixins import UIDObjectMixin


class BusListView(LoginRequiredMixin, ListView):
    """List all buses"""
    model = Bus
    template_name = 'buses/index.html'
    context_object_name = 'buses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Bus.objects.all().select_related('driver__user')
        
        # Filter by operational status if provided
        operational = self.request.GET.get('operational')
        if operational == 'true':
            queryset = queryset.filter(is_operational=True)
        elif operational == 'false':
            queryset = queryset.filter(is_operational=False)
        
        return queryset.order_by('bus_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_buses'] = Bus.objects.count()
        context['operational_buses'] = Bus.objects.filter(is_operational=True).count()
        context['maintenance_buses'] = Bus.objects.filter(is_operational=False).count()
        context['assigned_buses'] = Bus.objects.filter(driver__isnull=False).count()
        context['unassigned_buses'] = Bus.objects.filter(driver__isnull=True).count()
        return context


class BusCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new bus"""
    model = Bus
    form_class = BusForm
    template_name = 'buses/create.html'
    success_message = "Bus '%(bus_number)s' created successfully"

    def get_success_url(self):
        return reverse_lazy('buses-detail', kwargs={'uid': self.object.uid})


class BusDetailView(LoginRequiredMixin, UIDObjectMixin, DetailView):
    """Display bus details with inline edit mode"""
    model = Bus
    template_name = 'buses/detail.html'
    context_object_name = 'bus'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bus = self.object
        context['form'] = BusForm(instance=bus)
        context['driver_form'] = BusReassignDriverForm(instance=bus)
        context['schedules'] = bus.schedules.all().select_related('route').order_by('-departure_time')[:10]
        context['upcoming_schedules'] = bus.schedules.filter(
            status__in=['scheduled', 'in_progress']
        ).select_related('route').order_by('departure_time')[:5]
        return context


class BusUpdateView(LoginRequiredMixin, SuccessMessageMixin, UIDObjectMixin, UpdateView):
    """Update bus information (bus_number, plate_number, capacity)"""
    model = Bus
    form_class = BusForm
    template_name = 'buses/update.html'
    success_message = "Bus updated successfully"

    def get_success_url(self):
        return reverse_lazy('buses-detail', kwargs={'uid': self.object.uid})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'bus': {
                    'uid': str(self.object.uid),
                    'bus_number': self.object.bus_number,
                    'plate_number': self.object.plate_number,
                    'capacity': self.object.capacity,
                }
            })
        return response


class BusToggleOperationalView(LoginRequiredMixin, UIDObjectMixin, View):
    """Toggle bus operational status with modal confirmation"""
    model = Bus
    
    def post(self, request, uid):
        bus = get_object_or_404(Bus, uid=uid)
        action = request.POST.get('action')  # 'activate' or 'deactivate'
        
        if action == 'activate':
            bus.is_operational = True
            message = f"Bus '{bus.bus_number}' is now operational"
        elif action == 'deactivate':
            bus.is_operational = False
            message = f"Bus '{bus.bus_number}' is now in maintenance"
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        bus.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'is_operational': bus.is_operational,
            })
        
        return redirect('buses-detail', uid=bus.uid)


class BusReassignDriverView(LoginRequiredMixin, UIDObjectMixin, View):
    """Reassign driver to bus with swap logic"""
    model = Bus
    
    def post(self, request, uid):
        bus = get_object_or_404(Bus, uid=uid)
        form = BusReassignDriverForm(request.POST, instance=bus)
        
        if form.is_valid():
            new_driver = form.cleaned_data.get('driver')
            swap = form.cleaned_data.get('swap_driver') == 'True' or form.cleaned_data.get('swap_driver') is True
            old_driver = bus.driver
            
            if new_driver and swap and old_driver:
                # Swap drivers between buses
                other_bus = Bus.objects.filter(driver=new_driver).first()
                if other_bus:
                    # Swap
                    bus.driver = new_driver
                    other_bus.driver = old_driver
                    bus.save()
                    other_bus.save()
                    message = f"Drivers swapped: {new_driver.get_full_name()} → Bus {bus.bus_number}, {old_driver.get_full_name()} → Bus {other_bus.bus_number}"
                else:
                    # New driver not assigned anywhere, just assign
                    bus.driver = new_driver
                    bus.save()
                    message = f"Driver {new_driver.get_full_name()} assigned to Bus {bus.bus_number}"
            else:
                # Just assign (or remove)
                bus.driver = new_driver
                bus.save()
                if new_driver:
                    message = f"Driver {new_driver.get_full_name()} assigned to Bus {bus.bus_number}"
                else:
                    message = f"Driver removed from Bus {bus.bus_number}"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'driver': {
                        'uid': str(new_driver.uid) if new_driver else None,
                        'name': new_driver.get_full_name() if new_driver else 'No Driver',
                    } if new_driver else None,
                })
            
            return redirect('buses-detail', uid=bus.uid)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        context = {'bus': bus, 'form': form}
        return render(request, 'buses/detail.html', context)