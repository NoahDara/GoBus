# buses/forms.py

from django import forms
from .models import Bus, Route, RouteStop, RouteSegment, Schedule

from datetime import timedelta

class BusForm(forms.ModelForm):
    """Form for creating/updating buses - only bus_number, plate_number, capacity"""
    
    class Meta:
        model = Bus
        fields = ('bus_number', 'plate_number', 'capacity')
        widgets = {
            'bus_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. BUS001',
                'style': 'font-family: monospace;'
            }),
            'plate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. ZW123ABC',
                'style': 'font-family: monospace;'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 50',
                'min': '1',
                'max': '100'
            }),
        }
        labels = {
            'bus_number': 'Bus Number',
            'plate_number': 'Plate Number',
            'capacity': 'Seat Capacity',
        }

    def clean_bus_number(self):
        bus_number = self.cleaned_data.get('bus_number')
        if bus_number:
            # Check if this bus_number already exists (excluding current instance)
            qs = Bus.objects.filter(bus_number=bus_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A bus with this number already exists.")
        return bus_number

    def clean_plate_number(self):
        plate_number = self.cleaned_data.get('plate_number')
        if plate_number:
            # Check if this plate_number already exists (excluding current instance)
            qs = Bus.objects.filter(plate_number=plate_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A bus with this plate number already exists.")
        return plate_number

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity and (capacity < 1 or capacity > 100):
            raise forms.ValidationError("Capacity must be between 1 and 100 seats.")
        return capacity


class BusReassignDriverForm(forms.ModelForm):
    """Form for reassigning driver with swap option"""
    
    SWAP_CHOICES = [
        (False, "Just assign to this bus"),
        (True, "Swap drivers between buses"),
    ]
    
    swap_driver = forms.ChoiceField(
        choices=SWAP_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label="Driver Assignment",
        initial=False,
        help_text="Choose how to handle the driver reassignment"
    )
    
    class Meta:
        model = Bus
        fields = ('driver',)
        widgets = {
            'driver': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'driver': 'Select New Driver',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active drivers
        from drivers.models import Driver
        self.fields['driver'].queryset = Driver.objects.filter(
            user__is_active=True
        ).select_related('user')
        self.fields['driver'].empty_label = "— No Driver —"
        
        
class RouteForm(forms.ModelForm):
    """Form for creating/updating routes"""
    
    # Custom field for duration input
    estimated_duration = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2:30 (2 hours 30 minutes)',
            'pattern': r'^[0-9]{1,2}:[0-9]{2}$',
        }),
        label='Estimated Duration',
        help_text='Format: HH:MM (e.g., 2:30 for 2 hours 30 minutes)',
    )
    
    class Meta:
        model = Route
        fields = ('name', 'origin', 'destination', 'estimated_duration')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Harare to Bulawayo',
            }),
            'origin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Harare',
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Bulawayo',
            }),
        }
        labels = {
            'name': 'Route Name',
            'origin': 'Origin City',
            'destination': 'Destination City',
        }
 
    def clean_estimated_duration(self):
        """Convert HH:MM string to timedelta"""
        duration_str = self.cleaned_data.get('estimated_duration')
        
        if not duration_str:
            return None
        
        try:
            # Parse HH:MM format
            parts = duration_str.strip().split(':')
            if len(parts) != 2:
                raise ValueError("Invalid format")
            
            hours = int(parts[0])
            minutes = int(parts[1])
            
            if hours < 0 or minutes < 0 or minutes >= 60:
                raise ValueError("Invalid time values")
            
            return timedelta(hours=hours, minutes=minutes)
        except (ValueError, IndexError):
            raise forms.ValidationError(
                "Duration must be in HH:MM format (e.g., 2:30 for 2 hours 30 minutes)"
            )
 
    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        if origin and destination and origin.lower() == destination.lower():
            raise forms.ValidationError("Origin and destination must be different.")
        
        return cleaned_data
 
 
class RouteStopForm(forms.ModelForm):
    """Form for creating/updating route stops"""
    
    class Meta:
        model = RouteStop
        fields = ('name', 'order')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Harare Central',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1, 2, 3...',
            }),
        }
        labels = {
            'name': 'Stop Name',
            'order': 'Stop Order',
        }
 
    def clean_order(self):
        order = self.cleaned_data.get('order')
        if order and order < 1:
            raise forms.ValidationError("Order must be at least 1.")
        return order
 
 
class RouteSegmentForm(forms.ModelForm):
    """Form for creating/updating route segments (pricing)"""
    
    class Meta:
        model = RouteSegment
        fields = ('from_stop', 'to_stop', 'price')
        widgets = {
            'from_stop': forms.Select(attrs={
                'class': 'form-select',
            }),
            'to_stop': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
        }
        labels = {
            'from_stop': 'From Stop',
            'to_stop': 'To Stop',
            'price': 'Price ($)',
        }
 
    def __init__(self, *args, route=None, **kwargs):
        super().__init__(*args, **kwargs)
        if route:
            # Only show stops for this route
            self.fields['from_stop'].queryset = RouteStop.objects.filter(route=route).order_by('order')
            self.fields['to_stop'].queryset = RouteStop.objects.filter(route=route).order_by('order')
        
        # Set empty label
        self.fields['from_stop'].empty_label = "— Select Stop —"
        self.fields['to_stop'].empty_label = "— Select Stop —"
 
    def clean(self):
        cleaned_data = super().clean()
        from_stop = cleaned_data.get('from_stop')
        to_stop = cleaned_data.get('to_stop')
        
        if from_stop and to_stop and from_stop == to_stop:
            raise forms.ValidationError("From and To stops must be different.")
        
        return cleaned_data
 