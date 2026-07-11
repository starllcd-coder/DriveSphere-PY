from django import forms
from .models import Vehicle, VehicleDocument, VehiclePhoto, VehicleBrand, VehicleModel


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "branch",
            "plate_number",
            "vin",
            "brand",
            "model",
            "year",
            "category",
            "transmission",
            "fuel",
            "color",
            "seats",
            "odometer_km",
            "service_interval_km",
            "status",
            "daily_rate",
            "deposit",
            "tags",
            "notes",
            "registration_expiry",
            "insurance_expiry",
        ]
        widgets = {
            "plate_number": forms.TextInput(attrs={"class": "ds-input", "placeholder": "Plate Number"}),
            "vin": forms.TextInput(attrs={"class": "ds-input", "placeholder": "VIN"}),
            "brand": forms.Select(attrs={"class": "ds-input", "id": "vf-brand"}),
            "model": forms.Select(attrs={"class": "ds-input", "id": "vf-model"}),
            "year": forms.NumberInput(attrs={"class": "ds-input"}),
            "category": forms.Select(attrs={"class": "ds-input"}),
            "fuel": forms.Select(attrs={"class": "ds-input"}),
            "transmission": forms.Select(attrs={"class": "ds-input"}),
            "color": forms.TextInput(attrs={"class": "ds-input", "placeholder": "Color"}),
            "seats": forms.NumberInput(attrs={"class": "ds-input"}),
            "odometer_km": forms.NumberInput(attrs={"class": "ds-input"}),
            "service_interval_km": forms.NumberInput(attrs={"class": "ds-input"}),
            "status": forms.Select(attrs={"class": "ds-input"}),
            "daily_rate": forms.NumberInput(attrs={"class": "ds-input"}),
            "deposit": forms.NumberInput(attrs={"class": "ds-input"}),
            "tags": forms.TextInput(attrs={"class": "ds-input", "placeholder": "Comma separated"}),
            "notes": forms.Textarea(attrs={"class": "ds-input", "rows": 3, "placeholder": "Notes"}),
            "registration_expiry": forms.DateInput(attrs={"class": "ds-input", "type": "date"}),
            "insurance_expiry": forms.DateInput(attrs={"class": "ds-input", "type": "date"}),
        }


class VehicleDocumentForm(forms.ModelForm):
    class Meta:
        model = VehicleDocument
        fields = ["doc_type", "file", "expiry_date", "notes"]
        widgets = {
            "doc_type": forms.Select(attrs={"class": "ds-input"}),
            "expiry_date": forms.DateInput(attrs={"class": "ds-input", "type": "date"}),
            "notes": forms.TextInput(attrs={"class": "ds-input", "placeholder": "Notes"}),
            "file": forms.ClearableFileInput(attrs={"class": "ds-input"}),
        }


class VehiclePhotoForm(forms.ModelForm):
    class Meta:
        model = VehiclePhoto
        fields = ["image", "caption"]
        widgets = {
            "caption": forms.TextInput(attrs={"class": "ds-input", "placeholder": "Caption"}),
            "image": forms.ClearableFileInput(attrs={"class": "ds-input", "accept": "image/*"}),
        }


class VehicleFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(attrs={"placeholder": "Plate / VIN / Brand / Model"}))
    status = forms.ChoiceField(required=False, choices=[("", "All Status")] + list(Vehicle.STATUS_CHOICES))
    fuel = forms.ChoiceField(required=False, choices=[("", "All Fuel")] + list(Vehicle.FUEL_CHOICES))
    transmission = forms.ChoiceField(required=False, choices=[("", "All Transmission")] + list(Vehicle.TRANSMISSION_CHOICES))
    year = forms.IntegerField(required=False)
    brand = forms.ModelChoiceField(required=False, queryset=VehicleBrand.objects.all(), empty_label="All Brands")
    model = forms.ModelChoiceField(required=False, queryset=VehicleModel.objects.select_related("brand").all(), empty_label="All Models")