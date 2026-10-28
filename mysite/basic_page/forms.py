import re

from django import forms

from .models import UserBidModel


PHONE_PATTERN = re.compile(
    r"^(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$"
)


class UserBidForm(forms.ModelForm):
    """Server-side validation for public lead forms."""

    privacyPolicy = forms.BooleanField(required=True)

    class Meta:
        model = UserBidModel
        fields = ("full_name", "phone", "email")

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"].strip()
        if len(full_name) < 3:
            raise forms.ValidationError("Введите полное имя.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not PHONE_PATTERN.fullmatch(phone):
            raise forms.ValidationError("Введите номер в российском формате.")
        return phone

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.AWtPP = self.cleaned_data["privacyPolicy"]
        if commit:
            instance.save()
        return instance
