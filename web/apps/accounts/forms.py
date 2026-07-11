from django import forms
from django.contrib.auth import authenticate

from apps.settings_app.models import Branch


class LoginForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "placeholder": "Email or Username"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Password"})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Select Branch",
    )
    remember_me = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get("identifier")
        password = cleaned.get("password")

        if not identifier or not password:
            return cleaned

        user = authenticate(identifier=identifier, password=password)
        if not user:
            raise forms.ValidationError("Invalid Username/Email Or Password.")
        if not user.is_active:
            raise forms.ValidationError("This Account Is Disabled.")

        cleaned["user"] = user
        return cleaned

    def resolve_branch_id(self):
        user = self.cleaned_data["user"]
        branch = self.cleaned_data.get("branch")
        if branch:
            return branch.id
        if user.default_branch_id:
            return user.default_branch_id
        return None