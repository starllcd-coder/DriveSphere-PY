from django import forms
from django.db.models import Q

from .models import Customer, CustomerDocument


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "id_type",
            "id_number",
            "phone_number",
            "email",
            "address",
            "license_number",
            "license_issuer",
            "license_issue_date",
            "license_expiry_date",
            "notes",
            "is_active",
        ]


class CustomerDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomerDocument
        fields = ["doc_type", "file", "expiry_date", "notes"]


class CustomerFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(attrs={"placeholder": "Name / Phone / ID"}))

    def filter_queryset(self, qs):
        q = self.cleaned_data.get("q")
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(phone_number__icontains=q)
                | Q(id_number__icontains=q)
            )
        return qs