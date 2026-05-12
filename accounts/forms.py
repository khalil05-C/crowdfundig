from django import forms

from .models import User


class NotificationPreferenceForm(forms.ModelForm):
    """Form used to update user notification contact preferences."""

    class Meta:
        model = User
        fields = ["phone", "notification_preference"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control rounded-3"}),
            "notification_preference": forms.Select(attrs={"class": "form-select rounded-3"}),
        }
