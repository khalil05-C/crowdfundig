from django import forms

from .models import Reward


class RewardForm(forms.ModelForm):
    """Bootstrap-ready form used by project owners to create rewards."""

    class Meta:
        model = Reward
        fields = [
            "title",
            "description",
            "minimum_amount",
            "reward_type",
            "quantity_available",
            "image",
            "estimated_delivery",
            "ships_internationally",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control rounded-3"}),
            "description": forms.Textarea(attrs={"class": "form-control rounded-3", "rows": 3}),
            "minimum_amount": forms.NumberInput(attrs={"class": "form-control rounded-3", "min": 10}),
            "reward_type": forms.Select(attrs={"class": "form-select rounded-3"}),
            "quantity_available": forms.NumberInput(attrs={"class": "form-control rounded-3", "min": 1}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control rounded-3", "accept": "image/*"}),
            "estimated_delivery": forms.DateInput(attrs={"class": "form-control rounded-3", "type": "date"}),
            "ships_internationally": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
