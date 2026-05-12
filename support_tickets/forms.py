from django import forms

from .models import SupportMessage, SupportTicket


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["subject", "category", "description", "priority", "attachment"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control rounded-3", "placeholder": "Ex: Probleme de paiement"}),
            "category": forms.Select(attrs={"class": "form-select rounded-3"}),
            "description": forms.Textarea(attrs={"class": "form-control rounded-3", "rows": 5}),
            "priority": forms.Select(attrs={"class": "form-select rounded-3"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control rounded-3"}),
        }


class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ["content", "attachment"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "form-control rounded-3", "rows": 3, "placeholder": "Ecrire un message..."}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control rounded-3"}),
        }

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Le message ne peut pas etre vide.")
        return content
