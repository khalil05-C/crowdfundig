from decimal import Decimal

from django import forms

from rewards.models import Reward

from .models import Pledge


class PledgeForm(forms.ModelForm):
    """Validate pledge amount and selected reward eligibility."""

    class Meta:
        model = Pledge
        fields = ["amount", "reward", "message", "is_anonymous"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control form-control-lg rounded-start-3", "min": 10}),
            "reward": forms.RadioSelect,
            "message": forms.Textarea(attrs={"class": "form-control rounded-3", "rows": 3}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)
        self.fields["reward"].required = False
        self.fields["reward"].queryset = project.rewards.filter(is_active=True) if project else Reward.objects.none()

    def clean_amount(self):
        """Ensure the pledge amount is a positive contribution."""
        amount = self.cleaned_data["amount"]
        if amount < Decimal("10.00"):
            raise forms.ValidationError("Le montant minimum est 10 MAD.")
        return amount

    def clean(self):
        """Ensure selected rewards are unlocked by the contribution amount."""
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        reward = cleaned_data.get("reward")

        if reward and reward.project_id != self.project.id:
            raise forms.ValidationError("Cette recompense ne correspond pas a ce projet.")

        if amount and reward and not reward.is_eligible_for(amount):
            raise forms.ValidationError("Cette recompense n'est pas disponible pour ce montant.")

        return cleaned_data
