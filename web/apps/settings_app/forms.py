from django import forms
from .models import BusinessProfile


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            "business_name",
            "business_name_ar",
            "commercial_registration_number",
            "vat_no",
            "address",
            "address_ar",
            "phone_number",
            "phone_number_ar",
            "email",
            "email_ar",
            "website",
            "website_ar",
            "currency_code",
            "currency_symbol",
            "logo",
        ]