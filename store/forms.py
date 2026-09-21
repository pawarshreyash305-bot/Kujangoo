from django import forms
from django.contrib.auth import get_user_model
from .models import Review
User = get_user_model()


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number'
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']

        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                "An account with this mobile number already exists."
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = user.email.lower()
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ['rating', 'comment']

        widgets = {
            'rating': forms.NumberInput(
                attrs={
                    'min': 1,
                    'max': 5
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'placeholder': 'Write your review...'
                }
            ),
        }

class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'profile_image',
        ]