# buses/forms.py

from django import forms
from .models import Bus


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